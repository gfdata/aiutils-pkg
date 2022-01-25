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
    df = pd.read_excel(file, index_col=0)  # 已经设置了index_col为索引列
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

    def all_data(self) -> pd.dataFame:
        return _pd_read_excel(self.file, os.path.getmtime(self.file))

    def all_underlying(self) -> set:
        return set(self.all_data().index)

    def future_classify(self, by='classify_0') -> pd.Series:
        # type: (Optional[str]) -> Union[None,pd.Series]
        """获取期货品种分类
        """
        if not by.startswith('classify_'):
            raise ValueError(f'参数by(分类标准) 格式错误')
        df = self.all_data()
        if by not in df.columns:
            self.logger.error(f'{sys._getframe().f_code.co_name}没有该列 {by}')
            return None
        return df[by].sort_values()
