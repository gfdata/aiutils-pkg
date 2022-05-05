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


def _plus_ricequant():
    from rqalpha.utils import config
    from rqalpha_mod_ricequant_data.data_sources.bundle_data_source import BundleDataSource
    from rqalpha_mod_ricequant_data.minute_price_board import MinutePriceBoard

    # 修改整个默认配置目录
    config.rqalpha_path = os.path.join(os.path.expanduser('~'), ".rqalpha-plus")
    conf = parse_config({})
    clear_all_cached_functions()
    # rqalpha_plus 在 mod_handler.set_env执行时，修改了config.mod.xx具体的配置参数
    lib_name = 'rqalpha_mod_ricequant_data'
    mod_module = import_mod(lib_name)
    mod_config = RqAttrDict(copy.deepcopy(getattr(mod_module, "__config__", {})))

    # rqalpha_plus 启动 mod_riquant_data 绑定了data_source；BundleDataSource内部还依赖全局的 Env
    _env = Environment(conf)
    data_source = BundleDataSource(
        conf.base.data_bundle_path, mod_config.h5_minbar_path, mod_config.h5_tick_path,
        tick_type=mod_config.tick_type, custom_future_info=conf.base.future_info
    )
    data_board = MinutePriceBoard()
    data_proxy = DataProxy(data_source, data_board)
    return data_proxy


# DataProxy使用不同mod
PROXY_RQLPUS = _plus_ricequant()
