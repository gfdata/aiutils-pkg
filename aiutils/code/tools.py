# -*- coding: utf-8 -*-
# @time: 2021/12/24 9:59
# @Author：lhf

from functools import lru_cache
from typing import Tuple


@lru_cache()
def unique_code_head(unique_code: str) -> str:
    """根据合约编码分组
    * symbol纯数字：大于三位取前三；不足三位取全部；
    * symbol字母开头：使用该组字母；
    :param unique_code: 不一定要是本地规则转换之后，只需要symbol在前即可
    :return:
    """
    split = _split_by_iter(unique_code)
    if split[0].isalpha():
        return split[0]
    else:
        temp = split[0]
        if len(temp) > 3:
            return temp[:3]
        else:
            return temp


@lru_cache()
def unique_code_head_old(unique_code: str) -> str:
    """根据合约编码分组
    * symbol纯数字：大于三位取前三；不足三位取全部；
    * symbol字母开头：使用该组字母；
    :param unique_code: 不一定要是本地规则转换之后，只需要symbol在前即可
    :return:
    """
    split = sym_dot_exg_split(unique_code)
    if split[0][0].isalpha():
        return split[0][0]
    else:
        temp = split[0][0]
        if len(temp) > 3:
            return temp[:3]
        else:
            return temp


def sym_dot_exg_split(sym_dot_exg: str) -> Tuple[list, str]:
    """先根据“.”分割，再将symbol进行 数字字母 分割
    :param sym_dot_exg:格式符合 前面symbol 中间dot 后面exchange；本地unique_code就是如此
    :return:
    """
    temp = sym_dot_exg.split(".")  # 期货 期权 exchange为空
    if len(temp) == 1:
        symbol, exchange = temp[0], None
    elif len(temp) == 2:
        symbol, exchange = temp[0], temp[1]
    else:
        raise RuntimeError(f'unique_code编码规则:只能有一个或零个分隔符！ got{sym_dot_exg}')

    if not symbol:
        raise RuntimeError(f'unique_code编码规则:分割后的前半部分不能为空！ got{sym_dot_exg}')

    first = _split_by_iter(symbol)
    return (first, exchange)


def _split_by_re(s: str) -> list:
    import re
    return re.findall(r"[^\W\d_]+|\d+", s)


def _iter_yield(s: str) -> list:
    from itertools import groupby
    for k, g in groupby(s, str.isalpha):
        yield ''.join(g)


def _split_by_iter(s: str):
    return list(_iter_yield(s))
