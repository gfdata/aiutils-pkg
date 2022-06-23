1.3.1

* aiutils.sql.df_insert_existed

修复特殊情况下的报错（列名含有:与sqlalchemy传参占位符冲突）

* aiutils.code.unique_exchange.ExchangeMap

增加通用接口的交易所缩写映射（如wind vnpy）

# 1.3.0

openpyxl_tools编写excel

rqutils 模块

* data proxy 非回测环境直接使用
* run_func 结果的存储
* 回测环境中，交易下单封装

# 1.2.2

futureClassify 模块

* 修复pandas读取xlsx的依赖包

code 模块

* 依赖futureClassify，做品种字母与交易所的映射

# 1.2.1

增加futureClassify【期货分类数据】

* 新品种上市时，需要手动维护`future_classify.xlsx`(更新频率较低)
* code模块，内部变量 _ud_exchange_commodity 依赖此表进行更新维护

# 1.2.0

调整trans模块：数据打包传输

添加bind模块：通过赋值 BindTradingCalendar，方便调用多种交易日判断函数

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