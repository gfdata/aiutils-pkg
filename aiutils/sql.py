# -*- coding: utf-8 -*-
import hashlib
import sys
from typing import List, Tuple
import pandas as pd
import sqlalchemy
from sqlalchemy import Table, MetaData, NVARCHAR, Integer, Float, DateTime, text, inspect
from sqlalchemy.exc import IntegrityError
from logbook import Logger

from .pandas_obj import df_col_dt_like, df_to_dict
from .list_obj import split_iter
from .sql_session import with_db_session, get_db_session


def repair_has_table(engine, table_name: str) -> bool:
    """ has_table判断，兼容sqlalchemy不同版本 """
    v = str(sqlalchemy.__version__)
    if v >= '2.0':
        return inspect(engine).has_table(table_name)  # sqlalchemy版本2.0以上
    elif v <= '2.0':
        return engine.has_table(table_name)
    else:
        raise ValueError(f'sqlalchemy版本无法判断 got {v}')


def df_types_sql(df: pd.DataFrame):
    dtypedict = {}
    for i, j in zip(df.columns, df.dtypes):
        if "object" in str(j):
            dtypedict.update({i: NVARCHAR(length=255)})
        if "float" in str(j):
            dtypedict.update({i: Float(20)})
        if "int" in str(j):
            dtypedict.update({i: Integer()})
        if df_col_dt_like(df, i):
            dtypedict.update({i: DateTime})
    return dtypedict


def df_insert(df: pd.DataFrame, dt_columns: list, dt_format: str,
              table_name: str, engine, ignore_none=True, chunksize=1024 * 128, add_col=False,
              dtype: dict = {}, primary_keys: list = None, schema=None
              ):
    """
    将 DataFrame 数据批量插入数据库，处理方式 ON DUPLICATE KEY UPDATE
    :param df:
    :param dt_columns: 最终用于dt_to_dict，含义参考该函数：
    :param dt_format: 最终用于dt_to_dict，含义参考该函数；
    :param table_name:
    :param engine:
    :param ignore_none: 表存在时：为 None 或 NaN 字段不更新
    :param chunksize:
    :param chunksize:

    :param dtype: 创建表格才用到：数据类型的映射；可以为空，会通过df_types_sql计算默认结果；
    :param primary_keys: 创建表格才用到：设置主键；可以为None，会创建无主键的表格；
    :param schema: 创建表格并设置主键才用到：通常为数据库的名称；此时不能为空
    :return:
    """
    logger = Logger(sys._getframe().f_code.co_name)
    if primary_keys:
        df = df.dropna(subset=primary_keys)
    if df.empty:
        logger.warn(f'数据去除主键空值后长度为零，不做存储！')
        return

    has_table = repair_has_table(engine, table_name)
    if has_table:
        insert_count = df_insert_existed(df, dt_columns, dt_format, table_name, engine, ignore_none, chunksize, add_col)
        return insert_count

    # 升级主键存储类型
    dtype = {k: v for k, v in dtype.items() if v}  # 剔除v为None的无效类型
    if primary_keys:
        for x in primary_keys:
            if x not in dtype.keys():
                dtype.update(df_types_sql(df[[x]]))

    # fix-->df.to_sql会自动替换NaT为前值 -->先按df.dtypes创建表格 创建主键，但不插入数据。再按df_insert_existed执行
    temp = df[slice(0)]
    temp.to_sql(table_name, engine, if_exists='fail', index=False, dtype=dtype, chunksize=chunksize)

    # 创建主键
    if primary_keys:
        if schema is None:
            raise ValueError('schema 不能为 None，对表设置主键时需要指定schema')
        qry_column_type = """SELECT column_name, column_type
            FROM information_schema.columns 
            WHERE table_schema=:schema AND table_name=:table_name"""
        with with_db_session(engine) as session:
            table = session.execute(text(qry_column_type), params={'schema': schema, 'table_name': table_name})
            column_type_dic = dict(table.fetchall())
            praimary_keys_len, col_name_last, col_name_sql_str_list = len(primary_keys), None, []
            for num, col_name in enumerate(primary_keys):
                col_type = column_type_dic[col_name]
                position_str = 'FIRST' if col_name_last is None else f'AFTER `{col_name_last}`'
                col_name_sql_str_list.append(
                    f'CHANGE COLUMN `{col_name}` `{col_name}` {col_type} NOT NULL {position_str}' +
                    ("," if num < praimary_keys_len - 1 else "")
                )
                col_name_last = col_name
            # chg_pk_str = """ALTER TABLE `{table_name}`
            #     CHANGE COLUMN `ths_code` `ths_code` VARCHAR(20) NOT NULL FIRST,
            #     CHANGE COLUMN `time` `time` DATE NOT NULL AFTER `ths_code`,
            #     ADD PRIMARY KEY (`ths_code`, `time`)""".format(table_name=table_name)
            primary_keys_str = "`" + "`, `".join(primary_keys) + "`"
            add_primary_key_str = f",\nADD PRIMARY KEY ({primary_keys_str})"
            chg_pk_str = f"ALTER TABLE `{table_name}` \n" + "\n".join(col_name_sql_str_list) + add_primary_key_str
            logger.info('创建表格 %s 及主键 %s 插入数据%s ' % (table_name, primary_keys, temp.shape))
            try:
                session.execute(text(chg_pk_str))  # FIXME table_name含有'):{字母}' 会出错 --> 目前只能函数之外先执行建表
            except IntegrityError as e:
                # except Exception as e: # 其他异常 调用table_drop_duplicate也解决不了，所以指定捕捉 IntegrityError
                logger.exception(
                    '建立 %s 表主键 %s 时出现异常 %s ，调用`table_drop_duplicate`进行重建以修复主键' % (table_name, primary_keys, str(e)))
                table_drop_duplicate(table_name, engine, primary_keys)
    else:
        logger.info('创建表格 %s 没有主键 %s 插入数据%s ' % (table_name, primary_keys, temp.shape))

    # 插入数据
    insert_count = df_insert_existed(df, dt_columns, dt_format, table_name, engine, ignore_none, chunksize, add_col)
    return insert_count


def _insert_a(df_dic_list, col_name_list,
              engine, table_name, ignore_none):
    """ 列名参数的方式 """
    # 如果行作为新记录被插入，则受影响的行为1；如果原有记录被更新，则受影响行为2；如果原有记录已存在，但是更新的值和原有值相同，则受影响行为0
    if ignore_none:
        generated_directive = ["`{0}`=IFNULL(VALUES(`{0}`), `{0}`)".format(col_name) for col_name in
                               col_name_list]
    else:
        generated_directive = ["`{0}`=VALUES(`{0}`)".format(col_name) for col_name in col_name_list]

    with with_db_session(engine) as session:
        sql_str = "insert into `{table_name}` ({col_names}) VALUES ({params}) ON DUPLICATE KEY UPDATE {update}".format(
            table_name=table_name,
            col_names="`" + "`,`".join([f'{x}' for x in col_name_list]) + "`",
            params=','.join([f':{x}' for x in col_name_list]),
            update=','.join(generated_directive),
        )
        rslt = session.execute(text(sql_str), params=df_dic_list)
        session.commit()
    return rslt.rowcount


def _insert_b(df_dic_list, col_name_list,
              engine, table_name, ignore_none):
    """ 位置参数的方式 """
    if ignore_none:
        generated_directive = ["`{0}`=IFNULL(VALUES(`{0}`), `{0}`)".format(col_name) for col_name in
                               col_name_list]
    else:
        generated_directive = ["`{0}`=VALUES(`{0}`)".format(col_name) for col_name in col_name_list]

    with with_db_session(engine) as session:
        col_name_list_num = dict(zip(col_name_list, range(1, len(col_name_list) + 1)))
        df_dic_list2 = []
        for d in df_dic_list:
            # 注意key转为str(数字)
            df_dic_list2.append({str(col_name_list_num[k]): v for k, v in d.items()})
        sql_str = "insert into `{table_name}` ({col_names}) VALUES ({params}) ON DUPLICATE KEY UPDATE {update}".format(
            table_name=table_name,
            col_names="`" + "`,`".join([f'{x}' for x in col_name_list_num.keys()]) + "`",
            params=','.join([f':{x}' for x in col_name_list_num.values()]),
            update=','.join(generated_directive),  # 字段名称含有 ):字母，参数化会出错-->见下方异常处理
        )
        rslt = session.execute(text(sql_str), params=df_dic_list2)
        session.commit()
    return rslt.rowcount


def _insert_c(df_dic_list, col_name_list,
              engine, table_name, ignore_none):
    for chunk in [5000, 1000, 200]:
        try:
            temp = _insert_c_chunk(df_dic_list, col_name_list,
                                   engine, table_name, ignore_none, chunk)
        except Exception as e:
            status, result = e, None
        else:
            status, result = None, temp
            break
    # 判断结果
    if isinstance(status, Exception):
        raise status
    else:
        return result


def _insert_c_chunk(df_dic_list, col_name_list,
                    engine, table_name, ignore_none, chunk):
    """ DataFrame拼接 on_duplicate """
    # 可能出现连接超时的问题 -->使用conn 参考 https://www.coder.work/article/385432 ; 还需要chunksize，设置任务了小一些才能解决
    with engine.connect() as conn:
        # sac = conn.begin()  # 不能开启事务；会导致后面pd.to_sql执行无报错，但实际没有存储进去
        conn.execute(text("show databases;")).fetchall()

        # rslt = 1
        # for i in range(len(df_dic_list)):
        #     try:
        #         pd.DataFrame(df_dic_list[i], index=[i]).to_sql(
        #             table_name, conn, index=False, if_exists='append')
        #     except IntegrityError:
        #         pass
        #     else:
        #         rslt += 1
        # return rslt

        def insert_on_duplicate(table, conn, keys, data_iter):
            # pd.to_sql加上method参数；参考 https://9to5answer.com/pandas-to_sql-fails-on-duplicate-primary-key
            from sqlalchemy.dialects.mysql import insert
            insert_stmt = insert(table.table).values(list(data_iter))
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(insert_stmt.inserted)
            # conn.execute(text(on_duplicate_key_stmt)) # 传入的是个Insert对象，不用text
            conn.execute(on_duplicate_key_stmt)

        if sqlalchemy.__version__ >= '2.0':
            raise RuntimeError(f'pandas.to_sql暂不支持sqlalchemy版本2.0')
        # 用清洗过的 df_dic_list，防止原始数据中np.nan pd.Timestamp存储不了
        pd.DataFrame(df_dic_list).to_sql(
            table_name, conn, index=False, if_exists='append',
            chunksize=min(chunk, len(df_dic_list)), method=insert_on_duplicate)

    return len(df_dic_list)


def df_insert_existed(df: pd.DataFrame, dt_columns: list, dt_format: str,
                      table_name: str, engine, ignore_none=True, chunksize=1024 * 128, add_col=False):
    """
    将 DataFrame 数据批量插入数据库。要求表格已存在
    先split_ilter整个df，再进行df_to_dict略快一点
    """
    logger = Logger(sys._getframe().f_code.co_name)
    has_table = repair_has_table(engine, table_name)
    if not has_table:
        raise RuntimeError('{} not in {}，需先创建或使用函数`df_insert` '.format(table_name, engine))
    # 检查是否增加新列
    if add_col:
        table_model = Table(table_name, MetaData(bind=engine), autoload=True)
        raw = set(table_model.columns.keys())
        tb_add = list(set(df.columns).difference(raw))
        if tb_add:
            dtype = df_types_sql(df[tb_add])
            logger.debug(f'已存在 {table_name} 增加新列{dtype}')
            for k, v in dtype.items():
                table_add_col(engine, table_name, k, str(v))

        # df_add = list(raw.difference(set(df.columns)))
        # if df_add:
        #     logger.debug(f'已存在{table_name} DataFrame增加新列{df_add}')
        #     for x in df_add:
        #         df[x] = None

    # 插入数据
    insert_count = 0
    for each in split_iter(range(len(df.index)), chunksize):
        each_df = df.iloc[each, :]
        df_dic_list, col_name_list = df_to_dict(each_df, dt_columns, dt_format)
        if not df_dic_list:
            continue
        # sqlalchemy表名字段名含有特殊字符):的问题 https://www.cnblogs.com/i-love-python/p/11593501.html -->使用pd.to_sql一般能解决
        res = _insert_c(df_dic_list, col_name_list, engine, table_name, ignore_none)  # fixme 使用不同的插入方法
        insert_count += res

    logger.info(f'任务表格 {table_name} 任务操作{insert_count} 任务数据{df.shape}')
    return insert_count


def table_get_keys(table_name, engine, table_schema):
    """获取table的主键
    :return: List["Tuple"] like [(主键名称，主键类型)]
    """
    sql_str = """SELECT column_name, column_type
        FROM information_schema.columns
        WHERE table_schema=:table_schema AND table_name=:table_name and COLUMN_KEY='PRI'"""
    with with_db_session(engine) as session:
        table = session.execute(text(sql_str), params={
            'table_schema': table_schema,
            'table_name': table_name,
        })
        key_list = [(col_name, col_type) for col_name, col_type in table.fetchall()]
        return key_list


def table_get_columns(table_name, engine, schema) -> List["Tuple"]:
    """获取table的字段信息。
    :return: List["Tuple"] like [(列名称，列类型，是否主键bool)]
    """
    sql_str = """SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_KEY
        FROM information_schema.columns
        WHERE table_schema=:table_schema AND table_name=:table_name"""
    with with_db_session(engine) as session:
        table = session.execute(text(sql_str), params={
            'table_schema': schema,
            'table_name': table_name,
        })
        key_list = [(col_name, col_type, col_key == 'PRI') for col_name, col_type, col_key in table.fetchall()]
        return key_list


def table_drop_duplicate_keep(table_name, engine, schema, columns: list, keep_by: str = None, keep_m: str = 'min'):
    """
    根据`指定列` `留存规则` 删除重复数据。
    1、关于keep_by，为None将临时创建SERIAL的列用于判断数据保留
    2、使用表内inner join适用于数据量不大的表处理
    :param table_name:
    :param engine:
    :param schema:
    :param columns:
    :param keep_by:
    :param keep_m:
    :return:
    """
    all_col = table_get_columns(table_name, engine, schema)
    all_col = [x[0] for x in all_col]

    if not columns:
        columns = set(all_col)
    else:
        columns = set(columns)
    assert columns.issubset(set(all_col))
    columns = list(columns)
    columns.sort()
    # keep_by不传入时处理,先判断是否有自增列
    if not keep_by:  # 临时自增列
        keep_by = hashlib.md5(",".join(columns).encode('utf-8')).hexdigest()
        add_sql = f""" ALTER TABLE `{table_name}` ADD COLUMN `{keep_by}` SERIAL """
        del_sql = f""" ALTER TABLE `{table_name}` DROP COLUMN `{keep_by}`"""
    else:
        assert keep_by in [all_col]
        add_sql = ''
        del_sql = ''

    if keep_m.lower() == 'max':
        c_str = f" a.`{keep_by}` < b.`{keep_by}` " + " ".join([f"AND a.`{x}` <=> b.`{x}` " for x in columns])
    elif keep_m.lower() == 'min':
        c_str = f" a.`{keep_by}` > b.`{keep_by}` " + " ".join([f"AND a.`{x}` <=> b.`{x}` " for x in columns])
    else:
        raise ValueError(f"arg keep_m should in ['min','max'] got{keep_m}")
    dup_sql = f"""DELETE a FROM `{table_name}` a
    INNER JOIN `{table_name}` b
    WHERE {c_str}
    """

    with with_db_session(engine) as session:
        if add_sql:
            try:
                session.execute(text(add_sql))
            except:
                pass

        crud = session.execute(text(dup_sql))

        if del_sql:
            try:
                session.execute(text(del_sql))
            except:
                pass
        return crud


def table_drop_duplicate_rows(table_name, engine, schema, columns: list):
    """
    根据`指定列`删除重复数据。注意：
    1、execute中有删表操作，多进程下可能出现判断表格exsit的异常
    :param table_name:
    :param engine:
    :param schema:
    :param columns:
    :return:
    """
    # 参数检查
    all_col = table_get_columns(table_name, engine, schema)
    all_col = [x[0] for x in all_col]
    assert set(columns).issubset(set(all_col))

    group_str = "`" + "`, `".join(columns) + "`"
    table_name_copy = table_name + '_copy'

    drop_sql = f"""DROP TABLE IF EXISTS  `{table_name_copy}` """
    create_sql = f"""CREATE TABLE `{table_name_copy}` AS SELECT * FROM `{table_name}` GROUP BY {group_str}
    """
    drop_raw_sql = f""" DROP TABLE `{table_name}` """
    rename_sql = f""" RENAME TABLE {table_name_copy} TO `{table_name}` """
    with with_db_session(engine) as session:
        crud = session.execute(text(drop_sql))
        crud_ = session.execute(text(create_sql))
        crud = session.execute(text(drop_raw_sql))
        crud = session.execute(text(rename_sql))
        session.commit()
    return crud_


def table_add_col(engine, table_name, col_name, col_type_str: str):
    """
    检查当前数据库是否存在 db_col_name 列，如果不存在则添加该列
    :param engine:
    :param table_name:
    :param col_name:
    :param col_type_str: DOUBLE, VARCHAR(20), INTEGER, etc.
    :return:
    """
    logger = Logger(sys._getframe().f_code.co_name)

    metadata = MetaData(bind=engine)
    table_model = Table(table_name, metadata, autoload=True)
    if col_name not in table_model.columns:
        # 该语句无法自动更新数据库表结构，因此该方案放弃
        # table_model.append_column(Column(col_name, dtype))
        after_col_name = table_model.columns.keys()[-1]
        add_col_sql_str = "ALTER TABLE `{0}` ADD COLUMN `{1}` {2} NULL AFTER `{3}`".format(
            table_name, col_name, col_type_str, after_col_name
        )
        with with_db_session(engine) as session:
            session.execute(text(add_col_sql_str))
            session.commit()
        logger.info('%s 添加 %s [%s] 列成功' % (table_name, col_name, col_type_str))


def table_drop_duplicate(table_name, engine, primary_key=None):
    """
    根据 `主键` 删除重复数据。
    做法：新建表并建立主键->将原有表数据导入到新表->删除旧表->重命名新表
    :param table_name:
    :param engine:
    :param primary_key:
    :return:
    """
    logger = Logger(sys._getframe().f_code.co_name)
    has_table = repair_has_table(engine, table_name)
    if not has_table:
        return
    table_name_bak = f"{table_name}_bak"
    has_bak = repair_has_table(engine, table_name_bak)
    with with_db_session(engine) as session:
        if has_bak:
            sql_str = f"drop table {table_name_bak}"
            session.execute(text(sql_str))
            logger.debug('删除现有 %s 表' % table_name_bak)

        sql_str = f"create table {table_name_bak} like `{table_name}` "
        session.execute(text(sql_str))
        logger.debug('创建 %s 表' % table_name_bak)

        if primary_key is not None:
            key_str = ', '.join(primary_key)
            sql_str = f"""alter table {table_name_bak}
                add constraint {table_name}_pk
                primary key ({key_str})"""
            session.execute(text(sql_str))
            logger.debug('创建 %s 表 主键 %s：' % (table_name_bak, key_str))

        sql_str = f"replace into {table_name_bak} select * from `{table_name}` "
        session.execute(text(sql_str))
        session.commit()
        logger.debug('插入数据 %s -> %s' % (table_name, table_name_bak))
        sql_str = f"drop table `{table_name}`"
        session.execute(text(sql_str))
        logger.debug('删除 %s 表' % table_name)
        sql_str = f"rename table {table_name_bak} to `{table_name}` "
        session.execute(text(sql_str))
        logger.debug('重命名 %s --> %s' % (table_name_bak, table_name))

    logger.info('完成主键去重 %s' % (table_name))
