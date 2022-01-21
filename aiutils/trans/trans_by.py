# -*- coding: utf-8 -*-
"""
@time: 2021/11/13 14:23
@file: trans_by.py

"""
import gzip
import pickle
from io import BytesIO

import pandas as pd

from aiutils.json_obj import my_json
from .trans_error import TransError


class TransParser(object):
    """
    解析http传输的数据，与trans_to.py中的规则相一致
    * by_xxx方法：不同传输方式的解析方法；
    * 返回结果：根据obj['status']的编码，小于零时实例化TransError，抛出异常；正常时，仅返回 obj['data'] 部分
    """

    @classmethod
    def by_pickle(cls, response_content: bytes):
        """ 使用 pickle 方式传输 """
        return _parse_pickle(response_content)

    @classmethod
    def by_pkgz(cls, response_content: bytes):
        """ pickle外加gzip压缩的传输方式 """
        pk = gzip.decompress(response_content)
        return _parse_pickle(pk)

    @classmethod
    def by_json(cls, response_text: str):
        """ 使用 json 方式传输 """
        # response_text: Response响应，携带的json字符串(requests库中r.text)
        obj = my_json.loads(response_text)  # 解析成python内置对象

        status = int(obj['status'])
        if status < 0:
            if '】' in obj['msg']:
                msg = obj['msg'].split('】')[-1]
            else:
                msg = obj['msg']
            e = TransError(int(obj['status']), msg)
            raise e

        # 根据status分配
        if status == 0:
            return _parse_dict_raw(obj)
        elif status == 1:
            return _parse_dict_raw(obj)
        elif status == 2:
            return _parse_dict_pandas(obj)
        else:
            raise ValueError(f'trans_by协议：未定义的解析方式 {status}')


def _parse_pickle(b: bytes):
    """ pickle传输：不同status都通用的解析方法 """
    obj = pickle.loads(b)  # 解析成python内置对象
    if int(obj['status']) < 0:
        # 数据出错的情况，提取出msg
        if '】' in obj['msg']:
            msg = obj['msg'].split('】')[-1]
        else:
            msg = obj['msg']
        e = TransError(int(obj['status']), msg)
        raise e
    else:
        # 数据正常的情况
        return obj['data']


# ----------------------------------------------------------------------------------------------
def _parse_dict_raw(obj):
    """ 对应TransRaw """
    d = obj
    if int(d['status']) < 0:
        if '】' in d['msg']:
            msg = d['msg'].split('】')[-1]
        else:
            msg = d['msg']
        e = TransError(int(d['status']), msg)
        raise e
    return d['data']


def _parse_dict_pandas(obj):
    """ 对应TransPandas """
    d = obj
    if int(d['status']) < 0:
        if '】' in d['msg']:
            msg = d['msg'].split('】')[-1]
        else:
            msg = d['msg']
        e = TransError(int(d['status']), msg)
        raise e

    # 数据还原
    _all = pd.DataFrame(data=d['data'])
    if d['msg'].get('all_dtype'):
        mapping = {}  # df中的object，df[col].type.str为'|O'，不能被df.astype识别
        for k, v in d['msg'].get('all_dtype').items():
            if v == '|O':
                mapping[k] = 'object'
            else:
                mapping[k] = v

        _all = _all.astype(mapping)  # 数据类型的转换

    all_cols = list(_all.columns)

    if d['msg'].get('ind_names'):
        _all = _all.set_index(d['msg'].get('ind_names'))
        reback = []
        for x in d['msg'].get('ind_names'):
            if x.startswith('___') and x.endswith('___'):
                mid = x[3:-3]
                if mid.startswith('none-'):
                    reback.append(None)
                else:
                    reback.append(mid)
            else:
                reback.append(x)

        _all.index.names = reback

    if d['msg'].get('typ') == 'Series':
        col_names = [x for x in all_cols if x not in d['msg'].get('ind_names', [])]
        assert len(col_names) == 1
        _all = _all[col_names[0]]
        if _all.name == '___none___':
            _all.name = None

    return _all
