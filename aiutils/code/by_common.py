# -*- coding: utf-8 -*-
# @time: 2021/12/24 10:00
# @Author：lhf

import warnings
from functools import lru_cache
from typing import Tuple

import datetime
from aiutils.cache import MemoryCache
from .tools import _split_by_iter, sym_dot_exg_split
from .unique_exchange import ExchangeMap, Exchange, UD_EXCHANGE


def code_by_common(api_code: str, api_exchange: str = '', exchange_map=ExchangeMap.data, error_raise=False) -> str:
    """
    :param api_code: 分隔符为dot(如果有的话)
    :param api_exchange:
    :param exchange_map:
    :param error_raise:
    :return:
    """
    try:
        res = _code_by_common(api_code, api_exchange, exchange_map)
        return res.upper()
    except Exception as e:
        msg = f"转换编码失败，返回原值 {api_code} :{e}"
        if error_raise:
            raise RuntimeError(msg)
        else:
            warnings.warn(msg, RuntimeWarning)
            return api_code


# @lru_cache() # 不支持参数中含有dict 做缓存
# @MemoryCache.cached_function_result_for_a_time(cache_mb=1024, cache_second=3600 * 12)
def _code_by_common(api_code: str, api_exchange: str = '', exchange_map: dict = ExchangeMap.data) -> str:
    # 没法获取exchange
    if ('.' not in api_code) and (not api_exchange):
        if api_code.isdigit():  # 纯数字，默认是证券交易所的股票 金融期权
            return _security_digit(api_code)
        elif api_code.startswith('SZ'):
            return api_code.replace(".", "")[2:] + ".XSHE"
        elif api_code.startswith("SH"):
            return api_code.replace(".", "")[2:] + ".XSHG"
        else:
            temp = _split_by_iter(api_code)
            if temp[0].isdigit():  # 用简称表示的510050C1612M02050
                target = _security_digit(temp[0])
                obj = exchange_map[target.split('.')[-1]]
                return api_code + '.' + obj.value
            else:  # 混合，默认是商品期货 商品期权； # 特殊的IOxxxx(深交所)
                try:
                    obj = exchange_map[UD_EXCHANGE[temp[0]]]
                except Exception as e:
                    raise ValueError(f'未找到交易所映射 {api_code}')
                else:
                    return _commodity_future_option(api_code, obj)

    # 可以获取exchange信息；整理成规范的格式
    if ('.' not in api_code) and api_exchange:
        sym_dot_exg = api_code + '.' + api_exchange

    if '.' in api_code and not api_exchange:
        if any([api_code.startswith(x + '.') for x in exchange_map.keys()]):
            exg, sym = api_code.split('.')
            sym_dot_exg = sym + '.' + exg
        else:
            sym_dot_exg = api_code
    if '.' in api_code and api_exchange:
        sym_dot_exg = api_code.split('.')[0] + '.' + api_exchange

    # 查找exchange
    sym, exg = sym_dot_exg.split('.')
    try:
        obj = exchange_map[exg]
    except Exception as e:
        raise ValueError(f'未找到交易所映射 {api_code}')

    # 商品期货 期权；检查调整
    if obj in [Exchange.XSGE, Exchange.XDCE, Exchange.XZCE, Exchange.XINE]:
        return _commodity_future_option(sym_dot_exg, obj)

    # 最后其他
    return sym + '.' + obj.value


def _security_digit(sym_digit: str) -> str:
    """纯数字的证券
    可能是 股票编码6位，期权编码8位，债券编码6位
    """
    assert sym_digit.isdigit(), f'此处只处理纯数字类型的 got {sym_digit}'
    symbol = sym_digit
    if (
            symbol.startswith("0")
            or symbol.startswith("3")
            or symbol.startswith('159')
            or symbol.startswith('184')  # 封闭式基金
    ):
        return symbol + ".XSHE"
    elif (
            symbol.startswith("5")  # 基金
            or symbol.startswith("6")
            or symbol.startswith("9")
            or symbol.startswith("15")
            or symbol.startswith('1000')  # 50etf期权 300etf期权
    ):
        return symbol + ".XSHG"
    else:
        raise ValueError("纯数字类型的编码无法识别")


def _commodity_future_option(sym: str, obj: Exchange) -> str:
    """ 商品期货 商品期权 """
    # 替换分隔符
    order_book_id = sym.replace("-", "").split(".")[0]  # 前半部分
    try:
        res, exg = sym_dot_exg_split(order_book_id)
    except IndexError:
        raise ValueError(f"无法识别品种 {order_book_id}")
    if len(res[0]) > 2:
        raise ValueError(f"品种字母长度不符 {order_book_id}")
    # 期货相关的指数
    if res[1] in ['00', '88', '888', '8888', '99', '9999', '889']:  # 可以继续完善
        return ''.join(res) + '.' + obj.value
    # 年份补全
    if len(res[1]) == 3:
        year = str(datetime.datetime.now().year + 3)
        if res[1][0] > year[-1]:
            num = str(int(year[-2]) - 1)
        else:
            num = year[-2]
        res[1] = num + res[1]
        return ''.join(res) + '.' + obj.value
    else:
        return ''.join(res) + '.' + obj.value
