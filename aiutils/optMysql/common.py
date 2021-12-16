# -*- coding: utf-8 -*-
"""
@time: 2021/11/28 17:06
@file: common.py

"""
import pandas as pd
from logbook import Logger
from sqlalchemy.engine import Engine

from aiutils.singleton import SingletonType
from aiutils.sql_session import rows_2_list_dict, rows_2_df
from aiutils.orm_str import column_repr as _column_dumps  # eval_column_repr 写法

from .engine import StoreMysqlEngine


class ByMysql(metaclass=SingletonType):
    OUTPUT = ['list_dict', 'proxy', 'df']

    def __init__(self, *args, **kwargs):
        self.logger = Logger(self.__class__.__name__)
        self.logger.debug(f'单例模式 初始化')

    def get_engine(self, db: str) -> Engine:
        """ 获取数据库的engine，没有则添加到self.engine_dic"""
        return StoreMysqlEngine().get(db)

    def set_engine(self, db: str) -> Engine:
        return StoreMysqlEngine().set(db)

    def run_sql(self, db: str, sql: str, output='list_dict'):
        """
        执行sql语句之后，直接fetchall()获取全部查询结果。输出结果:
        - `list_dict`：默认，逐行组成List，Dict为各行数据的`字段名：字段值`映射
        - `proxy`：rowproxy对象组成的list
        - `df`: pd.DataFrame
        - `dict_col`：k为字段名，v为有序list，该行无值时补充None
        :return:
        """
        assert output in self.OUTPUT
        # 查询直接用engine.execute()和connection.execute()，不需要session事务
        engine = self.get_engine(db)
        with engine.connect() as conn:
            res = conn.execute(sql).fetchall()

        if output == 'list_dict':
            return rows_2_list_dict(res)
        elif output == 'proxy':
            return res
        elif output == 'df':
            return rows_2_df(res)
        else:
            raise ValueError(output, '未实现')

    def get_table_orm(self, db: str, table_name: str = ''):
        """
        table_name为空：返回数据库下面的表名，list[表名...]
        table_name不为空：返回表的结构能够用于传输用于创建Model
        使用`column_repr`时返回结果如下
        {
            'name': 'STK_FIN_FORCAST',
            'columns': [
                        ('id', "Column('id', Integer, primary_key=True)"),
                        ('company_id', "Column('company_id', Integer)")
                        ]
        }
        :param db:
        :param table_name:
        :return:
        """
        engine = self.get_engine(db)
        # 不含table_name参数
        if not table_name.strip():
            return engine.table_names()

        # 含有table_name参数
        res = dict()
        res["name"] = table_name
        res["columns"] = _column_dumps(table_name, engine)
        return res
