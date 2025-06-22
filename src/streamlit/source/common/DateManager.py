from datetime import date
from datetime import timedelta

# --DateManager---
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