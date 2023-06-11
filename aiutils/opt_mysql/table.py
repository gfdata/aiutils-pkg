# -*- coding: utf-8 -*-
"""
@time: 2021/11/28 17:06
@file: table.py

从数据库得到表结构

"""

from sqlalchemy.ext.declarative import declarative_base

from aiutils.cache import ttl_cache
from aiutils.sql_retrieve import compile_query, check_no_join
from aiutils.orm_eval import eval_column_repr as _eval_column  # eval_column_repr 写法

from aiutils.opt_mysql.config import AIUTILS_MYSQL_CONFIG
from aiutils.opt_mysql.common import ByMysql


def _get_session():
    from sqlalchemy.orm import scoped_session, sessionmaker
    session = scoped_session(sessionmaker())
    return session


session = _get_session()


def query(*args, **kwargs):
    """
    接收参数得到sqlalchemy当前环境下的query对象
    :param args:
    :param kwargs:
    :return:
    """
    return session.query(*args, **kwargs)


# 表结构---------------------------------------------------------------------------------------------
@ttl_cache(60 * 60 * 12)
class DBTable(object):
    RESULT_ROWS_LIMIT = AIUTILS_MYSQL_CONFIG.attrs.query_limit

    def __init__(self, db, disable_join=False):
        """ 动态生成数据库表格的对象，适用于单表query。"""
        self.__disable_join = True
        self.__table_names = []
        self.db_name = db

    def __load_table_names(self):
        self.__table_names = ByMysql().get_table_orm(self.db_name)
        for name in self.__table_names:
            setattr(self, name, None)

    def run_query(self, query_object, output='df'):
        """
        :param query_object:
        :param output: output 参数与ByMysql中对应
        :return:
        """
        if self.__disable_join:
            check_no_join(query_object)

        limit = self.RESULT_ROWS_LIMIT
        if query_object._limit:
            limit = min(limit, query_object._limit)
        query_object = query_object.limit(limit)

        sql = compile_query(query_object)

        # 整理输出格式 统一获取`list_dict`格式之后，在此次按需转换
        data = ByMysql().run_sql(db=self.db_name, sql=sql, output=output)
        return data

    def __load_table_class(self, table_name):
        data = ByMysql().get_table_orm(db=self.db_name, table_name=table_name)
        dct = _eval_column(data)
        return type(data["name"], (declarative_base(),), dct)

    def __getattr__(self, key):
        # 如果没有预先加载了table名字, 加载它
        if not self.__table_names:
            self.__load_table_names()
        # 只对table的名字调用getattr, 否则会无限递归
        if key in self.__table_names:
            return getattr(self, key)
        else:
            raise AttributeError("database %r has no table %r" % (self.db_name, key))

    def __getattribute__(self, key):
        v = object.__getattribute__(self, key)
        if v is None:
            if key in self.__table_names:
                v = self.__load_table_class(key)
                setattr(self, key, v)
        return v
