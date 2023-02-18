# -*- coding: utf-8 -*-
import random
import string
from uuid import uuid4


def random_code_digit(n=6) -> string:
    """ 随机字符串：纯数字 """
    l = random.sample(string.digits, n)
    return ''.join(l)


def random_code_string(n=6) -> string:
    """ 随机字符串：纯字母 """
    l = random.sample(string.ascii_letters, n)
    return ''.join(l)


def random_code_mix(n=6) -> string:
    """ 随机字符串，混合数字和字母 """
    l = random.sample(string.ascii_letters + string.digits, n)
    return ''.join(l)


def random_int_range(_min=1, _max=100) -> int:
    """ 随机取范围内的整数 """
    return random.randint(_min, _max)


def uuid_split_position(po=0):
    """ 截取uuid某个字串 """
    # UUID的标准型式包含32个16进制数字，以连字号分为五段，形式为8-4-4-4-12的32个字符
    assert 0 <= po <= 4
    return str(uuid4()).split("-")[po]
