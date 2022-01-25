# -*- coding: utf-8 -*-
# @time: 2021/12/24 9:12
# @Author：lhf

import warnings
from copy import deepcopy
from enum import Enum

from aiutils import futureClassify
from aiutils.singleton import SingletonType


class ExchangeISO(Enum):
    """ 采用ISO market identifier(MIC) 编码
    https://www.iso20022.org/market-identifier-codes
    未纳入的，则返回各平台原始方式；
    todo mark~新交易所纳入时，继续添加
    """
    # ISO COUNTRY=CN
    CFBC = 'CFBC'  # CHINA FOREIGN EXCHANGE TRADE SYSTEM - SHANGHAI - HONG KONG BOND CONNECT
    XSHG = 'XSHG'  # SHANGHAI STOCK EXCHANGE
    XSHE = 'XSHE'  # SHENZHEN STOCK EXCHANGE

    CCFX = 'CCFX'  # CHINA FINANCIAL FUTURES EXCHANGE
    XSGE = 'XSGE'  # SHANGHAI FUTURES EXCHANGE
    XDCE = 'XDCE'  # DALIAN COMMODITY EXCHANGE
    XZCE = 'XZCE'  # ZHENGZHOU COMMODITY EXCHANGE
    XINE = 'XINE'  # SHANGHAI INTERNATIONAL ENERGY EXCHANGE

    SGEX = 'SGEX'  # SHANGHAI GOLD EXCHANGE
    CSSX = 'CSSX'  # CHINA STAINLESS STEEL EXCHANGE


class _ExchangeMap(metaclass=SingletonType):
    """
    通过交易所缩写字符串，来找到ExchangeISO对象
    * 在 code_by_common 函数中的参数exchange_map可以使用；也可以传入自定义的
    * 私有类不应直接调用，而是使用下面已经实例化的对象 ExchangeMap

    """
    # {member.value: member for name, member in Exchange.__members__.items()}
    _data: dict = {x.value: x for x in ExchangeISO}

    def update(self, new: dict):
        for k, v in new.items():
            if k in self._data.keys() and v != self._data[k]:
                msg = f'已存在{k}覆盖写入！新值{v} 原值{self._data[k]}'
                warnings.warn(msg)
        self._data.update(new)

    @property
    def data(self):
        return self._data


# ---------------------------------------------------------------------------------
ExchangeMap = _ExchangeMap()
ExchangeMap.update({
    "SH": ExchangeISO.XSHG,
    'SZ': ExchangeISO.XSHE,
})

# vnpy 写法
ExchangeMap.update({
    'CFFEX': ExchangeISO.CCFX,
    'SHFE': ExchangeISO.XSGE,
    'DCE': ExchangeISO.XDCE,
    'CZCE': ExchangeISO.XZCE,
    'INE': ExchangeISO.XINE,
    'SSE': ExchangeISO.XSHG,
    'SZSE': ExchangeISO.XSHE,
    'SGE': ExchangeISO.SGEX,
    'WXE': ExchangeISO.CSSX,
    'CFETS': ExchangeISO.CFBC,
})

# 通过品种字母，来找到Exchange------------------------------------------------------------
# 国内商品期货期权，underlying对应交易所
_ud_exchange_commodity = deepcopy(futureClassify.all_data()['exchange_iso'].to_dict())

# 特殊的情况
UD_EXCHANGE = {
    'S': 'XDCE',  # 大豆（历史上弃用的编码）
    'IO': 'XSHE',  # 沪深300etf期权
}

UD_EXCHANGE.update({k: v for k, v in _ud_exchange_commodity.items()})
