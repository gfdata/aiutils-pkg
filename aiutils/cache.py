# -*- coding: utf-8 -*-
"""
@time: 2021/10/19 17:05
@file: cache.py
缓存功能
"""
import inspect
import os
import sys
import time
import threading
import warnings
from functools import update_wrapper, wraps
from logbook import Logger
from collections import OrderedDict
import hashlib

try:
    import cPickle as pickle
except ImportError:
    import pickle


# ---------------------------------------------------------------------------------------
def ttl_cache(ttl):
    """缓存装饰器
    可设定缓存秒数
    """
    if not isinstance(ttl, int) or not ttl > 0:
        raise TypeError("Expected ttl to be a positive integer")

    def decorating_function(user_function):
        wrapper = _ttl_cache_wrapper(user_function, ttl)
        return update_wrapper(wrapper, user_function)

    return decorating_function


def _ttl_cache_wrapper(user_function, ttl):
    sentinel = object()
    cache = {}
    cache_get = cache.get  # bound method to lookup a key or return None

    def wrapper(*args, **kwargs):
        if kwargs:
            key = args + (repr(sorted(kwargs.items())),)
        else:
            key = args

        # in cpython, dict.get is thread-safe
        result = cache_get(key, sentinel)
        if result is not sentinel:
            expire_at, value = result
            if expire_at > time.time():
                return value
        value = user_function(*args, **kwargs)
        cache[key] = (time.time() + ttl, value)
        return value

    return wrapper


# ---------------------------------------------------------------------------------------
def cache_safe(cls_or_func):
    """缓存装饰器：
    线程安全，作用于类或函数，可用于实现 `缓存实例对象`
    """
    instances = {}

    @_synchronized
    def get_instance(*args, **kw):
        # key = cls_or_func
        key = _make_arguments_to_key(cls_or_func, *args, **kw)
        if key not in instances:
            instances[key] = cls_or_func(*args, **kw)
        return instances[key]

    return get_instance


def _synchronized(func):
    """ 装饰器：为函数添加线程锁 """
    func.__lock__ = threading.Lock()

    def synced_func(*args, **kws):
        with func.__lock__:
            return func(*args, **kws)

    return synced_func


def _make_arguments_to_key(method, *args, **kwargs):
    arg_dict = inspect.getcallargs(method, *args, **kwargs)
    # arg_dict = {str(method): args}  # method内存对象地址每次运行在变，不能用str(method)
    # arg_dict.update(kwargs)

    # 更新method相关属性-->保证唯一性
    arg_dict.update(
        {'__qualname__': method.__qualname__,
         '__module__': method.__module__,
         }
    )
    # FIXME被装饰函数包含self参数时存在问题。key只由后面参数确定,保留self cls出现TypeError: can't pickle module objects
    arg_dict.pop('self', None)
    arg_dict.pop('cls', None)
    sorted_arg_dict = sorted(arg_dict.items())
    key = hashlib.md5(pickle.dumps(sorted_arg_dict)).hexdigest()
    return key


# ------------------------------------------------------------------------------------------
class MemoryCache(object):
    """
    缓存在内存的装饰器
    * 使用方式 @LocalCache.cached_function_result_for_a_time()
    * 适用于数据过大时，控制内存不被占用太多。
    * 此处可缓存任何对象，不同于LocalCache(只能缓存可pickle的对象)
    """
    logger = Logger('MemoryCache')
    func_result_dict = OrderedDict()

    @classmethod
    def cached_function_result_for_a_time(cls, cache_mb=2048, cache_second=60):
        """
        :param cache_mb: 整个缓存器的最大内存
        :param cache_second: 最长缓存秒数
        :return:
        """

        def _cached_function_result_for_a_time(fun):
            @wraps(fun)
            def __cached_function_result_for_a_time(*args, **kwargs):
                if sys.getsizeof(cls.func_result_dict) > cache_mb * 1024:
                    # cls.func_result_dict.clear()
                    cls.func_result_dict.popitem(last=False)  # 先进先出

                key = _make_arguments_to_key(fun, *args, **kwargs)
                if (fun, key) in cls.func_result_dict and time.time() - cls.func_result_dict[(fun, key)][
                    1] < cache_second:
                    cls.logger.debug(f'[{fun.__name__}]使用缓存[{key}]')
                    return cls.func_result_dict[(fun, key)][0]
                else:
                    cls.logger.debug(f'[{fun.__name__}]未使用缓存[{key}]')
                    result = fun(*args, **kwargs)
                    if result is not None:
                        cls.func_result_dict[(fun, key)] = (result, time.time())
                    return result

            return __cached_function_result_for_a_time

        return _cached_function_result_for_a_time


# ------------------------------------------------------------------------------------------
def _read_pickle_cache(file, cache_second):
    if not os.path.isfile(file):
        raise RuntimeError(f'文件未创建')
    # 文件最近修改时间
    if time.time() - os.path.getmtime(file) < cache_second:
        t_bool = True
    else:
        t_bool = False
    if not t_bool:
        raise RuntimeError(f'文件过期')

    # 读取
    try:
        with open(file, 'rb') as cache_fd:
            result = pickle.load(cache_fd)
    except Exception as e:
        msg = f'文件读取失败[{file}]{e}'  # 此情况 msg详细些
        warnings.warn(msg, UserWarning)
        raise e
    else:
        return result


class PickleCache(object):
    """
    缓存到本地pickle文件
    * 使用方式 @LocalCache.cached_function_result_for_a_time()，可传入子路径
    * 对可pickle的对象，实现文件缓存
    """
    logger = Logger('PickleCache')

    @classmethod
    def cached_function_result_for_a_time(cls, cache_dir, child_dir='',
                                          cache_second=3600):
        def _cached_function_result_for_a_time(fun):
            @wraps(fun)
            def __cached_function_result_for_a_time(*args, **kwargs):
                # 缓存主目录
                if not os.path.isdir(cache_dir):
                    os.makedirs(cache_dir)

                # 生成key
                key = _make_arguments_to_key(fun, *args, **kwargs)
                # 查找文件
                if child_dir:
                    temp_dir = os.path.join(cache_dir, child_dir)  # 指定localCache的子目录时
                    if not os.path.isdir(temp_dir):
                        os.makedirs(temp_dir)
                    cache_file = os.path.join(temp_dir, key)
                else:
                    cache_file = os.path.join(cache_dir, key)

                # 读取缓存文件
                try:
                    result = _read_pickle_cache(cache_file, cache_second)
                except Exception as e:
                    msg = f'[{fun.__name__}]未使用pickle缓存[{key}]：[{str(e)}]'
                    cls.logger.debug(msg)
                    result = cls.exec_func_and_pickle(cache_file, fun, *args, **kwargs)
                else:
                    cls.logger.debug(f'[{fun.__name__}]使用pickle缓存[{key}]')

                # 最后返回结果
                return result
                #
                # # 文件最近修改时间
                # t_bool = False
                # if os.path.isfile(cache_file):
                #     if time.time() - os.path.getmtime(cache_file) < cache_second:
                #         t_bool = True
                #
                # # 是否使用缓存
                # if t_bool and os.path.isfile(cache_file):
                #     try:
                #         with open(cache_file, 'rb') as cache_fd:
                #             result = pickle.load(cache_fd)
                #     except Exception as e:
                #         msg = f'[{fun.__name__}]使用缓存失败！[{key}]读取pickle异常[{str(e)}]'
                #         warnings.warn(msg, RuntimeWarning)  # 之后也会执行后面代码：其他情况
                #     else:
                #         cls.logger.debug(f'[{fun.__name__}]使用缓存[{key}]')
                #         return result  # 不会执行后面代码：其他情况
                #
                # # 其他情况
                # cls.logger.debug(f'[{fun.__name__}]未使用缓存[{key}]')
                # result = cls.exec_func_and_pickle(cache_file, fun, *args, **kwargs)
                # return result

            # -----以下为wrapper的return-----
            return __cached_function_result_for_a_time

        return _cached_function_result_for_a_time

    @classmethod
    def exec_func_and_pickle(cls, cache_file, fun, *args, **kwargs):
        result = fun(*args, **kwargs)
        if result is not None:
            try:
                with open(cache_file, 'wb') as cache_fd:
                    pickle.dump(result, cache_fd)
            except Exception as e:
                msg = '[{}]结果pickle失败[{}]'.format(fun.__name__, str(e))
                warnings.warn(msg, RuntimeWarning)

        return result
