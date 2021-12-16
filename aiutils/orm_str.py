# -*- coding: utf-8 -*-
"""
@time: 2021/11/28 17:09
@file: orm_str.py
orm对象，字符串化；便于传输，之后再eval创建对象
"""

from sqlalchemy import Column
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.ext.declarative import declarative_base


# eval_column_repr方式---------------------------------------------------------------------------------------
def column_repr(table_name, engine) -> list:
    """
    表格字段的repr， 便于通过eval()创建Column对象
    :param table_name:
    :param engine:
    :return: like [ ('id', "Column('id', Integer, primary_key=True)"),('company_id', "Column('company_id', Integer)") ]
    """
    Base = declarative_base()
    Base.metadata.reflect(engine)
    table = Base.metadata.tables[table_name]
    res = []
    for each in table.columns:
        res.append((str(each.name), _column__repr(each)))
    return res


def _column__repr(self: Column):
    """ Column字符化用于eval执行，去掉table属性。[参考Column.__repr__]"""
    kwarg = []
    if self.key != self.name:
        kwarg.append("key")
    if self.primary_key:
        kwarg.append("primary_key")
    if not self.nullable:
        kwarg.append("nullable")
    if self.onupdate:
        kwarg.append("onupdate")
    if self.default:
        kwarg.append("default")
    if self.server_default:
        kwarg.append("server_default")
    if self.comment:
        kwarg.append("comment")
    return "Column(%s)" % ", ".join(
        [repr(self.name)]
        + [repr(self.type)]
        + [repr(x) for x in self.foreign_keys if x is not None]
        + [repr(x) for x in self.constraints]
        # + [
        #     (
        #         self.table is not None
        #         and "table=<%s>" % self.table.description
        #         or "table=None"
        #     )
        # ]
        + ["%s=%s" % (k, repr(getattr(self, k))) for k in kwarg]
    )


# eval_column_arg方式---------------------------------------------------------------------------------------
def column_arg(table_name, engine) -> list:
    """
    sqlalchemy.engine.reflection.Inspector获取表格字段的参数
    1、修改了"type"为"type_"，可用于sqlalchemy.Columns(**v)创建字段对象。
    2、将结果保存为str便于传输，可用eval()函数执行得到原始结构。
    :param table_name:
    :param engine:
    :return: like [('order_book_id', "{'name': 'order_book_id', 'default': None, 'comment': None, 'nullable': False, 'type_': VARCHAR(length=12)}"),]
    """
    insp = Inspector.from_engine(engine)
    result = insp.get_columns(table_name)  # 只有 name type nullable default [attrs可选 如comment]

    # fixme用于映射表格时[ hfdata.hfdb.table.DBTable#__load_table_class ]
    # 报错sqlalchemy.exc.ArgumentError: could not assemble any primary key columns-->添加each['primary_key']解决
    constrained_columns = insp.get_pk_constraint(table_name).get('constrained_columns')
    for each in result:
        if each['name'] in constrained_columns:
            each['primary_key'] = True
        if "type" in each.keys():
            each['type_'] = each.pop("type")

    return [(x.get('name', table_name), str(x)) for x in result]
