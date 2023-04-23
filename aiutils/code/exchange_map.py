# -*- coding: utf-8 -*-
# @time: 2023/4/23 2:10
# @Author：lhf
# ----------------------
from typing import Dict

from aiutils.future_classify import FutureClassify
from .exchange_iso import ExchangeISO


def exchange_ud() -> Dict[str, ExchangeISO]:
    """ 品种字母，对应ExchangeISO """
    commodity = FutureClassify.all_data()['exchange_iso'].to_dict()
    # 一些特殊的情况
    total = {
        'S': ExchangeISO.XDCE,  # 大豆（历史上弃用的编码）
        'IO': ExchangeISO.XSHE,  # 沪深300etf期权
    }
    total.update({k: ExchangeISO(v) for k, v in commodity.items()})
    return total


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
