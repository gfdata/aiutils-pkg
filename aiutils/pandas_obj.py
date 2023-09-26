# -*- coding: utf-8 -*-
"""
@time: 2021/11/28 17:15
@file: pandas_obj.py

pandas相关的处理函数
"""

import datetime
import pandas as pd

from typing import Iterable


def df_col_dt_like(df: pd.DataFrame, col_name) -> bool:
    """ df数据列，是否为时间类型 """
    assert col_name in df.columns
    if hasattr(df[col_name], 'dt'):
        return True
    elif hasattr(df[col_name], "to_pydatetime"):
        return True
    elif df[col_name].dtype.name == 'object':  # 很多情况下，时间列未作转化时，dtype为object
        se = df[col_name].dropna()
        if se.empty:
            return False
        else:
            # temp = se.max() # 混合数据时有异常 TypeError: '>=' not supported between instances of 'float' and 'str'
            temp = [se.iloc[0], se.iloc[int(len(se) / 2)], se.iloc[-1], ]  # 列举几个进行检查
            for i in list(range(1, 10)):
                try:
                    temp.append(se.iloc[i])
                    temp.append(se.iloc[-i])
                except:
                    pass
            b = [isinstance(x, datetime.datetime) or isinstance(x, datetime.date) for x in temp]
            if all(b) is True:
                return True

        # 遇到NAT这种判断有问题
        # for x in df[col_name]:
        #     if isinstance(x, datetime.datetime) or isinstance(x, datetime.date):
        #         print(x)
        #         return True

        # # 列举几个进行检查
        # temp = df[col_name].iloc[0]
        # if isinstance(temp, datetime.datetime) or isinstance(temp, datetime.date):
        #     return True
        # temp = df[col_name].iloc[int(len(df) / 2)]
        # if isinstance(temp, datetime.datetime) or isinstance(temp, datetime.date):
        #     return True
        # temp = df[col_name].iloc[-1]
        # if isinstance(temp, datetime.datetime) or isinstance(temp, datetime.date):
        #     return True

    # 否则返回False
    return False


# 注意格式一定要` .%f ` 表示微秒-->因为其它的格式mysql识别不了，比如'%Y-%m-%d %H:%M:%S:%f'识别不了:%f，就会丢失微秒
# 毫秒精度之外会做四舍五入-->例如mysql字段类型为DATETIME(3)只存三位，而传入.%f有六位时
_DT_FORMAT_F = '%Y-%m-%d %H:%M:%S.%f'
_DT_FORMAT_S = '%Y-%m-%d %H:%M:%S'
_DT_FORMAT_D = '%Y-%m-%d'


def df_to_dict(df: pd.DataFrame, dt_columns: list = None, dt_format: str = _DT_FORMAT_F):
    """
    将 DataFrame 数据按records转化，便于进行批量插入

    * 此函数作为DataFrame的通用处理方式，也可用于其它数据库插入前的整理

    * 时间格式
        * 处理为str格式-->原因：可能报错pymysql: AttributeError: 'Timestamp' object has no attribute 'translate'
        * 可以不传，此时会根据DataFrame的列特性找出dt_columns

    * 空值，必须替换为None-->原因：返回的df_dic_list用于sql拼接参数时，其它的null类型不一定能准确识别

    """
    if df is None or df.empty or df.shape[0] == 0:
        return []

    # 补全dt_format
    if dt_format is None or dt_format.strip() == '':
        dt_format = _DT_FORMAT_F

    # 记录dt_columns
    if not dt_columns:
        dt_columns = []
    elif isinstance(dt_columns, Iterable):
        dt_columns = [x for x in dt_columns]

    for x in df.columns:  # 加上df自身的dt属性列
        if df_col_dt_like(df, x):
            dt_columns.append(x)
    dt_columns = list(set(dt_columns) & set(df.columns))

    # 空值替换会将dtype改为object，所以放在dtype记录之后再执行
    df = df.astype('object').where(pd.notnull(df), None)
    _null = df.isnull()
    if dt_columns:
        for field in dt_columns:
            df[field] = df[field].apply(lambda x: x.strftime(dt_format) if x else None)
            # df[field] = df[field].dt.strftime(dt_format)  # fix-->前面NaT转None，此处再strftime又会变成字符串的NaT
    df = df.astype('object').where(~_null, None)  # 所以使用_null记录位置，替换回来为None
    df_dic_list = df.to_dict('records')
    col_name_list = list(df.columns)
    return df_dic_list, col_name_list
