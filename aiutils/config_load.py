# -*- coding: utf-8 -*-
"""
@time: 2021/10/19 15:38
@file: config_load.py

加载配置项
"""
import os
import codecs
import json
import yaml
from pathlib import Path
from typing import Tuple

from .dict_obj import dict_deep_update, AttrDict
from .log_book import AI_UTILS_LOGGER


def config_dir(config_relative='env', cwd_dir=Path.cwd(), proj_dir=None, home_dir=Path.home()):
    # type: (str, Path, Path, Path) -> Tuple[Path, Path]
    """获取配置项的绝对路径
    查找顺序：cmd>proj>home
    :param config_relative: 配置项的相对目录，默认使用env目录
    :param cwd_dir: 当前的目录
    :param proj_dir: 项目的目录
    :param home_dir: 用户的目录
    :return: Tuple[所在目录，配置项目录]
    """
    if cwd_dir:
        temp_path = cwd_dir.joinpath(config_relative)
        if temp_path.exists():
            return cwd_dir, temp_path
    if proj_dir:
        temp_path = proj_dir.joinpath(config_relative)
        if temp_path.exists():
            return proj_dir, temp_path
    if home_dir:
        temp_path = home_dir.joinpath(config_relative)
        if temp_path.exists():
            return home_dir, temp_path
    raise EnvironmentError(
        f"""需要配置 {config_relative} 以下路径选择一个：
        当期路径 {cwd_dir}
        项目路径 {proj_dir}
        home路径 {home_dir}
        """
    )


class ConfigLoading:

    def __init__(self, default: dict, app_name: str):
        """
        配置项加载器
        :param default:
        :param app_name:
        """
        self.final = {}
        dict_deep_update(default, self.final)
        self.name = app_name

    def update_config_json(self, file) -> dict:
        """ json格式的配置项 """
        try:
            with codecs.open(file, encoding='utf-8') as f:
                d = json.loads(f.read())
        except Exception as e:
            AI_UTILS_LOGGER.error(f'项目[{self.name}]加载json配置失败[{file}]', e)
            raise e
        s = f'项目[{self.name}]加载json配置[{file}]'
        print("\033[1;32;40m" + s + "\033[0m" + f"{os.linesep}")  # 调整终端颜色并换行
        AI_UTILS_LOGGER.critical(s)
        dict_deep_update(d, self.final)
        return self.final

    def update_config_yaml(self, file) -> dict:
        """ yml格式的配置项 """
        try:
            with codecs.open(file, encoding='utf-8') as f:
                d = yaml.safe_load(f)
        except Exception as e:
            AI_UTILS_LOGGER.error(f'项目[{self.name}]加载yaml配置失败[{file}]', e)
            raise e
        s = f'项目[{self.name}]加载yaml配置成功[{file}]'
        AI_UTILS_LOGGER.critical(s)
        return self.final

    @property
    def attr_dict(self) -> AttrDict:
        return AttrDict(self.final)
