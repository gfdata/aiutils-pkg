# -*- coding: utf-8 -*-
"""
@time: 2021/11/13 14:23
@file: trans_to.py

"""
import gzip
import pickle
from typing import Any, Union
from copy import deepcopy
import pandas as pd

from .trans_error import TransError


class TransAbstract:

    def __init__(self, data: Any = None, msg: Union[str, dict] = None, status: int = 0):
        """
        根据传入的数据，生成用于传输的结构体
        根据传输类型，实现 to_xxx对象方法；transParser中做对应的解析，还原出对象；

        :param data: 任意类型；根据to_xxx函数 做相应转换
        :param msg: 字符串、字典类型；不传入时默认值None
        :param status: 整数类型>=0；每个TransAbstract对应自己的默认值，且相互不能冲突

        """
        self.data_raw = data
        self.status = status
        # 为空字符串或空字典，赋值为None
        if not msg:
            self.msg = None
        else:
            self.msg = msg

    def to_dict(self) -> dict:
        """
        生成可以做json.dumps的字典结构；第三方库中的对象，需要具体实现
        :return:
        """
        raise NotImplementedError

    def to_pickle(self) -> bytes:
        """
        数据做成pickle二进制
        :return:
        """
        return pickle.dumps({'data': self.data_raw, 'msg': self.msg, 'status': self.status})

    def to_pkgz(self) -> bytes:
        """
        数据做成pickle再进行gzip压缩
        :return:
        """
        pk = pickle.dumps({'data': self.data_raw, 'msg': self.msg, 'status': self.status})
        return gzip.compress(pk, compresslevel=9)

    @classmethod
    def by_pickle(cls, obj: bytes):
        d = pickle.loads(obj)

        if int(d['status']) < 0:
            e = TransError(int(d['status']), d['msg'])
            raise e

        return d['data']


class TransRaw(TransAbstract):
    """
    原样传输：
    * 传输的data就是load之后的d['data']内容
    * 适用场景：d['data']为语言内置对象，能够直接json处理。例如 string dict list
    """

    def __init__(self, data: Any = None, msg: dict = None, status: int = 1):
        super(TransRaw, self).__init__(data, msg, status)

    def to_dict(self):
        return {'data': self.data_raw, 'msg': self.msg, 'status': self.status}


class TransErrorObj(TransRaw):
    """
    传输自定义的error对象
    * init方法中，解析自定义Error的属性和内容
    """

    def __init__(self, e: TransError):
        super(TransErrorObj, self).__init__(data=None, msg=e.msg, status=e.status)


# -------------------------------------------------------------------------------------
class TransPandas(TransAbstract):
    """
    pandas数据类型的传输，支持Series、DataFrame
    * 传输结构中msg字典类型：
        * typ:'DataFrame'/'Series'
        * all_dtype: 所有数据列的类型，对应numpy的dtype str 表示方式
        * ind_names：作为索引的列名。注意___xxx___的特殊含义

    * 使用___xxx___的替换与还原：
        * 原始DataFrame 使用reset_index方法--对于没有names的索引，单索引 新增列名会自动设为'index'；多索引 新增列名会自动设为'level_n'
        * 原始DataFrame 使用reset_index方法--索引名字与列名重复时，会失败
        * 原始Series使用to_frame方法--没有name会自动设为0

    """

    def __init__(self, data: Union[pd.Series, pd.DataFrame] = None, msg: dict = None, status: int = 2):
        super(TransPandas, self).__init__(data, msg, status)

    def to_dict(self):
        _ind_names, dfall = TransPandas_gen(self.data_raw)
        _msg = TransPandas_gen_msg(self.data_raw, dfall, _ind_names)
        # 更新原始的msg
        if self.msg:
            if type(self.msg) == dict:
                msg_all = deepcopy(self.msg)
                for k, v in _msg.items():
                    msg_all[k] = v
            else:
                _msg['raw'] = self.msg
                msg_all = _msg

        else:
            msg_all = _msg

        # nan naT替换为None，否则不能被web框架Response自动转换
        return {'data': dfall.where(~dfall.isnull(), None).to_dict(orient='list'),
                'msg': msg_all,
                'status': self.status}


def TransPandas_gen_msg(data, dfall, _ind_names):
    """ 定义msg生成方式"""
    msg = {'typ': 'DataFrame'}
    if isinstance(data, pd.Series):
        msg['typ'] = 'Series'

    msg['all_dtype'] = {x: dfall[x].dtype.str for x in list(dfall.columns)}
    msg['ind_names'] = _ind_names
    return msg


def TransPandas_gen(data: Union[pd.Series, pd.DataFrame]):
    """
    定义的数据生成方式
    * notice!!! 函数内部会修改传入的data，所以想保持函数外部数据不受影响，应传入其deepcopy的拷贝
    """
    # 转化为普通索引的DataFrame
    if isinstance(data, pd.Series):
        if data.name is None:
            df = data.to_frame(name='___none___')
        else:
            df = data.to_frame()
    elif isinstance(data, pd.DataFrame):
        df = data
    else:
        raise TypeError(f'only support pd.Series and pd.DataFrame, got {type(data)}')

    # fixme索引没有names或names与原来columns重复
    fix = []
    for i in range(len(df.index.names)):
        x = df.index.names[i]
        if x is None:
            fix.append(f'___none-{i}___')
        else:
            fix.append(f'___{x}___') if x in list(df.columns) else fix.append(x)

    # 保存出来，保持顺序-->此处修改了传入的数据帧data
    _ind_names = deepcopy(fix)
    df.index.names = fix
    dfall = df.reset_index(drop=False)  # 经此两步，index的name保存到数据列，且不与原来的数据列重名

    return _ind_names, dfall
