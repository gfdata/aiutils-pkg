# -*- coding: utf-8 -*-
# @time: 2022/11/17 16:40
# @Author：lhf
# ----------------------
import numpy as np
import pandas as pd
from pyecharts.charts import Bar
from pyecharts import options as opts


def plot_distribute(data, step=0.05):
    """
    频率分布直方图
    :param data: 例如收益率数据
    :param step:
    :return:
    """
    bin_list = np.arange(data.min(), data.max(), 0.05)
    temp = pd.cut(data, bin_list).value_counts().sort_index()
    bar = (Bar()
        .add_xaxis([str(x) for x in temp.index])
        .add_yaxis('频率', [float(x) for x in temp.values])
        .set_global_opts(
        # 缩放可设置多种
        datazoom_opts=[opts.DataZoomOpts(is_show=True), opts.DataZoomOpts(type_="inside")],
        # toolbox_opts=opts.ToolboxOpts(),  # 工具栏
    )
    )
    return bar
