# -*- coding: utf-8 -*-
# @time: 2021/12/27 21:14
# @Author：lhf

import datetime
from collections import namedtuple

THIRD_DT_FORMAT_S = '%Y-%m-%d %H:%M:%S'


class TRADING_SECTION_RULE:
    """
    不同类型，对应的交易时段边界调整；todo 固定写法，可按需调整
    """
    params = namedtuple('params', ['acution',  # 连续竞价基础上左移集合竞价timedelta, 用于gen_trading_period
                                   'left_s', 'right_s'])  # 用于dt_in_trading_period
    dic = {
        # 照顾到最大的时间偏差情况
        'common': params(acution=datetime.timedelta(minutes=15), left_s=0, right_s=30),

        # 集合竞价15min，有数据变化 反映挂撤情况，09:25推第一个五档价格，09:30推第一个连续竞价tick；尾盘15:00:03左右的数据仍有意义
        #  证券接口xtp的末端晚的时间不确定，所以right_s设为30
        'stock': params(acution=datetime.timedelta(minutes=15), left_s=0, right_s=30),
        'fund': params(acution=datetime.timedelta(minutes=15), left_s=0, right_s=30),  # 同stock
        'index': None,  # 暂不清楚，用common

        # 集合竞价5min，ctp在开盘前1min才推数据；尾盘如15:00:00.5这类与14:59最后的数据没差别，所以right_s设为0
        'future': params(acution=datetime.timedelta(minutes=5), left_s=0, right_s=0),
        # 注意证券交易所的option集合竞价时间同stock
        'option': params(acution=datetime.timedelta(minutes=15), left_s=0, right_s=30),

        'repo': None,
        'spot': None,  # 暂不清楚spot，common代替
        'convertible': params(acution=datetime.timedelta(minutes=15), left_s=0, right_s=30),  # 同stock
    }

    @classmethod
    def get(cls, save_type: str):
        if cls.dic.get(save_type.lower(), None):
            return cls.dic.get(save_type.lower())
        else:
            return cls.dic.get('common')
