# -*- coding: utf-8 -*-
"""
@time: 2021/11/3 14:12
@file: rq_by_common.py

"""
import six
import warnings
import re
import datetime
from typing import List

from functools import lru_cache

from aiutils.code.tools import sym_dot_exg_split


def unique_by_common(order_book_ids) -> str or List:
    """合约格式转换，
    * 参考`rqdatac.services.basic.id_convert`
    * 功能有限，针对特定平台的编码方式还需细化规则
    :param order_book_ids: str 或 str list, 如'000001', 'SZ000001', '000001SZ','000001.SZ', 纯数字str默认为股票类型
    :returns: str 或 str list, 米筐格式的合约
    """
    # warnings.warn('本方法还有漏洞不能完全识别，请使用 aiutils.code.code_by_common 函数', DeprecationWarning)

    if isinstance(order_book_ids, six.string_types):
        return _id_convert_one(order_book_ids)
    elif isinstance(order_book_ids, list):
        return [_id_convert_one(o) for o in order_book_ids]
    else:
        raise ValueError("order_book_ids should be str or list")


@lru_cache()
def _id_convert_one(order_book_id):
    try:
        # res = __id_convert_one(order_book_id).upper()
        res = _convert_rule(order_book_id).upper()
    except Exception as e:
        res = order_book_id
        warnings.warn(f"转换编码失败，返回原值{order_book_id}, {e}", RuntimeWarning)
    return res


def _rule_XSHG_XSHE(only_symbol):
    """上交所 深交所；只分析前半部分的数字部分
    可能为 金融期权
    """
    symbol = only_symbol
    # hf20211103 上交所和深交所：股票编码6位，期权编码8位，债券编码6位；因此要做区分
    if len(symbol) == 8:
        return symbol  # rq期权不带交易所后缀
    if symbol.startswith("0") or symbol.startswith("3"):
        return symbol + ".XSHE"
    elif (
            symbol.startswith("5")
            or symbol.startswith("6")
            or symbol.startswith("9")
            or symbol.startswith("15")
    ):
        return symbol + ".XSHG"
    else:
        raise ValueError("should be str like 000001, 600000")


def _convert_rule(code_replaced_by_dot):
    """ 从此处分流具体类型
    与交易所(如有)的分隔符都替换为'.'之后，再处理
    """
    order_book_id = code_replaced_by_dot
    # 纯数字编码
    if order_book_id.isdigit():
        return _rule_XSHG_XSHE(order_book_id)
    # 带有证券交易所字符串
    order_book_id = order_book_id.upper()
    if order_book_id.endswith(".XSHG") or order_book_id.endswith(".XSHE"):
        rq_symbol = order_book_id.split('.')[0]
        # hf20211103 上交所和深交所：股票编码6位，期权编码8位，债券编码6位；因此要做区分
        if len(rq_symbol) == 8:  # rq期权不带交易所后缀
            return rq_symbol
        return order_book_id

    if order_book_id.startswith("SZ"):
        return order_book_id.replace(".", "")[2:] + ".XSHE"
    elif order_book_id.startswith("SH"):
        return order_book_id.replace(".", "")[2:] + ".XSHG"
    elif order_book_id.endswith("SZ"):
        return order_book_id.replace(".", "")[:-2] + ".XSHE"
    elif order_book_id.endswith("SH"):
        return order_book_id.replace(".", "")[:-2] + ".XSHG"

    if any([order_book_id.endswith(x) for x in ['.INDX']]):
        return order_book_id

    # 商品期货 期权
    return _rule_commodity(order_book_id)


def _rule_commodity(code_replaced_by_dot):
    """ 商品期货 期权
    """
    # 替换分隔符
    temp = code_replaced_by_dot.replace("-", "").split(".")
    if len(temp) >= 2 and temp[-1] in ['SGEX']:
        raise ValueError(f'不是期货交易所品种 {code_replaced_by_dot}')
    order_book_id = code_replaced_by_dot.replace("-", "").split(".")[0]
    try:
        # res = re.findall(r"^([A-Z]+)(\d+)([PC]\w+)?", order_book_id)[0]
        res, exg = sym_dot_exg_split(code_replaced_by_dot)
    except IndexError:
        raise ValueError("unknown order_book_id: {}".format(order_book_id))
    if len(res[0]) > 2:
        raise ValueError("品种字母不符合: {}".format(order_book_id))

    # 期货相关的指数
    if len(res) != 2 and res[1] in ['88', '888', '8888', '99', '9999', '889']:
        return ''.join(res) + exg
    # 年月是否符合
    if len(res[1]) <= 2:
        _y, _m = '', res[1]
    else:
        temp = len(res[1])
        _y, _m = res[1][:temp - 2], res[1][-2:]
    if not _m:
        raise ValueError("年月部分不符合: {}".format(order_book_id))
    if int(_m) < 1 or int(_m) > 12:
        raise ValueError("年月部分不符合: {}".format(order_book_id))

    # 年份补充
    if len(res[1]) == 3:
        year = str(datetime.datetime.now().year + 3)
        if res[1][0] > year[-1]:
            num = str(int(year[-2]) - 1)
        else:
            num = year[-2]
        res[1] = num + res[1]
        return ''.join(res)
    else:
        return ''.join(res)


def __id_convert_one(order_book_id):  # noqa: C901
    # hard code
    if order_book_id in {"T00018", "T00018.SH", "T00018.XSHG", "SH.T00018"}:
        return "990018.XSHG"

    if order_book_id.isdigit():
        if len(order_book_id) == 8:  # hf20211223 证券交易所的期权，纯数字8位
            return order_book_id
        if order_book_id.startswith("0") or order_book_id.startswith("3"):
            return order_book_id + ".XSHE"
        elif (
                order_book_id.startswith("5")
                or order_book_id.startswith("6")
                or order_book_id.startswith("9")
                or order_book_id.startswith("15")
        ):
            return order_book_id + ".XSHG"
        else:
            raise ValueError("order_book_ids should be str like 000001, 600000")

    order_book_id = order_book_id.upper()
    if order_book_id.endswith(".XSHG") or order_book_id.endswith(".XSHE"):
        rq_symbol = order_book_id.split('.')[0]
        # hf20211103 上交所和深交所：股票编码6位，期权编码8位，债券编码6位；因此要做区分
        if len(rq_symbol) == 8:  # rq期权不带交易所后缀
            return rq_symbol
        return order_book_id

    if order_book_id.startswith("SZ"):
        return order_book_id.replace(".", "")[2:] + ".XSHE"
    elif order_book_id.startswith("SH"):
        return order_book_id.replace(".", "")[2:] + ".XSHG"
    elif order_book_id.endswith("SZ"):
        return order_book_id.replace(".", "")[:-2] + ".XSHE"
    elif order_book_id.endswith("SH"):
        return order_book_id.replace(".", "")[:-2] + ".XSHG"

    # 期货
    order_book_id = order_book_id.replace("-", "").split(".")[0]
    try:
        res = re.findall(r"^([A-Z]+)(\d+)([PC]\w+)?", order_book_id)[0]
    except IndexError:
        raise ValueError("unknown order_book_id: {}".format(order_book_id))
    if len(res[1]) == 3 and res[1] != '888':
        year = str(datetime.datetime.now().year + 3)
        # # hf20211223: rqdatac 2.9.42 处理方式
        # # 按照当前年份+3之后的年份取十位位置上数字递减重新组合为 order_book_id列表 去查询 trading_code 相等的最大合约(即返回结果 trading_code 相等的首个合约)
        # # bug：当 year[-2] = 0(2097年)，若(设输入为'TA312')没有查到此 order_book_id('TA0312')， 则不会对三位代码补位而直接返回原 trading_code('TA312')
        # ins_infos = instruments([res[0] + str(n) + res[1] + res[2] for n in range(int(year[-2]), -1, -1)])
        # for ins_info in ins_infos:
        #     if ins_info is None:
        #         continue
        #     trading_code = getattr(ins_info, "trading_code", "")
        #     if trading_code.upper() == order_book_id.upper():
        #         return ins_info.order_book_id

        # 原来的处理方式
        if res[1][0] > year[-1]:
            num = str(int(year[-2]) - 1)
        else:
            num = year[-2]
        return res[0] + num + res[1] + res[2]
    return order_book_id
