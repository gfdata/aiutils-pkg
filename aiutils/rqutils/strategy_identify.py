# -*- coding: utf-8 -*-
# @time: 2022/7/19 9:09
# @Author：lhf
# ----------------------
import os
import hashlib
import pickle
from pathlib import Path

from pydantic import BaseModel

from aiutils.rqutils.saveResult.result_abs import ResultAbstract


class StrategyIdentify:
    def __init__(self, id_name, id_script, id_vars, save_type=''):
        """
        通用的策略id生成规则：各个部分内部用-连接，各个部分之间用+连接
        * id_name项目的识别码；一般使用模块或项目的名称；
        * id_script脚本的识别码；一般使用 脚本文件路径 相对于 项目路径；
        * id_vars对context外部参数的识别码；
        """
        self.id_name = id_name
        self.id_script = id_script
        self.id_vars = id_vars
        # 存储方式
        self.save_type = save_type

    def __str__(self):
        return str(self.__class__.__name__) + ":" + "+".join([self.id_name, self.id_script, self.id_vars])

    def get_result_obj(self, **kwargs) -> ResultAbstract:
        if self.save_type == 'file':
            from aiutils.rqutils.saveResult import ResultFile
            obj = ResultFile(id_name=self.id_name,
                             id_script=self.id_script,
                             id_vars=self.id_vars,
                             save_space=kwargs['save_space'])
        elif self.save_type == 'mysql':
            from aiutils.rqutils.saveResult import ResultMysql
            obj = ResultMysql(id_name=self.id_name,
                              id_script=self.id_script,
                              id_vars=self.id_vars,
                              save_db_name=kwargs['save_db_name'])
        else:
            raise RuntimeError(f'支持的存储方式 file mysql， got {self.save_type}')
        return obj


def generate_id_name(name: str):
    return name


def generate_id_script(file_path, relative_path):
    file_path = Path(os.path.abspath(file_path))
    relative_path = Path(os.path.abspath(relative_path))
    id_script = file_path.with_suffix('').relative_to(relative_path)
    id_script = '-'.join(id_script.parts)
    return id_script


def generate_id_vars(context_vars: dict, explicit_keys: list, params_model_class=None):
    """
    :param context_vars: 传给context的变量
    :param explicit_keys: 不在BaseParams中的参数，需要显式体现在id字符串中
    :param params_model_class:
    :return:
    """
    # 显式体现的部分；不在BaseParams中的参数
    if explicit_keys is None or len(explicit_keys) == 0:
        args1 = '()'  # 不需要时用括号占位
    else:
        _keys = list(sorted(set(explicit_keys)))
        assert len(_keys) == len(explicit_keys), f'显式体现的部分：不能重复'
        try:
            temp = []
            for k in _keys:
                v = context_vars[k]
                temp.append(str(k) + "(" + str(v) + ")")
            args1 = ''.join(temp)
        except Exception as e:
            raise ValueError(f'显式体现的部分：explicit_keys要为context_vars的键 {e}')

    # BaseParams部分
    s = ''
    if params_model_class:
        if issubclass(params_model_class, BaseModel):
            p = params_model_class(**context_vars)
            sorted_arg_dict = sorted(p.dict().items())  # 按需要进行定义；参考 aiutils.cache._make_arguments_to_key
            s = hashlib.md5(pickle.dumps(sorted_arg_dict)).hexdigest()
        else:
            raise RuntimeError(f'params_model_class 不支持 {type(params_model_class)}')
    # 拼接起来
    if s:
        id_vars = args1 + "-" + s
    else:
        id_vars = args1
    return id_vars
