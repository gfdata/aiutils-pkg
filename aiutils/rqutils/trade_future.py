# -*- coding: utf-8 -*-
# @time: 2022/3/20 18:13
# @Author：lhf
# ----------------------
from rqalpha.apis import *


def trade_dict_real(d_real, diff_value=0):
    """ 回测框架中的下单操作
    * d_real: 结构为 {标的：{真实合约：手数}}
    * diff_value: 新旧合约价值差距的阈值，避免小手数频繁调整；启用时会调用history_bars略微影响速度
    * 例如商品期货最大60万，股指100万；或者外部考虑账户的百分比
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
            old_long = get_position(code, POSITION_DIRECTION.LONG)
            old_short = get_position(code, POSITION_DIRECTION.SHORT)
            user_log.debug(
                f'平仓[多空归零]{code} 旧多{old_long.direction}+{old_long.quantity} 旧空{old_short.direction}-{old_short.quantity}')
            order_to(code, 0)

    # 调整多单
    for code, lots in long.items():
        old_temp = get_position(code, POSITION_DIRECTION.SHORT)
        if old_temp.quantity != 0:  # 使用order_to目标下单，其实可以不用这步判断
            user_log.debug(f'做多[旧反向]{code} 已有{old_temp.direction}-{old_temp.quantity} 先平再开{lots}')
            order_to(code, lots)

        old = get_position(code, POSITION_DIRECTION.LONG)
        # 新入场
        if old.quantity == 0:
            user_log.debug(f'做多[新入场]{code} 已有{old.direction}+{old.quantity} 目标{lots}')
            order_to(code, lots)
        # 有旧持仓
        elif old.quantity != lots:
            if diff_value <= 0:  # 直接调整
                user_log.debug(f'做多[旧调整]{code} 已有{old.direction}+{old.quantity} 目标{lots}')
                order_to(code, lots)
            else:  # 判断变动价值是否够大
                ins = instruments(code)
                price = history_bars(code, 1, '1d', 'close')[-1]
                v = ins.contract_multiplier * price * abs(abs(old.quantity) - abs(lots))
                if v > diff_value:
                    user_log.debug(f'做多[旧调整]变动够大{code} 已有{old.direction}+{old.quantity} 目标{lots}')
                    order_to(code, lots)

    # 调整空单
    for code, lots in short.items():
        old_temp = get_position(code, POSITION_DIRECTION.LONG)
        if old_temp.quantity != 0:  # 使用order_to目标下单，其实可以不用这步判断
            user_log.debug(f'做空[旧反向]{code} 已有{old_temp.direction}+{old_temp.quantity} 先平再开{lots}')
            order_to(code, lots)

        old = get_position(code, POSITION_DIRECTION.SHORT)
        # 新入场
        if old.quantity == 0:
            user_log.debug(f'做空[新入场]{code} 已有{old.direction}-{old.quantity} 目标{lots}')
            order_to(code, lots)
        # 有旧持仓
        elif old.quantity != 0 - lots:
            if diff_value <= 0:
                user_log.debug(f'做空[旧调整]{code} 已有{old.direction}-{old.quantity} 目标{lots}')
                order_to(code, lots)
            else:
                ins = instruments(code)
                price = history_bars(code, 1, '1d', 'close')[-1]
                v = ins.contract_multiplier * price * abs(abs(old.quantity) - abs(lots))
                if v > diff_value:
                    user_log.debug(f'做空[旧调整]变动够大{code} 已有{old.direction}-{old.quantity} 目标{lots}')
                    order_to(code, lots)
