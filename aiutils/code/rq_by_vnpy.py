# -*- coding: utf-8 -*-
"""
@time: 2021/11/3 13:52
@file: rq_by_vnpy.py

"""
import warnings

import six
from enum import Enum
from typing import Tuple, List

from functools import lru_cache


class Exchange(Enum):
    """
    Exchange.
    """
    # Chinese
    CFFEX = "CFFEX"  # China Financial Futures Exchange
    SHFE = "SHFE"  # Shanghai Futures Exchange
    CZCE = "CZCE"  # Zhengzhou Commodity Exchange
    DCE = "DCE"  # Dalian Commodity Exchange
    INE = "INE"  # Shanghai International Energy Exchange
    SSE = "SSE"  # Shanghai Stock Exchange
    SZSE = "SZSE"  # Shenzhen Stock Exchange
    SGE = "SGE"  # Shanghai Gold Exchange
    WXE = "WXE"  # Wuxi Steel Exchange
    CFETS = "CFETS"  # China Foreign Exchange Trade System

    # Global
    SMART = "SMART"  # Smart Router for US stocks
    NYSE = "NYSE"  # New York Stock Exchnage
    NASDAQ = "NASDAQ"  # Nasdaq Exchange
    ARCA = "ARCA"  # ARCA Exchange
    EDGEA = "EDGEA"  # Direct Edge Exchange
    ISLAND = "ISLAND"  # Nasdaq Island ECN
    BATS = "BATS"  # Bats Global Markets
    IEX = "IEX"  # The Investors Exchange
    NYMEX = "NYMEX"  # New York Mercantile Exchange
    COMEX = "COMEX"  # COMEX of CME
    GLOBEX = "GLOBEX"  # Globex of CME
    IDEALPRO = "IDEALPRO"  # Forex ECN of Interactive Brokers
    CME = "CME"  # Chicago Mercantile Exchange
    ICE = "ICE"  # Intercontinental Exchange
    SEHK = "SEHK"  # Stock Exchange of Hong Kong
    HKFE = "HKFE"  # Hong Kong Futures Exchange
    HKSE = "HKSE"  # Hong Kong Stock Exchange
    SGX = "SGX"  # Singapore Global Exchange
    CBOT = "CBT"  # Chicago Board of Trade
    CBOE = "CBOE"  # Chicago Board Options Exchange
    CFE = "CFE"  # CBOE Futures Exchange
    DME = "DME"  # Dubai Mercantile Exchange
    EUREX = "EUX"  # Eurex Exchange
    APEX = "APEX"  # Asia Pacific Exchange
    LME = "LME"  # London Metal Exchange
    BMD = "BMD"  # Bursa Malaysia Derivatives
    TOCOM = "TOCOM"  # Tokyo Commodity Exchange
    EUNX = "EUNX"  # Euronext Exchange
    KRX = "KRX"  # Korean Exchange
    OTC = "OTC"  # OTC Forex Broker
    IBKRATS = "IBKRATS"  # Paper Trading Exchange of IB

    # CryptoCurrency
    BITMEX = "BITMEX"
    OKEX = "OKEX"
    HUOBI = "HUOBI"
    BITFINEX = "BITFINEX"
    BINANCE = "BINANCE"
    BYBIT = "BYBIT"  # bybit.com
    COINBASE = "COINBASE"
    DERIBIT = "DERIBIT"
    GATEIO = "GATEIO"
    BITSTAMP = "BITSTAMP"

    # Special Function
    LOCAL = "LOCAL"  # For local generated data


def unique_by_vnpy(order_book_ids) -> str or List:
    warnings.warn('本方法还有漏洞不能完全识别，请使用 aiutils.code.code_by_common 函数', DeprecationWarning)
    if isinstance(order_book_ids, six.string_types):
        return _unique_by_vnpy(order_book_ids)
    elif isinstance(order_book_ids, list):
        return [_unique_by_vnpy(o) for o in order_book_ids]
    else:
        raise ValueError("order_book_ids should be str or list")


@lru_cache()
def _unique_by_vnpy(vt_symbol):
    symbol, exchange_str = vt_symbol.split(".")
    exchange = Exchange(exchange_str)
    return to_rq_symbol(symbol, exchange).upper()


def to_rq_symbol(symbol: str, exchange: Exchange) -> str:
    """将交易所代码转换为米筐代码"""
    # 股票
    if exchange in [Exchange.SSE, Exchange.SZSE]:
        if exchange == Exchange.SSE:
            rq_symbol = f"{symbol}.XSHG"
        else:
            rq_symbol = f"{symbol}.XSHE"
        # hf20211103 上交所和深交所：股票编码6位，期权编码8位，债券编码6位；因此要做区分
        if len(symbol) == 8:
            rq_symbol = symbol  # rq期权不带交易所后缀

    # 金交所现货
    elif exchange in [Exchange.SGE]:
        for char in ["(", ")", "+"]:
            symbol = symbol.replace(char, "")
        symbol = symbol.upper()
        rq_symbol = f"{symbol}.SGEX"
    # 期货和期权
    elif exchange in [Exchange.SHFE, Exchange.CFFEX, Exchange.DCE, Exchange.CZCE, Exchange.INE]:
        for count, word in enumerate(symbol):
            if word.isdigit():
                break

        product = symbol[:count]
        time_str = symbol[count:]

        # 期货
        if time_str.isdigit():
            if exchange is not Exchange.CZCE:
                return symbol.upper()

            # 检查是否为连续合约或者指数合约
            if time_str in ["88", "888", "99", "889"]:
                return symbol

            year = symbol[count]
            month = symbol[count + 1:]

            if year == "9":
                year = "1" + year
            else:
                year = "2" + year

            rq_symbol = f"{product}{year}{month}".upper()
        # 期权
        else:
            if exchange in [Exchange.CFFEX, Exchange.DCE, Exchange.SHFE]:
                rq_symbol = symbol.replace("-", "").upper()
            elif exchange == Exchange.CZCE:
                year = symbol[count]
                suffix = symbol[count + 1:]

                if year == "9":
                    year = "1" + year
                else:
                    year = "2" + year

                rq_symbol = f"{product}{year}{suffix}".upper()
    else:
        rq_symbol = f"{symbol}.{exchange.value}"

    return rq_symbol
