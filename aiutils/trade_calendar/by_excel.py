# -*- coding: utf-8 -*-
# @time: 2023/6/28 15:02
# @Author：lhf
# ----------------------
from functools import lru_cache
import pandas as pd

from aiutils.code.exchange_iso import ExchangeISO


@lru_cache()
def _pd_read_excel(file, file_t):  # file_t参数，只为了方便cache识别
    # xlrd 1.2.0以下才支持xlsx，2.0不支持；pandas 1.3.0 可用openpyxl引擎


    try:
        import xlrd
        df = pd.read_excel(file, index_col=None, skiprows=8)
    except Exception as e:
        df = pd.read_excel(file, index_col=None, skiprows=1, engine="openpyxl")

    df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
    # 检查，表格数据要满足exchange_iso，否则需要修改excel文件
    assert all([x.isupper() for x in df.index]), '品种名称要求：全为大写字母'
    assert all([x in ExchangeISO.__members__.keys() for x in df['exchange_iso']]), '品种交易所要求：符合ExchangeISO规范'
    df['list_start'] = pd.to_datetime(df['list_start'])
    df['list_end'] = pd.to_datetime(df['list_end'])
    return df.sort_index()


if __name__ == '__main__':
    _pd_read_excel('../')