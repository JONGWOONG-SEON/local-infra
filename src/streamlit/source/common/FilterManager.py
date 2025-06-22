import streamlit as st
import polars as pl
from source.common.DateManager import DateManager
from datetime import date

# --- Filter Management ---
class FilterManager:
    def __init__(self, df: pl.DataFrame, date_key: dict ,filter_keys: list[str]):
        self._df = df
        self._keys = filter_keys
        self._date_keys = date_key

    def init_session(self):
        for key in self._keys:
            session_key = f"filter_{key}"
            if session_key not in st.session_state:
                st.session_state[session_key] = self._df.select(key).unique().to_series().to_list()

    def get_sidebar_selection(self):
        selections = {}
        default_range = (date(2014, 12, 10))
        sel_dates = st.sidebar.date_input("As of Date", default_range, key="to_date")
        selections["orderdate"] = sel_dates

        for key in [k for k in self._keys if k != "orderdate"]:
            sel = st.sidebar.multiselect(
                key.capitalize(), st.session_state[f"filter_{key}"], key=key)
            selections[key] = sel
        return selections

    def current_apply_filters(self, selections: dict, _date_type: str) -> pl.DataFrame:
        date_type = DateManager.set_date_type(_date_type)
        df = self._df

        to_date = selections.get("orderdate", (None, None))
        from_date = to_date - date_type

        if to_date:
            df = df.filter((df["orderdate"] >= from_date) 
                         & (df["orderdate"] <= to_date))
        for key, vals in selections.items():
            if key == "orderdate" or not vals:
                continue
            df = df.filter(df[key].is_in(vals))
        return df

    def previous_apply_filters(self, selections: dict, _date_type : str) -> pl.DataFrame:
        date_type = DateManager.set_date_type(_date_type)
        compare_df = self._df

        to_date = selections.get("orderdate", (None, None))
        from_date = to_date - date_type
        compare_to_date = DateManager.set_compare_date_type(to_date,_date_type)
        compare_from_date = DateManager.set_compare_date_type(from_date,_date_type)

        if compare_to_date:
            compare_df = compare_df.filter((compare_df["orderdate"] >= compare_from_date) 
                                         & (compare_df["orderdate"] <= compare_to_date))
        for key, vals in selections.items():
            if key == "orderdate" or not vals:
                continue
            compare_df = compare_df.filter(compare_df[key].is_in(vals))
        return compare_df
    
    def line_apply_filters(self, selections: dict, _date_type : str) -> pl.DataFrame:
        default_date = selections.get("orderdate", (None,None))
        from_date, to_date = DateManager.set_line_date_type(default_date,_date_type)
        line_df = self._df

        if to_date:
            line_df = line_df.filter((line_df["orderdate"] >= from_date)
                                     &(line_df["orderdate"] <= to_date))
        for key, vals in selections.items():
            if key == "orderdate" or not vals:
                continue
            line_df = line_df.filter(line_df[key].is_in(vals))
        return line_df