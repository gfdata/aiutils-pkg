# -*- coding: utf-8 -*-
# @time: 2022/3/20 18:13
# @Author：lhf
# ----------------------
from rqalpha.apis import *


def trade_dict_real(d_real):
    """
    回测框架中的下单操作
    :param d_real: 结构为 {标的：{真实合约：手数}}
    :return:
    """
    holding_pos = get_positions()  # 弱引用方式；后面发生order时，此变量也会跟着变化
    holding_old = [x.order_book_id for x in holding_pos]  # 保留合约编码，保证不会随之改变
    # 区分多头空头
    long, short = {}, {}
    for ud, temp in d_real.items():
        for k, v in temp.items():
            if v > 0:
                _ = long.get(k, 0)
                long[k] = _ + v
            elif v < 0:
                _ = short.get(k, 0)
                short[k] = _ + v

    # 不在目标持仓的先平仓
    for code in holding_old:
        if code in list(long.keys()) or code in list(short.keys()):
            continue
        else:
            user_log.debug(f'平仓{code} 至零')
            order_to(code, 0)

    # 调整多单
    for code, lots in long.items():
        old = get_position(code, POSITION_DIRECTION.LONG)
        # 新入场
        if old.quantity == 0:
            user_log.debug(f'做多 {code} 已有 {old.direction} {old.quantity} 目标 {lots}')
            order_to(code, lots)
        # 有旧持仓
        elif old.quantity != lots:
            user_log.debug(f'做多 {code} 已有 {old.direction} {old.quantity} 目标 {lots}')
            order_to(code, lots)

    # 调整空单
    for code, lots in short.items():
        old = get_position(code, POSITION_DIRECTION.SHORT)
        # 新入场
        if old.quantity == 0:
            user_log.debug(f'做空 {code} 已有 {old.direction} {old.quantity} 目标 {lots}')
            order_to(code, lots)
        # 有旧持仓
        elif old.quantity != 0 - lots:
            user_log.debug(f'做空 {code} 已有 {old.direction} {old.quantity} 目标 {lots}')
            order_to(code, lots)
