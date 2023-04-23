# -*- coding: utf-8 -*-
# @time: 2022/3/20 13:38
# @Author：lhf
# ----------------------
import datetime
import sys
from typing import NamedTuple

import pandas as pd
from rqalpha.apis import history_bars, get_previous_trading_date, Environment, ExecutionContext
from rqalpha.const import EXECUTION_PHASE

from aiutils.cache import MemoryCache

"""
扩展运行环境下常用的数据接口
* 方式a 注册api函数，使用装饰器 @export_as_api @ExecutionContext.enforce_phase
参考 rqalpha.apis.api_base.history_bars/rqalpha.apis.api_rqdatac.get_price/apis.api_rqdatac.get_dominant_future
* 方式b 普通函数，接收context作为参数，再截取环境当时的时间戳

"""


class PhaseDatetime(NamedTuple):
    phase: EXECUTION_PHASE
    now: datetime.datetime
    calendar_dt: datetime.datetime  # 自然日，时分秒为框架下的时间，一般同上面的now
    trading_dt: datetime.datetime  # 交易日，时分秒为框架下的时间
    trading_finish: datetime.datetime  # 已走完的交易日，时分秒000，date部分才有意义

    def __str__(self):
        return ','.join([k + '=' + str(v) for k, v in self._asdict().items()])


def get_phase_datetime(context) -> PhaseDatetime:
    """ 获取运行状态，以及重要的时间概念 """
    env = Environment.get_instance()
    phase = ExecutionContext.phase()
    # 时间
    cdt = env.calendar_dt  # 自然日，时分秒日频率下都是000分钟 频率下才带上
    tdt = env.trading_dt  # 交易日，时分秒都是000  todo 验证是否如此
    # 已结束的交易日
    # 注意截取可观测时间，参考源码 rqalpha.model.bar.BarObject.mavg/rqalpha.data.trading_dates_mixin.TradingDatesMixin
    if phase in [
        EXECUTION_PHASE.AFTER_TRADING,
        EXECUTION_PHASE.FINALIZED,
    ]:
        finish = env.data_proxy.get_previous_trading_date(tdt.date(), n=0)  # 只传入date部分
    elif phase == EXECUTION_PHASE.SCHEDULED:
        # SCHEDULED触发在before_trading或盘中time_rule；所以也是前一个
        finish = env.data_proxy.get_previous_trading_date(tdt.date(), n=1)
    else:
        # 推前一天
        finish = env.data_proxy.get_previous_trading_date(tdt.date(), n=1)
    return PhaseDatetime(phase, context.now, cdt, tdt,
                         datetime.datetime(finish.year, finish.month, finish.day)
                         )


# 交易日定时触发函数------------------------------------------------------------------------------------
def trading_calendar_trigger(now_td, choose_freq, choose_day) -> bool:
    """
    用于定时触发任务；判断now_td是否正好满足定时频率
    :param now_td: 传入的交易日，会忽略时分秒部分
    :param choose_freq: 定时的频率
    :param choose_day: 定时的第几天
    :return:
    """
    # 忽略时分秒部分
    _date = pd.to_datetime(now_td).date()
    _date = pd.to_datetime(_date)
    res = False
    df = trading_calendar_number()
    if choose_freq == 'd':
        num = df.loc[_date, 'td_num']
        if num % choose_day != 0:
            res = True
    elif choose_freq == 'w':
        num = df.loc[_date, 'td_week_num']
        if num == choose_day:
            res = True
    elif choose_freq == 'm':
        num = df.loc[_date, 'td_month_num']
        if num == choose_day:
            res = True
    else:
        raise ValueError(f"{sys._getframe().f_code.co_name}定时触发参数限制为 ['d', 'w', 'm']")
    return res


@MemoryCache.cached_function_result_for_a_time(cache_second=60 * 60)
def trading_calendar_number() -> pd.DataFrame:
    """ 对交易日历进行编号；每期计数起始值为1 """
    # 参考定时器写法 rqalpha.mod.rqalpha_mod_sys_scheduler.scheduler.Scheduler._fill_week
    # 使用env的全部交易日历，而非context中的部分；后者有缺失导致开始的计数不准
    trading_calendar = Environment.get_instance().data_proxy.get_trading_calendar()
    df = pd.Series(data=trading_calendar, index=trading_calendar).to_frame('trading_calendar').sort_index()
    df['td_num'] = [x + 1 for x in range(len(df))]

    def _fill_week(_today):
        weekday = _today.isoweekday()
        weekend = _today + datetime.timedelta(days=7 - weekday)
        week_start = weekend - datetime.timedelta(days=6)

        left = trading_calendar.searchsorted(datetime.datetime.combine(week_start, datetime.time.min))
        right = trading_calendar.searchsorted(datetime.datetime.combine(weekend, datetime.time.min), side='right')
        _this_week = [d.date() for d in trading_calendar[left:right]]
        return _this_week.index(_today) + 1

    def _fill_month(_today):
        try:
            month_end = _today.replace(month=_today.month + 1, day=1)
        except ValueError:
            month_end = _today.replace(year=_today.year + 1, month=1, day=1)

        month_begin = _today.replace(day=1)
        left = trading_calendar.searchsorted(datetime.datetime.combine(month_begin, datetime.time.min))
        right = trading_calendar.searchsorted(datetime.datetime.combine(month_end, datetime.time.min))
        _this_month = [d.date() for d in trading_calendar[left:right]]
        return _this_month.index(_today) + 1

    df['td_week_num'] = df['trading_calendar'].apply(_fill_week)
    df['td_month_num'] = df['trading_calendar'].apply(_fill_month)
    # # resample写法
    # df['td_week_num'] = df['trading_calendar'].resample('W').apply(
    #     lambda x: pd.Series(data=[x + 1 for x in range(len(x))], index=x.index))
    # df['td_month_num'] = df['trading_calendar'].resample('M').apply(
    #     lambda x: pd.Series(data=[x + 1 for x in range(len(x))], index=x.index))
    return df[['trading_calendar', 'td_num', 'td_week_num', 'td_month_num']]
