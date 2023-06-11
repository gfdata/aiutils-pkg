# -*- coding: utf-8 -*-
# @time: 2023/4/23 2:10
# @Author：lhf
# ----------------------
from typing import Dict
from .exchange_iso import ExchangeISO


def exchange_ud() -> Dict[str, ExchangeISO]:
    """ 品种字母，对应ExchangeISO """
    from aiutils.future_classify import FutureClassify
    commodity = FutureClassify.all_data()['exchange_iso'].to_dict()
    # 一些特殊的情况
    total = {
        'S': ExchangeISO.XDCE,  # 大豆（历史上弃用的编码）
        'IO': ExchangeISO.XSHE,  # 沪深300etf期权
    }
    total.update({k: ExchangeISO(v) for k, v in commodity.items()})
    return total


def exchange_iso() -> Dict[str, ExchangeISO]:
    """ ISO标准本身的 """
    # return {member.value: member for name, member in ExchangeISO.__members__.items()}
    return {x.value: x for x in ExchangeISO}


def exchange_wind() -> Dict[str, ExchangeISO]:
    """ wind交易所编码，对应ExchangeISO """
    return {
        "SH": ExchangeISO.XSHG,
        "SZ": ExchangeISO.XSHE,

        'CFE': ExchangeISO.CCFX,
        'SHF': ExchangeISO.XSGE,
        'DCE': ExchangeISO.XDCE,
        'CZC': ExchangeISO.XZCE,
        'INE': ExchangeISO.XINE,
        'SGE': ExchangeISO.SGEX,
        'GFE': ExchangeISO.GFEX,
    }


def exchange_vnpy() -> Dict[str, ExchangeISO]:
    """ vnpy交易所编码，对应ExchangeISO """
    return {
        'CFFEX': ExchangeISO.CCFX,
        'SHFE': ExchangeISO.XSGE,
        'DCE': ExchangeISO.XDCE,
        'CZCE': ExchangeISO.XZCE,
        'INE': ExchangeISO.XINE,
        'GFEX': ExchangeISO.GFEX,
        'SSE': ExchangeISO.XSHG,
        'SZSE': ExchangeISO.XSHE,
        'SGE': ExchangeISO.SGEX,
        'WXE': ExchangeISO.CSSX,
        'CFETS': ExchangeISO.CFBC,
    }


class MapTotal(object):
    def __init__(self):
        """ 将上面的映射函数整合到一起，方便使用 """
        self._data = exchange_iso()

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def __getitem__(self, item):
        return self._data[item]

    def update(self, new: dict):
        for k, v in new.items():
            if isinstance(v, ExchangeISO):
                obj = v
            else:
                obj = ExchangeISO[v]
            if k in self._data.keys() and v != self._data[k]:
                raise ValueError(f'已存在{k}新值{obj}原值{self._data[k]}: 两者不相等请检查数据')
            else:
                self._data[k] = obj
        return self
