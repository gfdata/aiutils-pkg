# -*- coding: utf-8 -*-
# @time: 2021/12/27 21:13
# @Author：lhf

import datetime
from typing import List
from collections import namedtuple

from .tools import SectionBoundary, THIRD_DT_FORMAT_S

DatetimeRange = namedtuple('DatetimeRange', ['start', 'end'])


def str_to_datetime_range(date_time_str, exg_str, frequency, open_auction=True) -> List[DatetimeRange]:
    """
    解析交易时间字符串`date_time_str` 为List["DatetimeRange"]
    * 规则如下：字符串为 `分钟数据时间戳的右边界`；逗号隔开小节时间；按小节顺序排列；
        000001.XSHE:  '%Y-%m-%d 09:31~%Y-%m-%d 11:30,%Y-%m-%d 13:01~%Y-%m-%d 15:00'
        T2012:        '%Y-%m-%d 09:31~%Y-%m-%d 11:30,%Y-%m-%d 13:01~%Y-%m-%d 15:15'
        RB2101:       '%Y-%m-%d 21:01~%Y-%m-%d 23:00,%Y-%m-%d 09:01~%Y-%m-%d 10:15,%Y-%m-%d 10:31~%Y-%m-%d 11:30,%Y-%m-%d 13:31~%Y-%m-%d 15:00'
        AU2102:       '%Y-%m-%d 21:01~%Y-%m-%d 02:30,%Y-%m-%d 09:01~%Y-%m-%d 10:15,%Y-%m-%d 10:31~%Y-%m-%d 11:30,%Y-%m-%d 13:31~%Y-%m-%d 15:00'

    * 因此，每小节的start原始字符串中多加了1分钟，但是夜盘time(0,0)没有加，因为是连着前面23点的时段。
    * frequency=='tick'且open_auction is True时处理方式：简单处理为开盘时间前推15min（暂不区分各交易所的集合竞价时间）

    :param date_time_str:
    :param exg_str: 合约的交易所简称
    :param frequency: assert in ['1m','tick']
    :param open_auction: 是否加入集合竞价时段
    :return:
    """
    assert frequency in ["1m", "tick"]
    if date_time_str is None or date_time_str.strip() == '':
        raise ValueError(f'`section_str` should not be None or empty string ')

    if frequency == '1m':
        return _section_str_reback(date_time_str, frequency)

    elif frequency == "tick":
        res = _section_str_reback(date_time_str, frequency)
        if not open_auction:
            return res
        # 需要加开盘时段的情况
        res_adj = []
        first_start = res[0].start - SectionBoundary.get(exg_str).acution
        first_end = res[0].end
        res_adj.append(DatetimeRange(first_start, first_end))
        res_adj.extend(res[1:])
        return res_adj


def _section_str_reback(section_str, frequency):
    """
    对字符串进行还原
    * 仍保留顺序，开盘在List[0]位置
    """
    trading_period = []
    for time_range_str in section_str.split(","):
        temp = time_range_str.split('~')
        assert len(temp) == 2
        start = datetime.datetime.strptime(temp[0], THIRD_DT_FORMAT_S)
        end = datetime.datetime.strptime(temp[-1], THIRD_DT_FORMAT_S)
        # tick情况-->把1分钟加回来
        if frequency == 'tick':
            start = start - datetime.timedelta(minutes=1)

        # 跨凌晨的交易时段-->不切分，直接添加
        trading_period.append(DatetimeRange(start, end))
    return trading_period


def dt_in_datetime_range(dt: datetime.datetime,
                         dt_range_list: List[DatetimeRange],
                         left_s: int = 0, right_s: int = 0
                         ) -> bool:
    """
    包含日期部分，适用于历史行情数据过滤

    * 误差边界：left_s right_s自己传入，或使用 TRADING_SECTION_RULE.get(save_type)选用设定好的规则
    * 设置right_s=4，收盘(右边界)秒数小于4s的也保留，例如
        AU2012,2020-08-27 15:00:00.500；
        000001.XSHE,2020-08-24 11:30:00.000, 2020-08-24 15:00:03.00
    * 这类数据还是有意义的【其他平台也做了保留，因此选择此类处理方式】

    :param dt:
    :param dt_range_list:
    :param left_s:误差秒数，早于每节start该秒数仍为True
    :param right_s:误差秒数，晚于每节end该秒数仍为True
    :return:
    """
    right_s = max(0, right_s)
    dt_r = dt - datetime.timedelta(seconds=right_s)
    _ = any(r.start <= dt_r <= r.end for r in (dt_range_list or []))
    if _:
        return _

    left_s = max(0, left_s)
    dt_l = dt + datetime.timedelta(seconds=left_s)
    _ = any(r.start <= dt_l <= r.end for r in (dt_range_list or []))
    if _:
        return _

    return False
