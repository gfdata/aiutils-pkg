"""

"""
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session


class SessionWrapper:
    """用于对session对象进行封装，方便使用with语句进行控制"""

    def __init__(self, session):
        self.session = session

    def __enter__(self) -> Session:
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


def with_db_session(engine, expire_on_commit=True):
    """创建session对象，返回 session_wrapper 可以使用with语句进行调用"""
    db_session = sessionmaker(bind=engine, expire_on_commit=expire_on_commit)
    session = db_session()
    return SessionWrapper(session)


def get_db_session(engine, expire_on_commit=True):
    """返回 session 对象"""
    db_session = sessionmaker(bind=engine, expire_on_commit=expire_on_commit)
    session = db_session()
    return session


# 查询结果转换-------------------------------------------------------------------------------
def rows_2_df(rp_list):
    """
    :param rp_list: query.fetchall()得到的rowproxy 一组 list
    :return:
    """
    def func(rp):
        for x in rp:
            yield dict(zip(x.keys(), x))

    return pd.DataFrame(func(rp_list))  # 没有数据时返回空的DataFrame


def rows_2_list_dict(rp_list):
    """
    :param rp_list:query.fetchall()得到的rowproxy 一组 list ;元素为None的过滤掉了
    :return:
    """
    result = []
    for each in rp_list:
        result.append({x[0]: x[1] for x in each.items() if x[1] is not None})
    return result
