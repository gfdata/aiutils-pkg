# -*- coding: utf-8 -*-
# @time: 2022/1/15 13:56
# @Author：lhf
# ----------------------
from enum import Enum


def enum_obj_extend(enum: Enum, extend_dict: dict):
    """
    枚举类对象 扩展成员属性
    :params enum: Enum 枚举类型
    :params extend_dict: dict 追加的项目和值的字典
    :return: None
    """
    # 先做 key, value的唯一性校验
    if (
            extend_dict.keys() & enum._member_map_.keys() or
            extend_dict.values() & enum._value2member_map_.keys()
    ):
        raise ValueError('extend_dict:{} is invalid'.format(extend_dict))

    # 追加枚举项目
    for key, val in extend_dict.items():
        # 实例化枚举对象，enum.__new__ 是被重写过的，
        # 所以直接使用 object.__new__ 加赋值的方式实现
        v = object.__new__(enum)
        v.__objclass__ = enum
        v._name_ = key
        v._value_ = val

        # 将枚举对象加入枚举类型的映射表里
        enum._member_map_[key] = v  # 名字对应对象的字典
        enum._member_names_.append(key)  # 名字列表
        enum._value2member_map_[val] = v  # 值对应对象的字典
