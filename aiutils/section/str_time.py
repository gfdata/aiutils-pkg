# -*- coding: utf-8 -*-
# @time: 2021/12/27 21:35
# @Author：lhf

import datetime
from collections import namedtuple
from typing import List

from aiutils.section.tools import TRADING_SECTION_RULE

TimeRange = namedtuple('TimeRange', ['start', 'end'])


def str_to_time_range(time_str: str, save_type, frequency="1m", open_auction=True) -> List[TimeRange]:
    """
    解析交易时间字符串`time_str` 为List["TimeRange"]，注意几点：
    * all_instruments表中'trading_hours'的存储字符串规则：`分钟数据时间戳的右边界`、逗号隔开小节时间、开盘时间点在最前。
        000001.XSHE:  '09:31~11:30,13:01~15:00'
        T2012:        '09:31~11:30,13:01~15:15'
        RB2101:       '21:01~23:00,09:01~10:15,10:31~11:30,13:31~15:00'
        AU2102:       '21:01~02:30,09:01~10:15,10:31~11:30,13:31~15:00'
        AUTD.SGEX：   '20:01~02:30,09:01~15:30'

    * 因此，每小节的start原始字符串中多加了1分钟，但是夜盘time(0,0)没有加，因为是连着前面23点的时段。
    * frequency=='tick'且open_auction is True时处理方式：
    * 简单处理为开盘时间前推15min（暂不区分各交易所的集合竞价时间）

    :param time_str:
    :param save_type: 合约存储类型
    :param frequency: assert in ['1m','tick']
    :param open_auction: 是否加入集合竞价时段
    :return:
    """
    assert frequency in ["1m", "tick"]
    if time_str is None or time_str.strip() == '':
        # 更详细的获取trading_hours字符串，参考rqdatac.get_trading_hours
        raise ValueError(f'`trading_hours` should not be None or empty string ')

    if frequency == '1m':
        return _gen_trading_period(time_str, frequency)
    elif frequency == "tick":
        trading_hours = ",".join([s[:4] + str(int(s[4]) - 1) + s[5:] for s in time_str.split(",")])  # 修正左边界
        res = _gen_trading_period(trading_hours, frequency)

        if not open_auction:
            return res

        res_adj = []
        now = datetime.datetime.now()
        temp_1 = datetime.datetime.combine(now.date(), res[0].start)
        temp_2 = temp_1 - TRADING_SECTION_RULE.get(save_type).acution
        assert temp_1.date() == temp_2.date()  # 不能隔日
        res_adj.append(TimeRange(temp_2.time(), res[0].end))
        res_adj.extend(res[1:])
        return res_adj


def _gen_trading_period(trading_hours: str, frequency) -> List[TimeRange]:
    """ 对trading_hours切分，仍保留顺序，开盘在List[0]位置。"""
    trading_period = []
    trading_hours = trading_hours.replace("~", ":")
    for time_range_str in trading_hours.split(","):
        start_h, start_m, end_h, end_m = (int(i) for i in time_range_str.split(":"))
        start, end = datetime.time(start_h, start_m), datetime.time(end_h, end_m)
        if start > end:
            if frequency == 'tick':
                trading_period.append(TimeRange(start, datetime.time.max))  # (23, 59, 59, 999999)
                trading_period.append(TimeRange(datetime.time.min, end))
            else:
                trading_period.append(TimeRange(start, datetime.time(23, 59)))
                trading_period.append(TimeRange(datetime.time(0, 0), end))
        else:
            trading_period.append(TimeRange(start, end))
    return trading_period


def dt_in_time_range(dt: datetime.datetime,
                     time_range_list: List[TimeRange],
                     left_s: int = 0, right_s: int = 0
                     ) -> bool:
    """
    只含时间部分，适用于实时行情快速过滤（一是没有考虑历史上的调整；二是没有考虑节假日前后，夜盘时段有时候没有，此时起不到过滤作用；三是退市合约可能为空）

    * 此处只判断了time，没有判断日期。如有需要，应该调用此函数之前先进行日期判断。
    * left_s right_s自己传入，或选用 TRADING_SECTION_RULE.get(save_type)选用设定好的规则。
    * 设置right_s=4，收盘(右边界)秒数小于4s的也保留，例如
        AU2012,2020-08-27 15:00:00.500；
        000001.XSHE,2020-08-24 11:30:00.000, 2020-08-24 15:00:03.00
    * 这类数据还是有意义的【其他平台也做了保留，因此选择此类处理方式】

    :param dt:
    :param time_range_list:
    :param left_s:误差秒数，早于每节start该秒数仍为True
    :param right_s:误差秒数，晚于每节end该秒数仍为True
    :return:
    """
    right_s = max(0, right_s)
    dt_r = dt - datetime.timedelta(seconds=right_s)
    dt_r = dt_r.time()
    _ = any(r.start <= dt_r <= r.end for r in (time_range_list or []))
    if _:
        return _

    left_s = max(0, left_s)
    dt_l = dt + datetime.timedelta(seconds=left_s)
    dt_l = dt_l.time()
    _ = any(r.start <= dt_l <= r.end for r in (time_range_list or []))
    if _:
        return _

    return False


def merge_time_range(time_range_list: List[TimeRange]) -> List[TimeRange]:
    """
    List[TimeRange]交易小节顺序打乱，按大小排序。
    用于融合多个合约的trading_period，表示这些时段内会有交易数据。
    :param time_range_list:
    :return:
    """
    # 参考写法 rqalpha.utils.merge_trading_period
    result = []
    for time_range in sorted(set(time_range_list)):
        if result and result[-1].end >= time_range.start:
            result[-1] = TimeRange(start=result[-1].start, end=max(result[-1].end, time_range.end))
        else:
            result.append(time_range)
    return result
