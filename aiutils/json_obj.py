# -*- coding: utf-8 -*-
"""
@time: 2021/11/13 14:35
@file: json_obj.py

"""
try:
    # 不同的json，统一为my_json进行调用
    import orjson


    class my_json:
        @staticmethod
        def dumps(obj):
            # orjson 很个性，dumps 函数默认返回 byte 数据，需要转化
            return str(orjson.dumps(obj), encoding="utf-8")

        @staticmethod
        def loads(s):
            return orjson.loads(s)
except ModuleNotFoundError:
    try:
        import ujson as my_json
    except:
        import json as my_json
