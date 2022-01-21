# -*- coding: utf-8 -*-
"""
@time: 2021/11/13 14:23
@file: trans_error.py

"""
from enum import Enum


class TransOutputEnum(Enum):
    """
    支持的数据打包方式
    """
    json = 'json'
    pickle = 'pickle'
    pkgz = 'pkgz'  # pickle进行gzip压缩


class TransError(Exception):
    def __init__(self, status: int, msg):
        """
        传输转换的错误类型
        :param status: 规则：-1x 服务端错误；-2x 用户错误
        :param msg: str或可以str()转换的对象
        """
        self.status = int(status)
        if str(status).startswith('-1'):
            if str(status).startswith('-11'):
                pre = '【server 执行超时】'
            elif str(status).startswith('-12'):
                pre = '【server 数据缺失】'
            else:
                pre = '【server 其它错误】'

        elif str(status).startswith('-2'):
            if str(status).startswith('-21'):
                pre = '【user 权限不足】'
            elif str(status).startswith('-22'):
                pre = '【user 传参错误】'
            else:
                pre = '【user 其它错误】'

        else:
            raise ValueError(f'status开头应是[-1, -2], got {status}')

        # 拼接错误信息
        if isinstance(msg, str):
            self.msg = pre + msg
        else:
            self.msg = pre + str(msg)

    def __str__(self):
        return f"类型{self.status}:内容{self.msg}"

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self.__str__())
