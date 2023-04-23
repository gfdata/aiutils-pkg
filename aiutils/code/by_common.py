# -*- coding: utf-8 -*-
# @time: 2021/12/24 10:00
# @Author：lhf

import warnings
import datetime
from typing import Dict

from aiutils.cache import MemoryCache
from aiutils.code.exchange_iso import ExchangeISO
from aiutils.code.exchange_map import exchange_ud, exchange_wind, exchange_vnpy, MapTotal
from aiutils.code.tools import _split_by_iter, sym_dot_exg_split


def code_by_common(api_code: str, api_exchange_map: Dict[str, ExchangeISO] = {}, error_raise=False) -> str:
    """合约编码，转换为标准ISO格式
    :param api_code: 如果含有symbol和exchange，需要先处理为dot分割符
    :param api_exchange_map: 可以传入临时定义的交易所映射 str:ExchangeIso
    :param error_raise: 转换失败是否抛出异常
    :return:
    """
    try:
        res = _code_by_common(api_code, api_exchange_map)
        return res.upper()
    except Exception as e:
        msg = f"转换编码失败返回原值{api_code} : {e}"
        if error_raise:
            raise RuntimeError(msg)
        else:
            warnings.warn(msg, RuntimeWarning)
            return api_code


# @lru_cache() # 不支持参数中含有dict 做缓存
@MemoryCache.cached_function_result_for_a_time(cache_mb=1024, cache_second=3600 * 12)
def _code_by_common(api_code: str, api_exchange_map: Dict[str, ExchangeISO] = {}) -> str:
    if '.' not in api_code:
        return _no_dot(api_code)
    else:
        return _with_dot(api_code, api_exchange_map)


def _no_dot(api_code) -> str:
    """ 编码中没有dot分割符，需要推断exchange """
    assert '.' not in api_code, f'处理的是不含dot的情况'
    if api_code.isdigit():  # 纯数字，默认是证券交易所的股票 金融期权
        return _security_digit(api_code)
    elif api_code.startswith('SZ'):  # 证券可能直接连着写在一起，例如SH000001 SZ000001
        return api_code.replace(".", "")[2:] + ".XSHE"
    elif api_code.startswith("SH"):
        return api_code.replace(".", "")[2:] + ".XSHG"
    else:
        temp = _split_by_iter(api_code)
        if temp[0].isdigit():  # 分割后第一部分是数字，例如510050C1612M02050
            target = _security_digit(temp[0])
            obj = ExchangeISO[target.split('.')[-1]]
            return api_code + '.' + obj.value
        else:  # 分割后第一部分是字母，例如 商品期货 商品期权，以及特殊的IOxxxx(深交所)
            try:
                obj = exchange_ud()[temp[0].upper()]
            except Exception as e:
                raise ValueError(f'未找到交易所映射 {api_code}')
            else:
                return _commodity_future_option(api_code, obj)


def _with_dot(api_code, api_exchange_map: Dict[str, ExchangeISO] = {}):
    """ 编码中有分割符，需要转换exchange为ISO """
    assert '.' in api_code, f'处理的是含有dot的情况'
    map_total = MapTotal().update(exchange_wind()).update(exchange_vnpy())
    map_total.update(api_exchange_map)

    one, two = api_code.split('.')
    if one in map_total.keys():  # exg放在前面的情况
        sym_dot_exg = two + '.' + one
    else:
        sym_dot_exg = api_code
    # 查找exchangeISO
    sym, exg = sym_dot_exg.split('.')
    try:
        obj = map_total[exg]
    except Exception as e:
        raise ValueError(f'未找到交易所映射 {api_code}')
    # 商品期货 期权；检查调整
    if obj in [ExchangeISO.XSGE, ExchangeISO.XDCE, ExchangeISO.XZCE, ExchangeISO.XINE]:
        return _commodity_future_option(sym_dot_exg, obj)
    return sym + '.' + obj.value


# ------------------------------------------------------------------------------------------------------------
def _security_digit(sym_digit: str) -> str:
    """纯数字的证券，为其后面添加.ExchangeISO的字母
    例如：股票编码6位，期权编码8位，债券编码6位
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


def _commodity_future_option(sym: str, obj: ExchangeISO) -> str:
    """ 商品期货 商品期权 """
    # 替换分隔符
    order_book_id = sym.replace("-", "").split(".")[0]  # 前半部分
    try:
        res, exg = sym_dot_exg_split(order_book_id)
    except IndexError:
        raise ValueError(f"无法识别品种 {order_book_id}")
    if len(res[0]) > 2:
        raise ValueError(f"品种字母长度超过两位 {order_book_id}")
    # 期货相关的指数  # todo 可以继续完善
    if res[1] in ['00', '88', '888', '8888', '99', '9999', '889', '000']:
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
