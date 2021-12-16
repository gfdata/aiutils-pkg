# -*- coding: utf-8 -*-
"""
@time: 2021/11/3 14:12
@file: code_common.py

"""
import six
import warnings
import re
import datetime
from typing import Tuple, List


def unique_by_common(order_book_ids) -> str or List:
    """
    合约格式转换，参考`rqdatac.services.basic.id_convert`
    识别功能有限，针对特定平台的编码方式还需细化规则

    :param order_book_ids: str 或 str list, 如'000001', 'SZ000001', '000001SZ',
        '000001.SZ', 纯数字str默认为股票类型
    :returns: str 或 str list, 米筐格式的合约

    """
    if isinstance(order_book_ids, six.string_types):
        return _id_convert_one(order_book_ids)
    elif isinstance(order_book_ids, list):
        return [_id_convert_one(o) for o in order_book_ids]
    else:
        raise ValueError("order_book_ids should be str or list")


def _id_convert_one(order_book_id):
    try:
        res = __id_convert_one(order_book_id).upper()
    except Exception as e:  # fixme 50期权符合要求的编码，再做转换会识别不了
        res = order_book_id
        warnings.warn(f"转换编码失败，返回原值{order_book_id}, {e}", RuntimeWarning)
    return res


def __id_convert_one(order_book_id):  # noqa: C901
    # hard code
    if order_book_id in {"T00018", "T00018.SH", "T00018.XSHG", "SH.T00018"}:
        return "990018.XSHG"

    if order_book_id.isdigit():
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
        if res[1][0] > year[-1]:
            num = str(int(year[-2]) - 1)
        else:
            num = year[-2]
        return res[0] + num + res[1] + res[2]
    return order_book_id
