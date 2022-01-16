# -*- coding: utf-8 -*-
"""
@time: 2021/10/19 17:04
@file: dt_convert.py

时间解析及转换：
* 8位(年月日)、14位(保留到秒)、17位(保留到毫秒)，9位(时分秒毫秒)
* 根据整数位数不同，可以还原所需datetime相关对象

"""
from typing import List, Tuple
import pandas as pd

import datetime
from dateutil.parser import parse as parse_datetime
import numpy as np
from six import string_types, integer_types


# 集成方法-----------------------------------------------------------------------------------------
def to_datetime(dt) -> datetime.datetime:
    """各种格式转datetime: 不确定对象类型时使用。"""
    if isinstance(dt, datetime.datetime):
        return dt
    elif isinstance(dt, datetime.date):
        return datetime.datetime(dt.year, dt.month, dt.day)
    elif isinstance(dt, string_types):
        return parse_datetime(dt, ignoretz=True)
    elif isinstance(dt, integer_types):
        return int_to_datetime(dt)
    elif hasattr(dt, "to_pydatetime"):
        return dt.to_pydatetime()
    elif hasattr(dt, "dtype") and dt.dtype.char == "M":
        return parse_datetime(str(dt))
    raise ValueError("expect a datetime like object, got %r(%r)" % (type(dt), dt))


def to_date(dt) -> datetime.date:
    """各种格式转date: 不确定对象类型时使用。"""
    if isinstance(dt, datetime.datetime):
        return dt.date()
    elif isinstance(dt, datetime.date):
        return dt
    elif isinstance(dt, string_types):
        return parse_datetime(dt).date()
    elif isinstance(dt, integer_types):
        return int8_to_date(dt)
    elif hasattr(dt, "to_pydatetime"):
        return dt.to_pydatetime()
    elif hasattr(dt, "dtype") and dt.dtype.char == "M":
        return parse_datetime(str(dt)).date()
    raise ValueError("expect a datetime like object, got %r(%r)" % (type(dt), dt))


def int_to_datetime(dt):
    # type: (int) -> datetime.datetime
    """各种int格式转datetime: 确定对象类型为8 14 17位的整数。"""
    if 9999999 < dt < 99999999:  # 8位日期
        return int8_to_datetime(dt)
    if 9999999999999 < dt < 99999999999999:  # 14位日期时间
        return int14_to_datetime(dt)
    if 9999999999999999 < dt < 99999999999999999:  # 17位日期时间
        return int17_to_datetime(dt)
    raise ValueError("a datetime int should be 8, 14 or 17 length int, now is {}".format(dt))


def split_dates_range(day_start, day_end, freq) -> List[Tuple[datetime.date, datetime.date]]:
    """
    日期的始末时间，按频率切分任务块
    :param day_start: 能被to_date识别的
    :param day_end: 能被to_date识别的
    :param freq: pandas支持的resample
    :return: 嵌套
    """
    temp = pd.date_range(to_date(day_start), to_date(day_end), freq='D')
    se = pd.Series(data=temp, index=temp)
    # 采样，并保留起始边界，结束边界
    df = se.resample(freq).agg(['min', 'max'])
    res = []
    for tu in df.iterrows():
        res.append((tu[-1]['min'].to_pydatetime().date(),
                    tu[-1]['max'].to_pydatetime().date()
                    ))
    return res


# 整数 datetime 相互转化 ----------------------------------------------------------------------------------
def int8_to_datetime(dt):
    # type: (int) -> datetime.datetime
    year, dt = dt // 10000, dt % 10000
    month, day = dt // 100, dt % 100
    return datetime.datetime(year, month, day)


_int8_vectorize = np.vectorize(lambda y, m, d: datetime.datetime(y, m, d))


def int8_to_datetime_v(dtarr):
    if not isinstance(dtarr, np.ndarray):
        dtarr = np.array(dtarr)
    years, dt = dtarr // 10000, dtarr % 10000
    months, days = dt // 100, dt % 100
    return _int8_vectorize(years, months, days)


def int14_to_datetime(dt):
    # type: (int) -> datetime.datetime
    year, dt = dt // 10000000000, dt % 10000000000
    month, dt = dt // 100000000, dt % 100000000
    day, dt = dt // 1000000, dt % 1000000
    hour, dt = dt // 10000, dt % 10000
    minute, second = dt // 100, dt % 100
    return datetime.datetime(year, month, day, hour, minute, second)


_int14_vectorize = np.vectorize(lambda y, m, d, h, mm, s: datetime.datetime(y, m, d, h, mm, s))


def int14_to_datetime_v(dtarr):
    if not isinstance(dtarr, np.ndarray):
        dtarr = np.array(dtarr)
    years, dt = dtarr // 10000000000, dtarr % 10000000000
    months = dt // 100000000
    dt %= 100000000
    days = dt // 1000000
    dt %= 1000000
    hours = dt // 10000
    dt %= 10000
    minutes, seconds = dt // 100, dt % 100
    return _int14_vectorize(years, months, days, hours, minutes, seconds)


def datetime_to_int14(dt):
    return (
            dt.year * 10000000000
            + dt.month * 100000000
            + dt.day * 1000000
            + dt.hour * 10000
            + dt.minute * 100
            + dt.second
    )


def int17_to_datetime(dt):
    # type: (int) -> datetime.datetime
    year, dt = dt // 10000000000000, dt % 10000000000000
    month, dt = dt // 100000000000, dt % 100000000000
    day, dt = dt // 1000000000, dt % 1000000000
    hour, dt = dt // 10000000, dt % 10000000
    minute, dt = dt // 100000, dt % 100000
    second, ms = dt // 1000, dt % 1000
    return datetime.datetime(year, month, day, hour, minute, second, ms * 1000)


_int17_vectorize = np.vectorize(lambda y, m, d, h, mm, s, ms: datetime.datetime(y, m, d, h, mm, s, ms))


def int17_to_datetime_v(dtarr):
    if not isinstance(dtarr, np.ndarray):
        dtarr = np.array(dtarr)
    years, dt = dtarr // 10000000000000, dtarr % 10000000000000
    months = dt // 100000000000
    dt %= 100000000000
    days = dt // 1000000000
    dt %= 1000000000
    hours = dt // 10000000
    dt %= 10000000
    minutes = dt // 100000
    dt %= 100000
    seconds, ms = dt // 1000, dt % 1000
    return _int17_vectorize(years, months, days, hours, minutes, seconds, ms * 1000)


def datetime_to_int17(dt):
    return (
            dt.year * 10000000000000
            + dt.month * 100000000000
            + dt.day * 1000000000
            + dt.hour * 10000000
            + dt.minute * 100000
            + dt.second * 1000
            + int(round(dt.microsecond / 1000))  # ms have six digits
    )


def int8_to_date(dt):
    # type: (int) -> datetime.date
    year, dt = dt // 10000, dt % 10000
    month, day = dt // 100, dt % 100
    return datetime.date(year, month, day)


def date_to_int8(dt):
    return dt.year * 10000 + dt.month * 100 + dt.day


# -------------------------------------------------------------------------------------------------------
def int9_to_time(tm):
    hour, tm = tm // 10000000, tm % 10000000
    minute, tm = tm // 100000, tm % 100000
    second, ms = tm // 1000, tm % 1000
    return datetime.time(hour, minute, second, ms * 1000)


def time_to_int9(dt):
    return (dt.hour * 10000000
            + dt.minute * 100000
            + dt.second * 1000
            + int(round(dt.microsecond / 1000))  # ms have six digits
            )


# -------------------------------------------------------------------------------------------------------
def ensure_date_int(date):
    date = to_date(date)
    return date.year * 10000 + date.month * 100 + date.day
