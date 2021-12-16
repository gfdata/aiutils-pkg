# -*- coding: utf-8 -*-
"""
@time: 2021/10/19 16:08
@file: list_obj.py

列表对象工具
"""


def split_iter(l, n, as_list=False):
    """ 按照n的步长，切分可迭代对象"""

    def _split_iter(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def _split_list(l, n):
        return list(l[i:i + n] for i in range(0, len(l), n))

    if as_list:
        return _split_list(l, n)
    else:
        return _split_iter(l, n)
