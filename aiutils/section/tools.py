# -*- coding: utf-8 -*-
# @time: 2021/12/27 21:14
# @Author：lhf

import datetime
from collections import namedtuple

from aiutils.code.unique_exchange import ExchangeISO, ExchangeMap

THIRD_DT_FORMAT_S = '%Y-%m-%d %H:%M:%S'

SectionBoundaryParams = namedtuple('params', ['acution',  # 连续竞价基础上左移集合竞价timedelta, 用于str_to_xx_range
                                              'left_s', 'right_s'])  # 用于dt_in_xx_range的边界


class SectionBoundary:
    """
    不同交易所，交易时段的时间边界调整默认参数
    todo mark~有新交易所时，继续添加
    """
    params = SectionBoundaryParams
    # 照顾到最大的时间偏差情况
    common = params(acution=datetime.timedelta(minutes=15), left_s=0, right_s=30)
    dic = {
        # 证券交易所
        # 集合竞价15min，有数据变化 反映挂撤情况，09:25推第一个五档价格，09:30推第一个连续竞价tick；尾盘15:00:03左右的数据仍有意义
        # 证券接口xtp的末端晚的时间不确定，所以right_s设为30
        # 证券交易所的金融期权，推送时间也是类似股票
        ExchangeISO.XSHG: params(acution=datetime.timedelta(minutes=15), left_s=0, right_s=30),
        ExchangeISO.XSHE: params(acution=datetime.timedelta(minutes=15), left_s=0, right_s=30),

        # 期货交易所
        # 集合竞价5min，ctp在开盘前1min才推数据；尾盘如15:00:00.5这类与14:59最后的数据没差别，所以right_s设为0
        ExchangeISO.CCFX: params(acution=datetime.timedelta(minutes=5), left_s=0, right_s=0),
        ExchangeISO.XSGE: params(acution=datetime.timedelta(minutes=5), left_s=0, right_s=0),
        ExchangeISO.XDCE: params(acution=datetime.timedelta(minutes=5), left_s=0, right_s=0),
        ExchangeISO.XZCE: params(acution=datetime.timedelta(minutes=5), left_s=0, right_s=0),
        ExchangeISO.XINE: params(acution=datetime.timedelta(minutes=5), left_s=0, right_s=0),

        # 现货交易所
        ExchangeISO.SGEX: None,  # 暂不清楚spot，设为None，返回common代替
        ExchangeISO.CSSX: None,

    }

    @classmethod
    def get(cls, exg_str: str) -> SectionBoundaryParams:
        if isinstance(exg_str, str):
            obj = ExchangeMap.data.get(exg_str.upper())
        else:
            assert isinstance(exg_str, ExchangeISO), f'参数要求为Enum中的对象'
            obj = exg_str

        # 返回结果
        temp = cls.dic.get(obj, None)
        if temp:
            return temp
        else:
            return cls.common
