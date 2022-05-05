# -*- coding: utf-8 -*-
# @time: 2022/3/20 13:38
# @Author：lhf
# ----------------------
from rqalpha.apis import history_bars, get_previous_trading_date


def check_date_view_future(context, rq_func_name):
    dv1 = history_bars('AU99', 1, '1d', fields='datetime')[-1]
    dv2 = get_previous_trading_date(context.now, 0)
    dv3 = get_previous_trading_date(context.now, 1)
    print(f'\n执行约定函数 {rq_func_name} \n'
          f'context时间 {context.now} \n'
          f'history_bar方式{dv1} \n'
          f'get_previous 0 方式 {dv2} \n'
          f'get_previous 1 方式 {dv3}')
