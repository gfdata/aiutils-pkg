# -*- coding: utf-8 -*-
"""
@time: 2021/11/28 18:42
@file: sql_retrieve.py

"""
"""
用于sql查询的函数

"""
import re
import six
from functools import wraps


# compile--------------------------------------------------------------------------------------
def no_sa_warnings(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        import warnings
        from sqlalchemy import exc as sa_exc
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=sa_exc.SAWarning)
            return f(*args, **kwds)
    return wrapper


@no_sa_warnings
def check_no_join(query):
    """ 确保 query 中没有 join 语句, 也就是说: 没有引用多个表 """
    tables = get_tables_from_sql(str(query.statement))
    if len(tables) != 1:
        raise Exception("only a table is allowed to query every time")


def get_tables_from_sql(sql):
    """ 从 sql 语句中拿到所有引用的表名字 """
    # m = re.search(r'FROM (.*?)($| WHERE| GROUP| HAVING| ORDER)', sql, flags=re.M)
    # return [t.strip() for t in m.group(1).strip().split(',')] if m else []
    m = re.findall(r'FROM (.*?)($| WHERE| GROUP| HAVING| ORDER)', sql, flags=re.M)
    return [x[0].strip("`").strip() for x in m] if m else []


def compile_query(query):
    """ 把一个 sqlalchemy query object 编译成mysql风格的 sql 语句 """
    from sqlalchemy.sql import compiler
    from sqlalchemy.dialects import mysql as mysql_dialetct
    from pymysql.converters import conversions, escape_item, encoders

    dialect = mysql_dialetct.dialect()
    statement = query.statement
    comp = compiler.SQLCompiler(dialect, statement)
    comp.compile()
    enc = dialect.encoding
    comp_params = comp.params
    params = []
    for k in comp.positiontup:
        v = comp_params[k]
        if six.PY2 and isinstance(v, six.string_types) and not isinstance(v, six.text_type):
            v = v.decode("utf8")
        v = escape_item(v, conversions, encoders)
        params.append(v)
    return (comp.string % tuple(params))
