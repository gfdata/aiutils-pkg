# -*- coding: utf-8 -*-
"""
@time: 2021/10/19 16:06
@file: dict_obj.py

dict工具
"""
import six
import pprint
import collections


class AttrDict(object):
    """
    嵌套字典，转化为多重属性的对象
    """

    def __init__(self, d=None):
        self.__dict__ = d if d is not None else dict()

        for k, v in list(six.iteritems(self.__dict__)):
            if isinstance(v, dict):
                self.__dict__[k] = AttrDict(v)

    def __repr__(self):
        return pprint.pformat(self.__dict__)

    def __iter__(self):
        return self.__dict__.__iter__()

    def update(self, other):
        AttrDict._update_dict_recursive(self, other)

    def items(self):
        return six.iteritems(self.__dict__)

    iteritems = items

    def keys(self):
        return self.__dict__.keys()

    @staticmethod
    def _update_dict_recursive(target, other):
        if isinstance(other, AttrDict):
            other = other.__dict__
        target_dict = target.__dict__ if isinstance(target, AttrDict) else target

        for k, v in six.iteritems(other):
            if isinstance(v, AttrDict):
                v = v.__dict__
            if isinstance(v, collections.Mapping):
                r = AttrDict._update_dict_recursive(target_dict.get(k, {}), v)
                target_dict[k] = r
            else:
                target_dict[k] = other[k]
        return target

    def convert_to_dict(self):
        result_dict = {}
        for k, v in list(six.iteritems(self.__dict__)):
            if isinstance(v, AttrDict):
                v = v.convert_to_dict()
            result_dict[k] = v
        return result_dict


def dict_deep_update(from_dict, to_dict):
    """
    嵌套字典的修改，会直接改变传入的to_dict对象；相同k层次才会修改对应的值，否则沿用to_dict原有的
    :param from_dict: 用于修改的字典
    :param to_dict: 待修改的目标字典
    :return: None
    """
    for (key, value) in from_dict.items():
        if (key in to_dict.keys() and
                isinstance(to_dict[key], collections.Mapping) and
                isinstance(value, collections.Mapping)):
            dict_deep_update(value, to_dict[key])
        else:
            to_dict[key] = value
