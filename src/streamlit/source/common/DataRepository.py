from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import polars as pl
import streamlit as st
import os

# --- Data Repository ---
class DataRepository:
    _instance = None

    def __new__(cls, dev : bool = False):
        if dev == True:
            from dotenv import load_dotenv
            load_dotenv()
        else:
            pass
        if cls._instance is None:
            engine = create_engine(os.getenv("DATASOURCE_PATH"))
            cls._instance = super().__new__(cls)
            cls._instance._session = sessionmaker(bind=engine)()
        return cls._instance

    # @st.cache_data
    def load_data(_self, _sql) -> pl.DataFrame:
        query = text(_sql)
        df = pl.read_database(query, connection=_self._session.connection())
        df = df.with_columns(
            pl.col("orderdate").str.strptime(
                pl.Date,
                # format="%Y/%m/%d",  # single or double digit month/day
                strict=False
            ).alias("orderdate")
        )
        return df