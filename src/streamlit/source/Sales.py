
import streamlit as st

from source.common.DataRepository import DataRepository
from source.common.DateManager import DateManager
from source.common.FilterManager import FilterManager
from source.common.MeasureManager import MeasureManager
from source.common.UiManager import UIComponents

with st.expander("Packages"):
    """
    # --- Data Repository ---
    class DataRepository:
        _instance = None

        def __new__(cls):
            if cls._instance is None:
                load_dotenv()
                engine = create_engine(os.getenv("DATASOURCE_PATH"))
                cls._instance = super().__new__(cls)
                cls._instance._session = sessionmaker(bind=engine)()
            return cls._instance

        @st.cache_data
        def load_data(_self) -> pl.DataFrame:
            query = text("SELECT * FROM estore.superstore")
            df = pl.read_database(query, connection=_self._session.connection())
            df = df.with_columns(
                pl.col("orderdate").str.strptime(
                    pl.Date,
                    # format="%Y/%m/%d",  # single or double digit month/day
                    strict=False
                ).alias("orderdate")
            )
            return df
    """

    """
    # --- DateManager ---
    class DateManager:
        @staticmethod
        def set_date_type(_date_type : str):
            if _date_type == 'day':
                return timedelta(days=0)
            elif _date_type == 'week':
                return timedelta(days=7)
            elif _date_type == 'month':
                return timedelta(days=30)
            elif _date_type == 'year':
                return timedelta(days=365)
            else:
                raise ("Choose : day, week, month, year")
            
        @staticmethod
        def set_compare_date_type(date : date, _date_type : str):
            if _date_type == 'day':
                return date - timedelta(days=1)
            elif _date_type == 'week':
                return date - timedelta(days=7)
            elif _date_type == 'month':
                return date - timedelta(days=30)
            elif _date_type == 'year':
                return date - timedelta(days=365)
            else:
                raise ("Choose : day, week, month, year")
        
        @staticmethod
        def set_line_date_type(date : date, _date_type : str):
            if _date_type == 'day':
                to_date = date
                from_date = date - timedelta(days = 7)
                return from_date, to_date
            elif _date_type == 'week':
                to_date = date
                from_date = date - timedelta(weeks = 7)
                return from_date, to_date
            elif _date_type == 'month':
                to_date = date
                from_date = date - relativedelta(months = 3)
                return from_date, to_date
            else:
                raise ("Choose : day, week, month")
    """

    """
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
    """

    """
    # --- Measure Calculation ---
    class MeasureManager:
        def __init__(self, measure_keys: list[str]):
            self._keys = measure_keys
            
        def calculate(self, df: pl.DataFrame) -> dict[str, int]:
            sums = df[self._keys].sum()
            return {k: sums[k].to_list()[0] for k in self._keys}

        def compare_calculate(self, df: pl.DataFrame, compare_df : pl.DataFrame) -> int:
            _result = (df[self._keys].sum() / compare_df[self._keys].sum())
            return [_result[k].to_list()[0] for k in self._keys]

        def line_calculate(self, df: pl.DataFrame, _date_type:str) -> pl.DataFrame:
            if _date_type == 'day':
                line = df.with_columns(pl.col("orderdate").dt.strftime("%Y-%m-%d")).sort("orderdate")
                agg_df = line.group_by("orderdate").agg(pl.col("sales").sum().alias("sales_sum"))
                return agg_df
            elif _date_type == 'week':
                line = df.with_columns(pl.col("orderdate").dt.strftime("%Y-%W")).sort("orderdate")
                agg_df = line.group_by("orderdate").agg(pl.col("sales").sum().alias("sales_sum"))
                return agg_df

    """
    """
    # --- UI Components ---
    class UIComponents:

        @staticmethod
        def format_value(val: int) -> str:
            if val >= 1_000_000:
                return f"{round(val/1_000_000,2)}M"
            if val >= 1_000:
                return f"{round(val/1_000,2)}K"
            return str(val)
        
        @staticmethod
        def format_compare(val: int) -> str:
            return f"{round((val * 100),2)}%"

        @staticmethod
        def render_metrics(metrics: dict[str, int], compare: str, type: str):
            cols = st.columns(len(metrics)+1)
            with cols[0]:
                with st.container(border=True,height=130):
                    st.metric(label=type ,value=type ,label_visibility="hidden")
            for idx, (title, val) in enumerate(metrics.items()):
                with cols[idx+1]:
                    with st.container(border=True,height=130):
                        formatted = UIComponents.format_value(val)
                        formatted_compare = UIComponents.format_compare(compare[idx])
                        st.metric(title.capitalize(), formatted, delta = formatted_compare)
    """

# --- Main Application ---
class SuperStoreApp:
    def __init__(self):
        # 필터 키: DB 컬럼 이름과 일치시킬 것
        self.date_keys = {"asofdate" : "orderdate"}
        self.filter_keys = ["orderdate", "version", "region"]
        self.measure_keys = ["sales", "shippingcost", "orderquantity", "unitprice"]

        # 데이터 로드
        repo = DataRepository()
        sql = "SELECT * FROM estore.superstore"
        self.df = repo.load_data(sql)

        # 매니저 초기화
        self.filter_manager = FilterManager(self.df, self.date_keys, self.filter_keys)
        self.measure_manager = MeasureManager(self.measure_keys)

    def run(self):
        st.sidebar.title("Filters")
        # 필터 초기화 및 선택값 가져오기
        self.filter_manager.init_session()
        selections = self.filter_manager.get_sidebar_selection()

        # 필터 적용 -> Dataframe 반환
        day_df = self.filter_manager.current_apply_filters(selections,'day')
        day_compare_df = self.filter_manager.previous_apply_filters(selections,'day')
        day_line_df = self.filter_manager.line_apply_filters(selections, 'day')

        week_df = self.filter_manager.current_apply_filters(selections,'week')
        week_compare_df = self.filter_manager.previous_apply_filters(selections,'week')
        week_line_df = self.filter_manager.line_apply_filters(selections, 'week')

        # 측정값 계산
        day_metric = self.measure_manager.calculate(day_df)
        dod = self.measure_manager.compare_calculate(day_df,day_compare_df)
        day_agg = self.measure_manager.line_calculate(day_line_df,'day')

        week_metric = self.measure_manager.calculate(week_df)
        wow = self.measure_manager.compare_calculate(week_df,week_compare_df)
        week_agg = self.measure_manager.line_calculate(week_df,'week')


        # 화면 렌더링
        st.title("SuperStore Overview")
        UIComponents.render_metrics(day_metric,dod,'Daily')
        UIComponents.render_metrics(week_metric,wow,'WTD')

        print(day_line_df)
        tabs_col = st.columns(2)
        
        st.write("View By")
        tab1, tab2 = st.tabs(["Daily", "Weekly"])
        with tab1:
            col1, col2, col3 = st.columns(3)

            with col1:
                with st.container(border = True, height= 360):
                    st.line_chart(day_agg,x='orderdate',y='sales_sum')
            with col2:
                with st.container(border = True, height= 360):
                    st.line_chart(day_agg,x='orderdate',y='sales_sum')
            with col3:
                with st.container(border = True, height= 360):
                    st.line_chart(day_agg,x='orderdate',y='sales_sum')

        with tab2:
            col1, col2, col3 = st.columns(3)

            with col1:
                with st.container(border = True, height= 360):
                    st.line_chart(week_agg,x='orderdate',y='sales_sum')
            with col2:
                with st.container(border = True, height= 360):
                    st.line_chart(week_agg,x='orderdate',y='sales_sum')
            with col3:
                with st.container(border = True, height= 360):
                    st.line_chart(week_agg,x='orderdate',y='sales_sum')

        st.dataframe(day_df, width = 1600, hide_index = True)

app = SuperStoreApp()
app.run()