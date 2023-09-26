# -*- coding: utf-8 -*-
# @time: 2022/11/17 17:18
# @Author：lhf
# ----------------------
import pandas as pd

from pyecharts.charts import Line, Grid
from pyecharts import options as opts


def plot_multi_line(df: pd.DataFrame, col_enhance=None,
                    width='900px', height='450px'):
    """ 绘制多条数据的折线图 """
    from pyecharts.charts import Line
    from pyecharts import options as opts

    # 数据检查
    temp = df.sort_index()
    assert isinstance(temp.index, pd.DatetimeIndex), f'df要求index为时间索引'

    # 图形对象
    line = Line(init_opts=opts.InitOpts(width=width, height=height)).add_xaxis(
        [x.strftime('%Y-%m-%d') for x in temp.index])
    # 添加y值
    for i in range(0, len(temp.columns)):
        col = temp.columns[i]
        if col == col_enhance:
            line.add_yaxis(col, [x for x in temp[col]], linestyle_opts=opts.LineStyleOpts(width=2, color='red'))
        else:
            line.add_yaxis(col, [x for x in temp[col]],
                           is_symbol_show=False,  # 去掉圆圈标识
                           )
    # 其他设置
    line.set_global_opts(
        legend_opts=opts.LegendOpts(is_show=True, type_='plain', pos_left='center'),
        yaxis_opts=opts.AxisOpts(
            type_='value', is_scale=True,  # 自适应的y轴刻度，需要type_='value'
            splitline_opts=opts.SplitLineOpts(is_show=True),  # 网格线
        ),
        # 缩放可设置多种
        datazoom_opts=[opts.DataZoomOpts(is_show=True), opts.DataZoomOpts(type_="inside")],
        # 提示数据，十字光标
        tooltip_opts=opts.TooltipOpts(is_show=True, trigger_on="mousemove | click", axis_pointer_type='cross'),
    )
    line.set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    return line


def plot_two_grid(dfa: pd.DataFrame, dfb: pd.DataFrame,
                  dfa_text: pd.Series = None, dfb_text: pd.Series = None,
                  strftime='%Y-%m-%d', gridw='900px', gridh='450px'):
    """
    两个图表区域，共用一个x轴联动展示
    :param dfa: 上方区域的数据
    :param dfb: 下方区域的数据
    :param dfa_text:
    :param dfb_text:
    :param strftime:
    :param gridw:
    :param gridh:
    :return:
    """
    assert isinstance(dfa.index, pd.DatetimeIndex), f'要求为时间索引'
    assert isinstance(dfb.index, pd.DatetimeIndex), f'要求为时间索引'
    # 图形对象
    dfup = dfa.sort_index(ascending=True)
    linup = Line().add_xaxis([x.strftime(strftime) for x in dfup.index])
    # 添加y值
    for i in range(0, len(dfup.columns)):
        col = dfup.columns[i]
        if i == 0:
            linup.add_yaxis(col, list(dfup[col]), linestyle_opts=opts.LineStyleOpts(width=2, color='red'),
                            is_symbol_show=False)
        else:
            linup.add_yaxis(col, list(dfup[col]), is_symbol_show=False)  # 去掉圆圈标识
    # 其他设置
    linup.set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    linup.set_global_opts(
        legend_opts=opts.LegendOpts(is_show=True, type_='plain', pos_left='center'),
        axispointer_opts=opts.AxisPointerOpts(
            is_show=True, link=[{"xAxisIndex": "all"}]
        ),
        yaxis_opts=opts.AxisOpts(
            type_='value', is_scale=True,  # 自适应的y轴刻度，需要type_='value'
            splitline_opts=opts.SplitLineOpts(is_show=True),  # 网格线
        ),
        # 缩放控制两个x轴
        datazoom_opts=[opts.DataZoomOpts(type_='inside', start_value=50, end_value=100, xaxis_index=[0, 1]),
                       opts.DataZoomOpts(is_show=True, start_value=0, end_value=100, orient='vertical')
                       ],
        # 提示数据，十字光标
        tooltip_opts=opts.TooltipOpts(is_show=True, trigger_on="mousemove | click", axis_pointer_type='cross'),
    )
    linup.set_series_opts(label_opts=opts.LabelOpts(is_show=False))

    # 第二个图表区
    dfdw = dfb.sort_index(ascending=True)
    lindw = Line().add_xaxis([x.strftime(strftime) for x in dfdw.index])
    for i in range(0, len(dfdw.columns)):
        col = dfdw.columns[i]
        if i == 0:
            lindw.add_yaxis(col, list(dfdw[col]), linestyle_opts=opts.LineStyleOpts(width=2, color='red'))
        else:
            lindw.add_yaxis(col, list(dfdw[col]), is_symbol_show=False)  # 去掉圆圈标识
    lindw.set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    lindw.set_global_opts(
        legend_opts=opts.LegendOpts(is_show=True, type_='plain', pos_top="60%"),
        axispointer_opts=opts.AxisPointerOpts(
            is_show=True, link=[{"xAxisIndex": "all"}]
        ),
        yaxis_opts=opts.AxisOpts(
            splitline_opts=opts.SplitLineOpts(is_show=True),  # 网格线
        ),
    )

    # 放在一个grid
    grid = (Grid(init_opts=opts.InitOpts(width=gridw, height=gridh))
            .add(linup, grid_opts=opts.GridOpts(pos_bottom="60%"))
            .add(lindw, grid_opts=opts.GridOpts(pos_top="60%"))
            )
    return grid


def plot_double_y(linea: pd.Series, lineb: pd.Series, strftime='%Y-%m-%d',
                  width='900px', height='450px'):
    """
    双y轴画图，共用一个x轴
    :param linea:
    :param lineb:
    :param strftime:
    :return:
    """
    if not linea.name:
        namea = 'lineA'
    else:
        namea = linea.name
    if not lineb.name:
        nameb = 'lineB'
    else:
        nameb = lineb.name
    total = pd.DataFrame({namea: linea, nameb: lineb})
    assert isinstance(total.index, pd.DatetimeIndex), f'要求为时间索引'

    line_left = (
        Line(init_opts=opts.InitOpts(width=width, height=height))
            # Line(init_opts=opts.InitOpts(theme=ThemeType.DARK))  # 选择主题
            .add_xaxis(list(total.index.strftime(strftime)))
            .add_yaxis(namea, total[namea], linestyle_opts=opts.LineStyleOpts(width=2))
            # 增添y轴才能双坐标
            .extend_axis(yaxis=opts.AxisOpts(axislabel_opts=opts.LabelOpts(formatter="{value}%"), interval=10))
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(
            # 缩放可设置多种
            datazoom_opts=[opts.DataZoomOpts(is_show=True), opts.DataZoomOpts(type_="inside")],
            # 提示数据，十字光标
            tooltip_opts=opts.TooltipOpts(
                is_show=True, trigger_on="mousemove | click", axis_pointer_type='cross')
        )
    )

    line_right = (
        Line()
            .add_xaxis(list(total.index.strftime(strftime)))
            .add_yaxis(nameb, total[nameb] * 100, yaxis_index=1)  # 副坐标轴
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    )
    # overlap组合到一起
    line_left.overlap(line_right)
    return line_left
