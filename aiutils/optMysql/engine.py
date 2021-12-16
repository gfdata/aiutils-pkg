# -*- coding: utf-8 -*-
"""
@time: 2021/11/28 17:06
@file: engine.py

"""
from logbook import Logger
from sqlalchemy import create_engine
from aiutils.singleton import SingletonTypeThreadSafe, SingletonType
from .config import AIUTILS_MYSQL_CONFIG


# class StoreMysqlEngine(metaclass=SingletonTypeThreadSafe):  # create_engine使用了pool，是否还要限制为全线程单例(影响速度)
class StoreMysqlEngine(metaclass=SingletonType):

    def __init__(self):
        self.logger = Logger(self.__class__.__name__)
        self.logger.debug(f'单例模式 初始化')
        self._engine_dict = {}
        # engine 不在init时全创建，改为需要get时再创建-->避免某个库加载失败，导致其它也不能用

    def get(self, db: str):
        engine = self._engine_dict.get(db, None)
        if not engine:
            engine = self.set(db)
        return engine

    def set(self, db):
        self._set_connect(db)

        try:
            self._engine_dict[db]
        except Exception as e:
            raise RuntimeError(f"{self.__class__.__name__} can not get db={db}")
        else:
            return self._engine_dict[db]

    def _set_connect(self, db):
        """ 创建并测试能否连接；保存到self._engine_dict """
        try:
            db_dict = AIUTILS_MYSQL_CONFIG.attrs.database.convert_to_dict()
            url = db_dict.get(db)
            self._engine_dict[db] = create_engine(
                url,
                pool_size=AIUTILS_MYSQL_CONFIG.attrs.engine_params.pool_size,
                max_overflow=AIUTILS_MYSQL_CONFIG.attrs.engine_params.max_overflow,
                pool_timeout=AIUTILS_MYSQL_CONFIG.attrs.engine_params.pool_timeout,
                pool_recycle=AIUTILS_MYSQL_CONFIG.attrs.engine_params.pool_recycle,
                pool_pre_ping=AIUTILS_MYSQL_CONFIG.attrs.engine_params.pool_pre_ping
            )
            self._engine_dict[db].connect()

        except Exception as e:
            raise RuntimeError(f"{self.__class__.__name__} 创建engine失败：{str(e)} 连接地址：{url}")
