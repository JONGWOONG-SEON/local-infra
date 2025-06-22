from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
# from dotenv import load_dotenv
import pandas as pd 
import streamlit as st
import threading
from datetime import date
from datetime import datetime

# load_dotenv()
DATASOURCE_PATH = os.getenv("DATASOURCE_PATH")

engine = create_engine(DATASOURCE_PATH)
Session = sessionmaker(bind=engine)
session = Session()

sql = text("SELECT * FROM estore.superstore")
result = session.execute(sql)

gloabl_df = pd.read_sql(sql, session.bind)

session.close()

gloabl_df['orderdate_parsed'] = pd.to_datetime(gloabl_df['orderdate'], format='%m/%d/%Y')
gloabl_df['orderdate'] = gloabl_df['orderdate_parsed'].dt.strftime('%Y%m%d').astype(int)


def format_with_commas(number):
    return f"{number:,}"

def get_sales_max(df,col1,col2,aov : None):
    revenue = sum(df[col1])
    order = sum(df[col2])
    if aov == None:
        if revenue > 1000000:
            revenue = int(revenue/1000000)
            unit = 'M'
            return revenue, order, unit
        elif revenue >= 1000 and revenue < 1000000:
            revenue = int(revenue/1000)
            unit = 'K'
            return revenue, order, unit
        elif revenue < 1000:
            unit = ''
            return revenue, order, unit
    elif aov == True:
        if  revenue > 1000000:
            aov = revenue/order
            revenue = int(revenue / 1000000)
            unit = 'M'
            return revenue, order, unit ,aov
        elif revenue >= 1000 and revenue < 1000000:
            aov = revenue/order
            revenue = int(revenue / 1000)
            unit = 'K'
            return revenue, order, unit, aov
        elif revenue < 1000:
            aov = revenue/order
            unit = ''
            return revenue, order, unit, aov


def display_barchart(data,x,y):

    if x == 'aov':
        chart_data = data[["sales","unitprice","orderdate"]]
        chart_data = chart_data.groupby("orderdate")[["sales","unitprice"]].sum()
        chart_data = chart_data["sales"]/chart_data["unitprice"]
        st.bar_chart(chart_data, height=200, x_label=None, y_label=None)
    elif x != 'aov':
        chart_data = data[[x,y]]
        chart_data = chart_data.groupby(y)[x].sum()
        st.bar_chart(chart_data,height=200,x_label=None,y_label=None)

def display_metric(col, title, value, data ,bar_value):
    with col:
        with st.container(border = True, height= 350):
            st.metric(title, value)
            display_barchart(data,bar_value,"orderdate")

def upload_handling(version,from_date,to_date, data):

    df = data
    metircs = [
        ("Overview_v1", "Net Revenue"),
        ("Overview_v2", "Net Revenue")
    ]
    
    from_date = int(from_date.strftime('%Y%m%d'))
    to_date = int(to_date.strftime('%Y%m%d'))

    df = df[(df['orderdate']>= from_date)
            &(df['orderdate'] <= to_date)
            &(df['version'] == version)].copy()

    cols = st.columns(3)

    revenue, order, unit, aov = get_sales_max(df, "sales", "unitprice",aov=True)
    st.dataframe(df , width= 1600, hide_index = True)
    display_metric(cols[0],"Revenue", f" {revenue}{unit}", df,"sales")
    display_metric(cols[1],"Order Count", f" {order}", df,"unitprice")
    display_metric(cols[2],"aov", f" {int(aov)}", df, "aov")

def get_dimension_filter(data):
    df = gloabl_df
    for i in df.select_dtypes(include='object').columns:
        filter_value = []
        filter_value = list(df[i].drop_duplicates())
        i = st.multiselect(
            f"{i}",
            filter_value,
            filter_value
        )
    return get_dimension_filter(i)

with st.sidebar:
    st.header("⚙️ Settings")
    total = st.date_input("Between Date",(date(2014, 12, 21),date(2014, 12, 31)) )
    if int(len(total)) == 2:
        from_date , to_date = total
        sales_filter = True
    else:
        st.error("Choose Date")
        sales_filter = False
    version = st.selectbox("Version"
                           , gloabl_df['version'].drop_duplicates()
                           , placeholder="Select Version")
    if version != None:
        apply_version = version
        sales_filter = True
    else:
        st.error("Choose Version")
        sales_filter = False

condition = threading.Condition()

with condition:
    if sales_filter == False:
        condition.wait()
    elif sales_filter == True:
        upload_handling(apply_version,from_date, to_date, gloabl_df)
