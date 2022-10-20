# -*- coding: utf-8 -*-
# @time: 2022/3/20 13:38
# @Author：lhf
# ----------------------
import datetime
from functools import lru_cache

import pandas as pd
from rqalpha.apis import history_bars, get_previous_trading_date, Environment


def check_date_view_future(context, rq_func_name):
    dv1 = history_bars('AU99', 1, '1d', fields='datetime')[-1]
    dv2 = get_previous_trading_date(context.now, 0)
    dv3 = get_previous_trading_date(context.now, 1)
    print(f'\n执行约定函数 {rq_func_name} \n'
          f'context时间 {context.now} \n'
          f'history_bar方式{dv1} \n'
          f'get_previous 0 方式 {dv2} \n'
          f'get_previous 1 方式 {dv3}')


def trading_calendar_trigger(now_td, choose_freq, choose_day) -> bool:
    """
    判断是否定时触发
    """
    now_td = pd.to_datetime(now_td)
    res = False
    df = trading_calendar_scheduler()
    if choose_freq == 'd':
        num = df.loc[now_td, 'td_num']
        if num % choose_day != 0:
            res = True
    elif choose_freq == 'w':
        num = df.loc[now_td, 'td_week_num']
        if num == choose_day:
            res = True
    elif choose_freq == 'm':
        num = df.loc[now_td, 'td_month_num']
        if num == choose_day:
            res = True
    else:
        raise ValueError(f"定时任务周期限制为 ['d', 'w', 'm']")
    return res


@lru_cache()
def trading_calendar_scheduler() -> pd.DataFrame:
    """
    每期计数起始值为 1；参考定时器写法 rqalpha.mod.rqalpha_mod_sys_scheduler.scheduler.Scheduler._fill_week
    :return:
    """
    # 使用env的全部交易日历；而非context中的部分，有缺失导致开始的计数不准
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
