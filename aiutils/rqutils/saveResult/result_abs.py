# -*- coding: utf-8 -*-
# @time: 2022/7/23 14:31
# @Author：lhf
# ----------------------
class ResultAbstract:
    """数据的存储方式"""

    @property
    def output_path(self):
        raise NotImplementedError()

    def read_common_df(self, file_name, sheet_name, use_cache=True):
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------
    def is_exist(self) -> bool:
        raise NotImplementedError()

    def save_common_df(self, file_name, sheet_name, df):
        raise NotImplementedError()

    def save_common_jsonable(self, name, obj):
        """ 通用的存储可json序列化的数据 """
        raise NotImplementedError()

    def save_context_config(self, context):
        raise NotImplementedError()

    def save_rq_run(self, rq: dict):
        raise NotImplementedError()
