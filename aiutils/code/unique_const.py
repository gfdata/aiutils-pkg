# -*- coding: utf-8 -*-
# @time: 2022/2/9 9:05
# @Author：lhf
# ----------------------
from enum import Enum


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
