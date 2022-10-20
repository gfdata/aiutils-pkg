# -*- coding: utf-8 -*-
# @time: 2022/1/16 17:32
# @Author：lhf
# ----------------------
import os
import sys
from typing import Optional, Union
from functools import lru_cache

from logbook import Logger
import pandas as pd

from aiutils.singleton import SingletonType


@lru_cache()
def _pd_read_excel(file, file_t):
    # xlrd 1.2.0以下才支持xlsx，2.0不支持；pandas 1.3.0 可用openpyxl引擎
    try:
        import xlrd
        df = pd.read_excel(file, index_col=0, skiprows=1)  # 已经设置了index_col为索引列
    except Exception as e:
        df = pd.read_excel(file, index_col=0, skiprows=1, engine="openpyxl")

    df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
    # 检查
    assert all([x.isupper() for x in df.index]), '品种名称要求：全为大写字母'
    from aiutils.code.unique_const import ExchangeISO
    assert all([x in ExchangeISO.__members__.keys() for x in df['exchange_iso']]), '品种交易所要求：全部在ExchangeISO中'
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])
    return df.sort_index()


class UnderlyingExcel(metaclass=SingletonType):
    def save(self):
        """ excel数据较少，手动更新即可 """
        self.logger.info('excel存储：手动更新即可')

    def __init__(self, file_dir=None):
        """
        :param file_dir: 文件所在目录
        """
        self.logger = Logger(self.__class__.__name__)
        if not file_dir:  # 默认aiutils目录下
            file_dir = os.path.dirname(os.path.dirname(__file__))
            file = os.path.join(file_dir, 'future_classify.xlsx')
        if not os.path.exists(file):
            s = f'所需文件不存在 {file}'
            self.logger.error(s)
            raise RuntimeError(s)
        else:
            self.file = file

    def all_data(self) -> pd.DataFrame:
        return _pd_read_excel(self.file, os.path.getmtime(self.file))

    def all_underlying(self) -> set:
        return set(self.all_data().index)

    def future_classify(self, by='classify_a') -> pd.Series:
        # type: (Optional[str]) -> Union[None,pd.Series]
        """获取期货品种分类
        """
        if not by.startswith('classify_'):
            raise ValueError(f'分类标准的参数by：要求全名，classify_开头 got {by}')
        df = self.all_data()
        if by not in df.columns:
            self.logger.error(f'{sys._getframe().f_code.co_name}没有该列 {by}')
            return None
        return df[by].sort_values()
