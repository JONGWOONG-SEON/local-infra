from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine, select, Float, UniqueConstraint
from sqlalchemy.sql import quoted_name
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import declarative_base, sessionmaker
from dataclasses import dataclass
import polars as pl
from io import StringIO,BytesIO
from abc import ABC, abstractmethod
from typing import Set, Optional, Type
from src.airflow import read_csv_from_s3
from src.airflow import list_csv_keys
import os

DATASOURCE_PATH = os.getenv("DATASOURCE_PATH")

engine = create_engine(DATASOURCE_PATH, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
Base = declarative_base()

@dataclass(frozen=True)
class PgConfig:
    property: dict
    table : str
    schema: str
    datasource_path: str
    
    @staticmethod
    def get_config(ddl, table, shema) -> "PgConfig":
        return PgConfig(
            property=ddl,
            table=table,
            schema=shema,
            datasource_path=os.environ["DATASOURCE_PATH"]
        )

def ImplementDBConfig(cls: Type) -> Type:
    origin_init = cls.__init__

    def __init__(self, config: PgConfig, *args, **kwargs):
        self._property = config.property
        self._table = config.table
        self._schema = config.schema
        self._datasource_path = config.datasource_path
        self._engine = create_engine(config.datasource_path, future=True)
        self._Base = declarative_base()

    cls.__init__ = __init__
    return cls

@ImplementDBConfig
class DButils:

    def set_table(self):
        """
        테이블 셋업 책임 함수
        """
        attrs = {
            "__tablename__": self._table,
            "__table_args__": (
            {"schema": self._schema}
            ),
        }
        attrs.update(self._property)

        return type(f"Note_{self._table}", (self._Base,), attrs)
    
    def make_table(self):
        """
        테이블 생성 책임 함수
        """
        SessionLocal = sessionmaker(bind=self._engine, autoflush=False, future=True)

        Note = self.set_table()
        self._Base.metadata.create_all(self._engine,checkfirst=True)
        
        print(f"테이블 생성: {self._table}")

        return Note
    
    def insert_notes_from_prefix(self, bucket: str, prefix: str ,keys, s3, **kwargs):
        """
        메인 함수
        """

        print(keys)
        all_rows = []

        for key in keys:
            rows = read_csv_from_s3(bucket, key, s3)
            all_rows.append(rows)
        
        print(all_rows)

        if all_rows:
            result = pl.concat(all_rows)
        else:
            return 
        return result

    def copy_to_pg_polars(self,df: pl.DataFrame):
        """
        적재 책임 함수
        """
        buf = StringIO()
        df.write_csv(buf, include_header=False)
        buf.seek(0)

        conn = self._engine.raw_connection()
        cur = conn.cursor()
        cols_quoted = ','.join(map('"{}"'.format, df.columns))
        cur.copy_expert(
            f"COPY {self._schema}.{self._table} ({cols_quoted}) FROM STDIN WITH CSV",
            buf
        )
        conn.commit()
        cur.close()
