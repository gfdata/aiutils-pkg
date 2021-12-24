# -*- coding: utf-8 -*-
# @time: 2021/12/24 9:12
# @Author：lhf

import warnings
from enum import Enum

from aiutils.singleton import SingletonType


class Exchange(Enum):
    """ 采用ISO market identifier(MIC) 编码
    https://www.iso20022.org/market-identifier-codes
    未纳入的，则返回各平台原始方式
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
    # {member.value: member for name, member in Exchange.__members__.items()}
    _data: dict = {x.value: x for x in Exchange}

    def update(self, new: dict):
        for k, v in new.items():
            if k in self._data.keys() and v != self._data[k]:
                msg = f'已存在{k}覆盖写入！新值{v} 原值{self._data[k]}'
                warnings.warn(msg)
        self._data.update(new)

    @property
    def data(self):
        return self._data


# -------------------------------------------------------
""" 通过交易所缩写，来找到Exchange
* 在code_by_common函数中使用；可以用通用的，也自定义传入

"""
ExchangeMap = _ExchangeMap()
ExchangeMap.update({
    "SH": Exchange.XSHG,
    'SZ': Exchange.XSHE,
})

# vnpy 写法
ExchangeMap.update({
    'CFFEX': Exchange.CCFX,
    'SHFE': Exchange.XSGE,
    'DCE': Exchange.XDCE,
    'CZCE': Exchange.XZCE,
    'INE': Exchange.XINE,
    'SSE': Exchange.XSHG,
    'SZSE': Exchange.XSHE,
    'SGE': Exchange.SGEX,
    'WXE': Exchange.CSSX,
    'CFETS': Exchange.CFBC,
})

# -----------------------------------------------------------------------
""" 通过品种字母，来找到Exchange
* 根据underlying对应交易所；硬编码方式，有新合约上市时要此处加上

"""
UD_EXCHANGE = {
    'IO': 'XSHE',  # 沪深300etf期权
}
UD_EXCHANGE.update({
    'S': 'XDCE',  # 大豆（弃用的编码）
})

UD_EXCHANGE.update({  # 国内商品期货期权，根据underlying对应交易所；硬编码方式，有新合约上市时要此处加上
    'A': 'XDCE',
    'AG': 'XSGE',
    'AL': 'XSGE',
    'AP': 'XZCE',
    'AU': 'XSGE',
    'B': 'XDCE',
    'BB': 'XDCE',
    'BC': 'XINE',
    'BU': 'XSGE',
    'C': 'XDCE',
    'CF': 'XZCE',
    'CJ': 'XZCE',
    'CS': 'XDCE',
    'CU': 'XSGE',
    'CY': 'XZCE',
    'EB': 'XDCE',
    'EG': 'XDCE',
    'ER': 'XZCE',
    'FB': 'XDCE',
    'FG': 'XZCE',
    'FU': 'XSGE',
    'GN': 'XZCE',
    'HC': 'XSGE',
    'I': 'XDCE',
    'IC': 'CCFX',
    'IF': 'CCFX',
    'IH': 'CCFX',
    'J': 'XDCE',
    'JD': 'XDCE',
    'JM': 'XDCE',
    'JR': 'XZCE',
    'L': 'XDCE',
    'LH': 'XDCE',
    'LR': 'XZCE',
    'LU': 'XINE',
    'M': 'XDCE',
    'MA': 'XZCE',
    'ME': 'XZCE',
    'NI': 'XSGE',
    'NR': 'XINE',
    'OI': 'XZCE',
    'P': 'XDCE',
    'PB': 'XSGE',
    'PF': 'XZCE',
    'PG': 'XDCE',
    'PK': 'XZCE',
    'PM': 'XZCE',
    'PP': 'XDCE',
    'RB': 'XSGE',
    'RI': 'XZCE',
    'RM': 'XZCE',
    'RO': 'XZCE',
    'RR': 'XDCE',
    'RS': 'XZCE',
    'RU': 'XSGE',
    'SA': 'XZCE',
    'SC': 'XINE',
    'SF': 'XZCE',
    'SM': 'XZCE',
    'SN': 'XSGE',
    'SP': 'XSGE',
    'SR': 'XZCE',
    'SS': 'XSGE',
    'T': 'CCFX',
    'TA': 'XZCE',
    'TC': 'XZCE',
    'TF': 'CCFX',
    'TS': 'CCFX',
    'UR': 'XZCE',
    'V': 'XDCE',
    'WH': 'XZCE',
    'WR': 'XSGE',
    'WS': 'XZCE',
    'WT': 'XZCE',
    'Y': 'XDCE',
    'ZC': 'XZCE',
    'ZN': 'XSGE',
}
)
