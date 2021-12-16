"""
单例模式
- 参考 [https://www.cnblogs.com/huchong/p/8244279.html]

"""

import threading


class SingletonType(type):

    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(SingletonType, cls).__call__(*args, **kwargs)
        return cls._instance


class SingletonTypeThreadSafe(type):
    """
    其它对象的实现，通过传入参数 metaclass=SingletonTypeThreadSafe
    线程安全
    """
    _instance_lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            with SingletonTypeThreadSafe._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = super(SingletonTypeThreadSafe, cls).__call__(*args, **kwargs)
        return cls._instance
