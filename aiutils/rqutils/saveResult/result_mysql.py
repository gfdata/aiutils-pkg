# -*- coding: utf-8 -*-
# @time: 2022/7/23 13:59
# @Author：lhf
# ----------------------
import json
from copy import deepcopy

import pandas as pd
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, Text, inspect

from aiutils.opt_mysql.engine import StoreMysqlEngine
from aiutils.pandas_obj import df_col_dt_like
from aiutils.sql import df_insert
from aiutils.json_obj import jsonable_encoder
from aiutils.sql_session import with_db_session

from .result_abs import ResultAbstract

Base = declarative_base()


class AllSidRouter(Base):
    __tablename__ = 'all_sid_router'
    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    id_name = Column(String(64), comment='策略id_name')
    sid_str = Column(String(255), unique=True, comment='策略识别码')


class ResultMysql(ResultAbstract):
    def __init__(self, id_name, id_script, id_vars,
                 save_db_name):
        self.id_name = id_name
        self.id_script = id_script
        self.id_vars = id_vars
        # 其他规则
        self._save_db_name = save_db_name
        self._engine = StoreMysqlEngine().get(save_db_name)
        self._sid_str = "+".join([self.id_name, self.id_script, self.id_vars])  # 建议与StrategyIdentify保持一致
        self._tb_prefix = None
        self._query_sid_router()

    @property
    def output_path(self):
        """ 此处output_path只是为了显示，无实际作用 """
        return str(self._engine.url) + '\nsid=' + str(self._sid_str)

    def _query_sid_router(self):
        try:
            temp = self._engine.has_table(AllSidRouter.__tablename__)  # sqlalchemy 1.4版本后弃用
        except AttributeError:
            temp = inspect(self._engine).has_table(AllSidRouter.__tablename__)  # sqlalchemy版本2.0以上 使用insp
        if not temp:
            Base.metadata.create_all(self._engine)
        # 查找与更新
        with with_db_session(self._engine) as session:
            obj = session.query(AllSidRouter).filter_by(sid_str=self._sid_str).first()
            if not obj:
                obj = AllSidRouter(id_name=self.id_name, sid_str=self._sid_str)
            else:
                obj.id_name = self.id_name
            session.add(obj)
            session.commit()
            assert obj.id is not None and obj.id_name  # 要用到自增id
            self._tb_prefix = '-'.join([str(obj.id_name), str(obj.id)])

    def read_common_df(self, file_name, sheet_name, use_cache=True):
        table_name = self._gen_table_name(file_name, sheet_name)
        if not self._engine.has_table(table_name):
            raise ValueError(f'缺少表格 {table_name}')
        df = pd.read_sql(f"select * from `{table_name}`", self._engine)
        return df

    def is_exist(self) -> bool:
        if self._engine.has_table(self._tb_prefix):
            return True
        else:
            return False

    def _gen_table_name(self, file_name, sheet_name):
        suffix_list = [x for x in (file_name, sheet_name) if x]
        if suffix_list:
            suffix = '-'.join(suffix_list)
            table_name = self._tb_prefix + "+" + suffix
        else:
            table_name = self._tb_prefix
        return table_name

    def save_common_df(self, file_name, sheet_name, df, **kwargs):
        # 表格规则
        if df is None or df.empty:
            return
        table_name = self._gen_table_name(file_name, sheet_name)

        # 数据检查
        new_df = df
        if kwargs['primary_keys']:
            if isinstance(kwargs['primary_keys'], str):
                new_pk = [kwargs['primary_keys']]
            else:
                new_pk = [x for x in kwargs['primary_keys']]
        else:
            new_pk = None
        # 识别时间列
        dt_cols = [x for x in new_df.columns if df_col_dt_like(new_df, x)]
        res = df_insert(new_df, dt_columns=dt_cols, dt_format=None,  # 会使用默认
                        table_name=table_name, engine=self._engine, ignore_none=False,  # 如有空值也会存入
                        primary_keys=new_pk, schema=self._save_db_name,
                        )
        return res

    def save_common_jsonable(self, name, obj):
        """可能存在嵌套字典，所以只能保存为字符串 """
        d = jsonable_encoder(obj)
        df = pd.Series({'name': name, 'content': json.dumps(d)}).to_frame().T
        self.save_common_df(None, None, df.reset_index(), primary_keys='name')

    def save_context_config(self, context):
        temp = deepcopy(context.config.convert_to_dict())
        del temp['base']['trading_calendar']
        self.save_common_jsonable('context_config', temp)

    def save_rq_run(self, rq: dict):
        # 存储sys_analyser
        temp = rq.get('sys_analyser', None)
        if temp:
            summary = pd.Series(temp['summary']).to_frame('summary').reset_index()
            self.save_common_df('sys_analyser', 'summary', summary, **_save_rq_run_kwargs['summary'])  # 需要整理一下
            # mod_sys_analyser中会用到的key
            for name in ["portfolio", "stock_account", "future_account",
                         "stock_positions", "future_positions", "trades"]:
                try:
                    df = temp[name]
                except KeyError:
                    continue
                # replace all date in dataframe as string
                if df.index.name == "date":  # 例如portfolio按日统计；trades带时间部分
                    df = df.reset_index()
                    df["date"] = df["date"].apply(lambda x: x.strftime("%Y-%m-%d"))
                    df = df.set_index("date")
                # index name 和cols重复时
                if df.index.name in df.columns:
                    del df[df.index.name]
                df = df.reset_index()  # 以下函数不会保存index，所以需要reset
                self.save_common_df('sys_analyser', name, df, **_save_rq_run_kwargs[name])


_save_rq_run_kwargs = {
    'summary': {'primary_keys': 'index'},
    'portfolio': {'primary_keys': 'date'},
    'stock_account': {'primary_keys': 'date'},
    'future_account': {'primary_keys': 'date'},
    'stock_positions': {'primary_keys': ['date', 'order_book_id']},
    'future_positions': {'primary_keys': ['date', 'order_book_id']},
    # 'trades': {'primary_keys': ['trading_datetime', 'order_book_id']},
    # 相同品种一天内多笔时，主键用下单编号更合理
    'trades': {'primary_keys': ['trading_datetime', 'order_book_id', 'exec_id', 'order_id']},
}
