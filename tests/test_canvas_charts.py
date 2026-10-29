"""自绘图表测试：三种图表能在隐藏窗口里构建并绘制。"""

import tkinter as tk

import pytest


@pytest.fixture(scope="module")
def root_csy():
    """创建隐藏根窗口；无图形界面时跳过。"""
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("当前环境没有可用的图形界面")
    root.withdraw()
    yield root
    root.destroy()


def test_donut_chart_draws_csy(root_csy):
    """环形图应画出扇形与图例。"""
    from pathway.canvas_charts import DonutChart

    chart = DonutChart(root_csy, [("企业单位", 86.4), ("自由职业", 8.5), ("事业单位", 1.5)],
                       title="单位性质占比")
    chart.pack(fill="x")
    chart.redraw_csy()
    root_csy.update()
    assert chart.find_all()
    chart.destroy()


def test_bar_chart_draws_axes_and_bars_csy(root_csy):
    """柱状图应画出坐标轴、刻度与柱子。"""
    from pathway.canvas_charts import BarChart

    chart = BarChart(root_csy, ["2021 本科", "2021 专科", "2023 专科"], [4.38, 85.52, 81.92],
                     xlabel="届别与学历", ylabel="升学率（%）", title="升学率对比")
    chart.pack(fill="x")
    chart.redraw_csy()
    root_csy.update()
    texts = [chart.itemcget(item, "text") for item in chart.find_all()
             if chart.type(item) == "text"]
    assert "届别与学历" in texts
    assert "升学率（%）" in texts
    chart.destroy()


def test_line_chart_draws_points_csy(root_csy):
    """折线图应画出折线与数据点。"""
    from pathway.canvas_charts import LineChart

    chart = LineChart(root_csy, ["2022", "2023", "2024", "2025", "2026"],
                      [273, 273, 273, 260, 264],
                      xlabel="年份", ylabel="总分线（分）", title="工学国家线")
    chart.pack(fill="x")
    chart.redraw_csy()
    root_csy.update()
    ovals = [item for item in chart.find_all() if chart.type(item) == "oval"]
    assert len(ovals) >= 5
    chart.destroy()
