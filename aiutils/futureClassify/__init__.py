# -*- coding: utf-8 -*-
# @time: 2022/1/16 17:30
# @Author：lhf
# ----------------------
__doc__ = """
期货品种的合约字母、上市退市时间、品种分类；
包括已退市品种，已改名的品种；
有品种上市退市时，需要手动更新文件；

"""

from .by_excel import UnderlyingExcel

OBJ = UnderlyingExcel()


def all_data():
    """ 获取所有数据 """
    return OBJ.all_data()


def all_underlying():
    """ 获取所有品种的缩写字母 """
    return OBJ.all_underlying()


def get(by='classify_a'):
    """
    获取品种的分类规则，详见 future_classify.xlsx表格列名
    """
    return OBJ.future_classify(by)
