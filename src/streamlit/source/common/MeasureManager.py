import polars as pl

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
