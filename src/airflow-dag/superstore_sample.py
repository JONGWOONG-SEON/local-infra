from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine, select, Float, UniqueConstraint
from sqlalchemy.sql import quoted_name
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import declarative_base, sessionmaker
from airflow.sensors.base import BaseSensorOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.exceptions import AirflowSkipException
from airflow.sensors.external_task import ExternalTaskSensor
import datetime
import boto3
import csv
import polars as pl
from io import StringIO,BytesIO
import os
from dotenv import load_dotenv
from airflow import DAG
from src.s3 import S3Config,S3MetaStore

load_dotenv()

BUCKET_NAME = "result"
BUCKET_PREFIX = "superstore/"
TARGET_TABLE = "superstore"
DATASOURCE_PATH = os.getenv("DATASOURCE_PATH")

config = S3Config.get_env()
client = S3MetaStore(config = config)
s3 = client()

engine = create_engine(DATASOURCE_PATH, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
Base = declarative_base()
paginator = s3.get_paginator("list_objects_v2")

def result_xcom_pull(**kwargs):

    data = kwargs["dag_run"].conf.get("input_result")
    if not data:
        raise AirflowSkipException("DAG A에서 데이터를 가져올 수 없어 중단")
    
    return data


def make_table(table_name: str, schema: str = "estore"):
    attrs = {
        "__tablename__": table_name,
        "__table_args__": (
            {
            "schema": schema,
            "extend_existing": True
            }
        ),
        "id"               : Column(Integer,primary_key=True,autoincrement=True),
        "table"            : Column(String(200)),
        "version"          : Column(String(200)),
        "describe"         : Column(String(200)),
        "timestamp"        : Column(String(200)),
        "category"         : Column(String(200)),
        "city"             : Column(String(200)),
        "container"        : Column(String(200)),
        "customerid"       : Column(String(200)),
        "customername"     : Column(String(200)),
        "customersegment"  : Column(String(200)),
        "department"       : Column(String(200)),
        "itemid"           : Column(String(200)),
        "item"             : Column(String(200)),
        "orderdate"        : Column(String(200)),
        "orderid"          : Column(String(200)),
        "orderpriority"    : Column(String(200)),
        "postalcode"       : Column(String(200)),
        "region"           : Column(String(200)),
        "rowid"            : Column(String(200)),
        "shipdate"         : Column(String(200)),
        "shipmode"         : Column(String(200)),
        "state"            : Column(String(200)),
        "discount"         : Column(Float),
        "orderquantity"    : Column(Float),
        "productbasemargin": Column(Float),
        "profit"           : Column(Float),
        "sales"            : Column(Float),
        "shippingcost"     : Column(Float),
        "unitprice"        : Column(Float)
    }
    return type(f"Note_{table_name}", (Base,), attrs)


def list_csv_keys(bucket:str,prefix:str,**kwargs) -> list[dict]:
    ti = kwargs['ti']
    input_result = ti.xcom_pull(task_ids='xcom_pull')

    rows: list[list[str]] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key not in input_result:
                continue

            print(f"keys:{key} \n insert_result:{input_result}")
            basename = key.rsplit("/", 1)[-1]      
            name, _ext = basename.rsplit(".", 1)   
            parts = name.split("_")                
            
            if len(parts) != 4:
                continue

            table     = parts[0] if len(parts) > 0 else ""
            version   = parts[1] if len(parts) > 1 else ""
            describe  = parts[2] if len(parts) > 2 else ""
            timestamp = parts[3] if len(parts) > 3 else ""

            rows.append([key, table, version, describe, timestamp])
    return rows

def read_csv_from_s3(bucket:str, key:list) -> pl.DataFrame:
    table = key[1]
    version = key[2]
    describe = key[3]
    timestamp = key[4]

    obj = s3.get_object(Bucket=bucket, Key=key[0])
    data = obj["Body"].read().decode("utf-8",errors="ignore")

    df = pl.read_csv(
        StringIO(data),
        infer_schema_length=None,
        low_memory=False
    )

    df = df.rename({
        "Category"           : "category",
        "City"               : "city",
        "Container"          : "container",
        "Customer ID"        : "customerid",
        "Customer Name"      : "customername",
        "Customer Segment"   : "customersegment",
        "Department"         : "department",
        "Item ID"            : "itemid",
        "Item"               : "item",
        "Order Date"         : "orderdate",
        "Order ID"           : "orderid",
        "Order Priority"     : "orderpriority",
        "Postal Code"        : "postalcode",
        "Region"             : "region",
        "Row ID"             : "rowid",
        "Ship Date"          : "shipdate",
        "Ship Mode"          : "shipmode",
        "State"              : "state",
        "Discount"           : "discount",
        "Order Quantity"     : "orderquantity",
        "Product Base Margin": "productbasemargin",
        "Profit"             : "profit",
        "Sales"              : "sales",
        "Shipping Cost"      : "shippingcost",
        "Unit Price"         : "unitprice",

    })

    df = df.with_columns([
        pl.lit(table).alias("table"),
        pl.lit(version).alias("version"),
        pl.lit(describe).alias("describe"),
        pl.lit(timestamp).alias("timestamp")
    ])

    print(df.head())

    df = df.with_columns([
        pl.col("discount").cast(pl.Float64),
        pl.col("orderquantity").cast(pl.Float64),
        pl.col("productbasemargin").cast(pl.Float64),
        pl.col("profit").cast(pl.Float64),
        pl.col("sales").cast(pl.Float64),
        pl.col("shippingcost").cast(pl.Float64),
        pl.col("unitprice").cast(pl.Float64)
    ])

    return df

def copy_to_pg_polars(df: pl.DataFrame, table_name: str, schema: str):
    buf = StringIO()
    df.write_csv(buf, include_header=False)
    buf.seek(0)

    conn = engine.raw_connection()
    cur = conn.cursor()
    cols_quoted = ','.join(map('"{}"'.format, df.columns))
    cur.copy_expert(
        f"COPY {schema}.{table_name} ({cols_quoted}) FROM STDIN WITH CSV",
        buf
    )
    conn.commit()
    cur.close()

def insert_notes_from_prefix(bucket: str, prefix: str, **kwargs):
    keys = list_csv_keys(bucket, prefix, **kwargs)
    print(keys)
    all_rows = []

    for key in keys:
        Note = make_table(TARGET_TABLE)
        Base.metadata.create_all(engine,checkfirst=True)
        rows = read_csv_from_s3(bucket, key)
        all_rows.append(rows)

    if all_rows:
        result = pl.concat(all_rows)
    else:
        return 
    
    copy_to_pg_polars(result, TARGET_TABLE, "estore")

def run(**kwargs):
    insert_notes_from_prefix(BUCKET_NAME, BUCKET_PREFIX, **kwargs)

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
}

with DAG(
    dag_id = "superstore_sample",
    start_date = days_ago(1),
    catchup=False,
    schedule_interval=None,
    max_active_runs=1,
    concurrency=5,
    tags = ["superstore"]
) as dag:
    
    xcom_pull = PythonOperator(
        task_id = 'xcom_pull',
        python_callable=result_xcom_pull,
        provide_context=True
    )

    superstore_insert = PythonOperator(
        task_id='superstore_task_id',
        python_callable=run,
        provide_context=True
    )

xcom_pull >> superstore_insert