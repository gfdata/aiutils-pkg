# -*- coding: utf-8 -*-
# @time: 2022/11/17 16:40
# @Author：lhf
# ----------------------
import numpy as np
import pandas as pd
from pyecharts.charts import Bar
from pyecharts import options as opts


def plot_bar_stack(df: pd.DataFrame,
                   width='800px', height='450px'):
    """
    柱状堆积图
    :return:
    """
    temp = df
    # 数据检查
    temp = df.sort_index()
    assert isinstance(temp.index, pd.DatetimeIndex), f'df要求index为时间索引'

    obj = Bar(init_opts=opts.InitOpts(width=width, height=height)).add_xaxis(
        [x.strftime('%Y-%m-%d') for x in temp.index])
    # 添加y值
    for i in range(0, len(temp.columns)):
        col = temp.columns[i]
        obj.add_yaxis(col, [x for x in temp[col]], stack="stack1")  # bar堆积
    # 其他设置
    obj.set_global_opts(
        legend_opts=opts.LegendOpts(is_show=True, type_='plain', pos_left='center'),
        yaxis_opts=opts.AxisOpts(
            type_='value', is_scale=True,  # 自适应的y轴刻度，需要type_='value'
            splitline_opts=opts.SplitLineOpts(is_show=True),  # 网格线
        ),
        # 缩放可设置多种
        datazoom_opts=[opts.DataZoomOpts(is_show=True), opts.DataZoomOpts(type_="inside")],
        #     toolbox_opts=opts.ToolboxOpts(is_show=True),
        # 提示数据，十字光标
        tooltip_opts=opts.TooltipOpts(is_show=True, trigger_on="mousemove | click", axis_pointer_type='cross'),
    )
    obj.set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    return obj


def plot_distribute(data, step=0.05,
                    width='800px', height='450px'):
    """
    频率分布直方图
    :param data: 例如收益率数据
    :param step:
    :return:
    """
    bin_list = np.arange(data.min(), data.max(), 0.05)
    temp = pd.cut(data, bin_list).value_counts().sort_index()
    bar = (Bar(init_opts=opts.InitOpts(width=width, height=height))
        .add_xaxis([str(x) for x in temp.index])
        .add_yaxis('频率', [float(x) for x in temp.values])
        .set_global_opts(
        # 缩放可设置多种
        datazoom_opts=[opts.DataZoomOpts(is_show=True), opts.DataZoomOpts(type_="inside")],
        # toolbox_opts=opts.ToolboxOpts(),  # 工具栏
    )
    )
    return bar
