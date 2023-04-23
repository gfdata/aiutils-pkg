# -*- coding: utf-8 -*-
# @time: 2022/1/16 17:32
# @Author：lhf
# ----------------------
import os
from pathlib import Path
from typing import Optional, Union
from functools import lru_cache

from logbook import Logger
import pandas as pd

from aiutils.code.exchange_iso import ExchangeISO
from aiutils.singleton import SingletonType


@lru_cache()
def _pd_read_excel(file, file_t):  # file_t参数，只为了方便cache识别
    # xlrd 1.2.0以下才支持xlsx，2.0不支持；pandas 1.3.0 可用openpyxl引擎
    try:
        import xlrd
        df = pd.read_excel(file, index_col=0, skiprows=1)  # 已经设置了index_col为索引列
    except Exception as e:
        df = pd.read_excel(file, index_col=0, skiprows=1, engine="openpyxl")

    df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
    # 检查，表格数据要满足exchange_iso，否则需要修改excel文件
    assert all([x.isupper() for x in df.index]), '品种名称要求：全为大写字母'
    assert all([x in ExchangeISO.__members__.keys() for x in df['exchange_iso']]), '品种交易所要求：符合ExchangeISO规范'
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])
    return df.sort_index()


class _FutureClassify(metaclass=SingletonType):
    def save(self):
        """ excel数据较少，手动更新即可 """
        self.logger.info('excel存储：手动更新即可')

    def __init__(self, file_dir=None, file_name='future_classify.xlsx'):
        """
        :param file_dir: 文件所在目录，默认使用 aiutils包目录下的；文件名
        """
        self.logger = Logger(self.__class__.__name__)
        if not file_dir:
            file = Path(__file__).parent.parent.joinpath(file_name)
        else:
            file = Path(file_dir).joinpath(file_name)
        if not file.exists():
            raise FileNotFoundError(f'所需文件不存在 {file}')
        else:
            self.file = file

    def all_data(self) -> pd.DataFrame:
        """ 读取所有品种数据，index为品种字母 """
        return _pd_read_excel(self.file, os.path.getmtime(self.file))

    def all_underlying(self) -> set:
        """ 获取所有品种的字母 """
        return set(self.all_data().index)

    def get(self, by='classify_a'):
        # type: (Optional[str]) -> Union[None,pd.Series]
        """
        获取品种的分类规则，详见 future_classify.xlsx表格列名
        :param by: 分类标准，也就是excel中的列名称
        :return:
        """
        if not by.startswith('classify_'):
            raise ValueError(f'分类标准的参数by要求：classify_开头 got {by}')
        df = self.all_data()
        if by not in df.columns:
            self.logger.error(f'没有该列 {by}')
            return None
        return df[by].sort_values()


FutureClassify = _FutureClassify()
