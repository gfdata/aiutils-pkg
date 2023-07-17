# -*- coding: utf-8 -*-
# @time: 2022/1/16 22:52
# @Author：lhf
# ----------------------
import os
import bisect
import datetime
from pathlib import Path
from typing import List
import pandas as pd
from aiutils import dt_convert
from aiutils.cache import lru_cache
from aiutils.singleton import SingletonType

_FILE = Path(__file__).absolute()


@lru_cache()
def _pd_read_excel(file, file_t):
    """
    * file_t参数，只为了方便cache识别
    * 函数内read_excel参数，要适配所读取的文件内数据位置
    """
    try:
        import xlrd  # xlrd 1.2.0以下才支持xlsx，2.0不支持；pandas 1.3.0 可用openpyxl引擎
        df = pd.read_excel(file, index_col=None, skiprows=8)
    except Exception as e:
        df = pd.read_excel(file, index_col=None, skiprows=8, engine="openpyxl")
    # 整理检查
    df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
    df = df.astype('datetime64[ns]')
    return df


class _TradeCalendar(metaclass=SingletonType):
    # 市场交易日的时间边界-->非此时间段内，划分到其它交易日
    cn_div_start = datetime.time(6)
    cn_div_end = datetime.time(18)

    def set(self, market: str, dates: List) -> List[int]:
        """
        添加交易日历
        :param market: 国内市场'cn'可以涵盖多个交易所；
        :param dates:
        :return:
        """
        # 单例模式修改属性，一般通过set方法
        dates = [dt_convert.date_to_int8(dt_convert.to_datetime(x)) for x in dates]
        self.data_dict[market] = list(sorted(dates))  # 升序list，具体值为的dates_int8格式
        return self.data_dict[market]

    def __init__(self, file_dir=_FILE.parent):
        self.data_dict = {}
        # 默认读取的
        file = os.path.join(file_dir, 'calendar.xlsx')
        self.set('cn', _pd_read_excel(file, os.path.getmtime(file))['SSE'])

    def get_div(self, market) -> tuple:
        if market == 'cn':
            return self.cn_div_start, self.cn_div_end
        else:
            raise ValueError(f"目前支持market=['cn']")

    def get(self, market: str) -> List[int]:
        try:
            dates = self.data_dict[market]
        except KeyError as e:
            raise RuntimeError(f"{self.__class__.__name__}需要先执行set()方法绑定数据")
        else:
            return dates


TradeCalendar = _TradeCalendar()


# 调用函数--------------------------------------------------------------------------------
def _map_expect_type(ty, fmt, dates):
    if ty == "int":
        return dates
    if ty == "datetime":
        return [dt_convert.int_to_datetime(dt) for dt in dates]
    if ty == "date":
        return [dt_convert.int8_to_date(dt) for dt in dates]
    if ty == "str":
        return [dt_convert.int_to_datetime(dt).strftime(fmt) for dt in dates]
    raise TypeError(ty)


def get_trading_dates_in_type(start_date, end_date, expect_type="datetime", fmt=None, market='cn'):
    """ 获取两个日期之间的交易日列表 """
    dates = TradeCalendar.get(market)

    start_date = dt_convert.ensure_date_int(start_date)
    end_date = dt_convert.ensure_date_int(end_date)
    start_pos = bisect.bisect_left(dates, start_date)
    end_pos = bisect.bisect_right(dates, end_date)
    return _map_expect_type(expect_type, fmt, dates[start_pos:end_pos])


def get_previous_trading_date(date, n=1, market="cn"):
    """ 获取前n交易日 """
    dates = TradeCalendar.get(market)

    if n < 1:
        raise ValueError("n: except a positive value, got {}".format(n))
    date = dt_convert.ensure_date_int(date)
    pos = bisect.bisect_left(dates, date)
    if pos > n:
        return dt_convert.int8_to_date(dates[pos - n])
    return dt_convert.int8_to_date(dates[0])


def get_next_trading_date(date, n=1, market='cn'):
    """ 获取后n交易日 """
    dates = TradeCalendar.get(market)

    if n < 1:
        raise ValueError("n: except a positive value, got {}".format(n))
    date = dt_convert.ensure_date_int(date)
    pos = bisect.bisect_right(dates, date)
    if pos + n - 1 < len(dates):
        return dt_convert.int8_to_date(dates[pos + n - 1])
    return dt_convert.int8_to_date(dates[-1])


def is_trading_date(date, market="cn"):
    """判断日期是否为交易日
    :param date: 日期 如20190401
    :param market:  (Default value = "cn")
    :returns: bool
    """
    date = dt_convert.ensure_date_int(date)
    dates = TradeCalendar.get(market)
    return date in dates


# ---------------------------------------------------------------------------------
def trading_date_to_nature(trading_date, market='cn') -> tuple:
    """ 扩展交易日期，到自然日边界时间段 """
    div_end = TradeCalendar.get_div(market)[-1]
    # 日期是否在交易日历中
    if is_trading_date(trading_date, market):
        valid = dt_convert.to_date(trading_date)
    else:
        valid = get_previous_trading_date(trading_date, n=1, market=market)

    # 上一交易日的结束
    td_previous = get_previous_trading_date(valid, n=1, market=market)
    nature_start = datetime.datetime.fromordinal(td_previous.toordinal()).replace(
        hour=div_end.hour, minute=div_end.minute, second=div_end.second, microsecond=div_end.microsecond)

    # 当前交易日的结束
    nature_end = datetime.datetime.fromordinal(valid.toordinal()).replace(
        hour=div_end.hour, minute=div_end.minute, second=div_end.second, microsecond=div_end.microsecond)

    return nature_start, nature_end


def get_current_trading_date(dt, market) -> datetime.date:
    """ 自然日时间戳，定位到所属交易日 """
    if _TradeCalendar.cn_div_start.hour <= dt.hour < _TradeCalendar.cn_div_end.hour:
        return datetime.date(year=dt.year, month=dt.month, day=dt.day)
    return get_next_trading_date(dt - datetime.timedelta(hours=4), n=1, market=market)
