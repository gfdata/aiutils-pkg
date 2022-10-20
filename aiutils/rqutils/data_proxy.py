# -*- coding: utf-8 -*-
# @time: 2022/3/24 15:28
# @Author：lhf
# ----------------------
"""
直接使用rqalpha提供数据
"""
import os
import copy
from rqalpha.data import DataProxy
from rqalpha.environment import Environment
from rqalpha.utils import RqAttrDict
from rqalpha.utils.config import parse_config
from rqalpha.utils.functools import clear_all_cached_functions
from rqalpha.utils.package_helper import import_mod


def _base_data_source():
    from rqalpha.data.base_data_source import BaseDataSource
    # 已有env环境则直接返回，否则重新创建
    try:
        _env = Environment.get_instance()
        if isinstance(_env.data_source, BaseDataSource):
            return _env.data_proxy
        else:
            raise RuntimeError(f'当前rqalpha data_source不是来自{BaseDataSource.__module__}')
    except RuntimeError:
        pass

    # 默认配置config
    from rqalpha.utils import config
    _dir = os.path.join(os.path.expanduser('~'), ".rqalpha")
    if not os.path.exists(os.path.join(_dir, 'config.yml')):
        raise RuntimeError(f'缺少默认配置！目录{_dir} 文件config.yml')
    config.rqalpha_path = _dir  # 框架中用的就是.rqalpha 其实不用改
    conf = parse_config({})
    clear_all_cached_functions()

    # 创建环境
    _env = Environment(conf)
    data_source = BaseDataSource(
        path=conf.base.data_bundle_path, custom_future_info=conf.base.future_info)
    from rqalpha.data.bar_dict_price_board import BarDictPriceBoard
    data_board = BarDictPriceBoard()
    data_proxy = DataProxy(data_source, data_board)
    return data_proxy


PROXY_BASE = _base_data_source()


def _mod_ricequant_data():
    from rqalpha_mod_ricequant_data.data_sources.bundle_data_source import BundleDataSource
    # 已有env环境则直接返回，否则重新创建
    lib_name = 'rqalpha_mod_ricequant_data'
    try:
        _env = Environment.get_instance()
        if isinstance(_env.data_source, BundleDataSource):
            return _env.data_proxy
        else:
            raise RuntimeError(f'当前rqalpha data_source不是来自{lib_name}')
    except RuntimeError:
        pass

    # 默认配置config
    from rqalpha.utils import config
    _dir = os.path.join(os.path.expanduser('~'), ".rqalpha-plus")
    if not os.path.exists(os.path.join(_dir, 'config.yml')):
        raise RuntimeError(f'缺少默认配置！目录{_dir} 文件config.yml')
    config.rqalpha_path = _dir  # rqalpha_plus用的不是框架中的.rqalpha
    conf = parse_config({})
    clear_all_cached_functions()

    # 创建环境
    _env = Environment(conf)
    # 此时conf对此mod设置只有enable=True；没有详细的mod配置
    # 需要读取具体的mod配置；rqalpha_plus在mod_handler.set_env执行时，修改了config.mod.xx具体的配置参数
    mod_module = import_mod(lib_name)
    mod_config = RqAttrDict(copy.deepcopy(getattr(mod_module, "__config__", {})))
    # rqalpha_plus启动mod_riquant_data绑定了data_source；BundleDataSource内部依赖全局的Env
    data_source = BundleDataSource(
        conf.base.data_bundle_path, mod_config.h5_minbar_path, mod_config.h5_tick_path,
        tick_type=mod_config.tick_type, custom_future_info=conf.base.future_info
    )
    from rqalpha_mod_ricequant_data.minute_price_board import MinutePriceBoard
    data_board = MinutePriceBoard()
    data_proxy = DataProxy(data_source, data_board)
    return data_proxy


# DataProxy使用不同mod
PROXY_RQLPUS = _mod_ricequant_data()
