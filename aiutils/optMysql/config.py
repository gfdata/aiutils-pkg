# -*- coding: utf-8 -*-
"""
@time: 2021/11/28 16:59
配置对象
"""

from aiutils.dict_obj import AttrDict, dict_deep_update
from aiutils.singleton import SingletonTypeThreadSafe


class _MysqlConfig(metaclass=SingletonTypeThreadSafe):
    # 多线程单例，确保其他项目中使用optMysql时，配置项只有一份
    # 默认配置-->修改时也应遵循此结构
    _default = {
        "database": {
            "//": "数据库的name和url",

        },
        "engine_params": {
            "//": "创建engine的参数设置",
            "pool_size": 50,
            "max_overflow": 25,
            "pool_timeout": 360,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
        },

        "//": "查询的参数设置",
        "query_limit": 1024000,
    }

    def __init__(self):
        self.final = {}
        dict_deep_update(self._default, self.final)

    def update(self, d: dict):
        dict_deep_update(d, self.final)
        return self.final

    def update_database(self, name, url):
        """ 修改database的url方式 """
        self.final['database'].update({name: url})

    @property
    def attrs(self) -> AttrDict:
        return AttrDict(self.final)


AIUTILS_MYSQL_CONFIG = _MysqlConfig()
