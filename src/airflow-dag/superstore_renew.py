from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine, select, Float, UniqueConstraint
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
from src.postgres import PgConfig,DButils
from src.airflow import result_xcom_pull,read_csv_from_s3,list_csv_keys
from src.utils import key_parser

BUCKET_NAME = "result"
BUCKET_PREFIX = "superstore/"
TARGET_TABLE = "superstore"
DATASOURCE_PATH = os.getenv("DATASOURCE_PATH")


superstore_property ={
        "id"               : Column(Integer,primary_key=True,autoincrement=True),
        "table"            : Column(String(200)),
        "version"          : Column(String(200)),
        "description"      : Column(String(200)),
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


def superstore_tranform(df, table, version, description, timestamp):
    # df = pl.read_csv(
    #     StringIO(data),
    #     infer_schema_length=None,
    #     low_memory=False
    # )

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
        pl.lit(description).alias("description"),
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

def run(**kwargs):
    config = S3Config.get_env()
    client = S3MetaStore(config = config)
    s3 = client()
    paginator = s3.get_paginator("list_objects_v2")

    dbconfig = PgConfig.get_config(superstore_property,TARGET_TABLE,"estore")
    dbutils = DButils(dbconfig)
    dbutils.make_table()

    list_keys = list_csv_keys(BUCKET_NAME,BUCKET_PREFIX,paginator,'xcom_pull_new',**kwargs)
    df = dbutils.insert_notes_from_prefix(BUCKET_NAME ,BUCKET_PREFIX ,list_keys ,s3)
    
    print(f"확인용 {list_keys}")

    table, version, description, timestamp = key_parser(list_keys)
    result = superstore_tranform(df, table, version, description, timestamp)
    dbutils.copy_to_pg_polars(result)

with DAG(
    dag_id = "superstore_test_sample",
    start_date = days_ago(1),
    catchup=False,
    schedule_interval=None,
    max_active_runs=1,
    concurrency=5,
    tags = ["superstore"]
) as dag:   
    
    xcom_pull_new = PythonOperator(
        task_id = 'xcom_pull_new',
        python_callable=result_xcom_pull,
        provide_context=True
    )

    superstore_insert_new = PythonOperator(
        task_id='superstore_task_id_new',
        python_callable=run,
        provide_context=True
    )

xcom_pull_new >> superstore_insert_new