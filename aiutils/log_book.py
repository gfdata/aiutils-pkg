# -*- coding: utf-8 -*-
"""
@time: 2021/10/19 16:04
@file: log_book.py

使用logbook库
"""

import os
from logbook import Logger, StderrHandler, TimedRotatingFileHandler
from logbook.more import ColorizedStderrHandler

AI_UTILS_LOGGER = Logger('aiutils')


def user_handler_log_formatter(record, handler):
    log = "[{dt}][{level}][{filename}][{func_name}][{lineno}] {msg}".format(
        dt=record.time,
        level=record.level_name,  # 日志等级
        filename=os.path.split(record.filename)[-1],  # 文件名
        func_name=record.func_name,  # 函数名
        lineno=record.lineno,  # 行号
        msg=record.message,  # 日志内容
    )
    return log


def init_file_logger(log_dir, filename, level):
    # 日志输出
    log_dir = os.path.join(log_dir, 'logbook')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    user_file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, '{}.log'.format(filename)), date_format='%Y%m%d', bubble=True, level=level)
    user_file_handler.formatter = user_handler_log_formatter

    user_file_handler.push_application()


def init_stdout_logger(level='DEBUG', color=True):
    # 控制台输出
    if color:
        ColorizedStderrHandler(level=level, bubble=True).push_application()
    else:
        StderrHandler(level=level, bubble=True).push_application()
