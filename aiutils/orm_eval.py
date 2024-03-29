# -*- coding: utf-8 -*-
"""
@time: 2021/11/28 17:10
@file: orm_eval.py

"""

"""
orm对象，重新构造

传入data结构要求如下：
    { "name": table_name,
     "columns": list generated by `column_repr` or `column_arg`
    }

"""
from sqlalchemy import *
from sqlalchemy.dialects.mysql import *


# fixme python eval漏洞
def eval_column_repr(data):  # eval_column_repr方式

    dct = {}
    for k, v in data["columns"]:
        __column = eval(v)
        dct[k] = __column
        __column.name = k
    dct["__tablename__"] = data["name"]
    return dct


def eval_column_arg(data):  # eval_column_arg方式
    dct = {}
    for k, v in data["columns"]:
        __column = Column(**eval(v))
        dct[k] = __column
        __column.name = k
    dct["__tablename__"] = data["name"]
    return dct
