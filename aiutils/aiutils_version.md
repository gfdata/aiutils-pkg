1.5.1

## aiuitls.optMysql改名aiutils.opt_mysql

# 1.5.0

## aiutils.code.exchange_map.MapTotal

作为常用的映射关系使用，参考 aiutils/code/by_common.py:71

## aiutils.code

* 重构内部exchange写法

## aiutils.code.by_common.code_by_common

* 参数exchange_map，默认值为空

## aiutils.rqutils.check

* get_phase_datetime 获取运行状态及时间

# 1.4.2

## aiutils.rqutils.strategy_identify.generate_id_vars

* 修改生成规则

## aiutils.dt_convert.split_dates_more

* 增加参数，是否扩展结束日期

## aiutils.sql

* 表名字段名含有特殊字符组合 "):{字母}" sqlalchemy执行异常的问题解决：

- 一般先建表，例如手动建表或type动态建表
- 插入数据，利用df.to_sql增加method方法防止duplicate key异常

# 1.4.1

## aiutils.random_str

* 新增，生成随机字符串的函数

# 1.4.0

* 增加交易所常量 GFEX； future_classify增加SI

# 1.3.2

## aiutils.dt_convert

* 增加 split_dates系列函数

# 1.3.1

## aiutils.sql

* df_insert_existed 修复特殊情况下的报错（列名含有:与sqlalchemy传参占位符冲突）

## aiutils.code

* unique_exchange.ExchangeMap 增加通用接口的交易所缩写映射（如wind vnpy）

# 1.3.0

## 新增 aiutils.openpyxl_tools

常用的excel写入

## 新增 aiutils.rqutils

* data proxy 非回测环境直接使用
* run_func 结果的存储
* 回测环境中，交易下单封装

# 1.2.2

## aiutils.futureClassify

* 修复pandas读取xlsx的依赖包

## aiutils.code

* 依赖futureClassify，做品种字母与交易所的映射

# 1.2.1

## 新增 aiutils.futureClassify

期货分类数据

* 新品种上市时，需要手动维护`future_classify.xlsx`(更新频率较低)
* code模块，内部变量 _ud_exchange_commodity 依赖此表进行更新维护

# 1.2.0

## aiutils.trans

数据打包传输

## 新增 aiutils.bind

通过赋值 BindTradingCalendar，方便调用多种交易日判断函数

# 1.1.3

enum_obj.py，实现Enum对象的动态扩展

dir_file.py，目录的不同遍历方式

# 1.1.2

section边界规则，改为按所属交易所来获取

# 1.1.1

添加section交易时段的字符串化，以及判断函数

str_datetime:包含日期部分，适用于历史行情数据过滤

str_time:只含时间部分，适用于实时行情快速过滤（一是没有考虑历史上的调整；二是没有考虑节假日前后，夜盘时段有时候没有，此时起不到过滤作用；三是退市合约可能为空）

# 1.1.0

升级code模块，合约转换的规则；

# 1.0.0

迁移大部分功能