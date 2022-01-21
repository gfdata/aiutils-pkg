# -*- coding: utf-8 -*-
# @time: 2022/1/19 16:44
# @Author：lhf
# ----------------------
import re
from importlib import import_module
from typing import Callable


def callable_append(to: dict, lib: str, include: list = [], exclude: list = ['^_', '^__']):
    """
    将lib下面的可执行方法，绑定到字典中
    :param to:
    :param lib:
    :param include: 要求为 全匹配
    :param exclude: 要求为 re.search 正则匹配
    :return:
    """
    if isinstance(lib, str):
        m = import_module(lib)
        name = lib
    else:
        m = lib
        name = lib.__name__
    for k, v in m.__dict__.items():
        if not isinstance(v, Callable):
            continue
        if k in include:
            to[(name, k)] = v
            continue
        if any([re.search(x, k) for x in exclude]):
            continue
        # 最后加进去的
        to[(name, k)] = v
    return to
