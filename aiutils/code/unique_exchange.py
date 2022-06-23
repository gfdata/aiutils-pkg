# -*- coding: utf-8 -*-
# @time: 2021/12/24 9:12
# @Author：lhf

import warnings
from copy import deepcopy

from aiutils import futureClassify
from aiutils.singleton import SingletonType

from .unique_const import ExchangeISO


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
# wind 写法
EXCHANGE_WIND = {
    "SH": ExchangeISO.XSHG,
    "SZ": ExchangeISO.XSHE,

    'CFE': ExchangeISO.CCFX,
    'SHF': ExchangeISO.XSGE,
    'DCE': ExchangeISO.XDCE,
    'CZC': ExchangeISO.XZCE,
    'INE': ExchangeISO.XINE,
    'SGE': ExchangeISO.SGEX,
}
ExchangeMap.update({k: v for k, v in EXCHANGE_WIND.items()})

# vnpy 写法
EXCHANGE_VNPY = {
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
}
ExchangeMap.update({k: v for k, v in EXCHANGE_VNPY.items()})

# 通过品种字母，来找到Exchange------------------------------------------------------------
# 国内商品期货期权，underlying对应交易所
_ud_exchange_commodity = deepcopy(futureClassify.all_data()['exchange_iso'].to_dict())

# 特殊的情况
UD_EXCHANGE = {
    'S': 'XDCE',  # 大豆（历史上弃用的编码）
    'IO': 'XSHE',  # 沪深300etf期权
}

UD_EXCHANGE.update({k: v for k, v in _ud_exchange_commodity.items()})
