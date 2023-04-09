# -*- coding: utf-8 -*-
import sys
from functools import lru_cache
from typing import List, Tuple
import pandas as pd

import datetime
from dateutil.parser import parse as parse_datetime
import numpy as np
from six import string_types, integer_types
from .cache import lru_cache, hashable_lru

"""
时间解析及转换：
* 8位(年月日)、14位(保留到秒)、17位(保留到毫秒)，9位(时分秒毫秒)
* 根据整数位数不同，可以还原所需datetime相关对象
"""


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


# 日期范围切分----------------------------------------------------------------------------------------------
@lru_cache()
def split_dates_more(start, end, freq, extend_end=True) -> pd.DataFrame:
    """
    切分日期范围，当分块任务需要读取缓存时，扩展日期范围方便生成缓存
    * 补充`start`为该频率的第一个日期
    * 此处会生成全部日期，包括自然日（非交易日）的阶段
    :param start:
    :param end:
    :param freq: 切分频率
    :param extend_end: 是否扩展end为该频率最后一个日期
    :return: pd.DataFrame
    """
    # 参考材料 https://www.jianshu.com/p/2a4522c76dca
    from pandas.tseries.frequencies import to_offset
    start = pd.to_datetime(start).normalize()
    end = pd.to_datetime(end).normalize()
    of = to_offset(freq)
    start_use = pd.to_datetime(start) - of + pd.offsets.Day()  # 起始时间扩展，到该频率的第一个日期
    start_use.normalize()
    assert start_use <= start, f'时间段划分有漏洞 {sys._getframe().f_code.co_name}'
    if extend_end:
        end_use = pd.to_datetime(end) + of  # 结束时间扩展，该频率的最后一个日期
        assert end_use >= end, f'时间段划分有漏洞 {sys._getframe().f_code.co_name}'
    else:
        end_use = end

    # 切分时间段
    td = pd.date_range(start_use, end_use, freq='D')
    se = pd.Series(index=pd.to_datetime(td), data=td, name='td')
    return split_dates_series(se=se, freq=freq, tag_dropna=True)


@lru_cache()
def split_dates_range(day_start, day_end, freq) -> pd.DataFrame:
    """
    按频率切分任务块
    """
    temp = pd.date_range(to_date(day_start), to_date(day_end), freq='D')
    se = pd.Series(data=temp, index=temp)
    df = split_dates_series(se=se, freq=freq, tag_dropna=True)
    return df


def split_dates_series(se: pd.Series, freq, tag_dropna=True) -> pd.DataFrame:
    """
    时间索引的series进行切分
    * 如果是交易日历按week采样时，碰到春节或国庆假期，可能都是nan；tag_dropna 决定是否去掉这个区间
    """
    assert isinstance(se.index, pd.DatetimeIndex), f'series参数：要求为时间索引'
    df = se.resample(freq).agg(['min', 'max']).sort_index(ascending=True)
    if tag_dropna:
        df = df.dropna(how='any')
    return df


def split_dates_tolist(df: pd.DataFrame) -> List[Tuple[datetime.date, datetime.date]]:
    """ 转化结果形式为 嵌套list """
    res = []
    for tu in df.iterrows():
        res.append(
            (tu[-1]['min'].to_pydatetime().date(), tu[-1]['max'].to_pydatetime().date())
        )
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
