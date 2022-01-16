# -*- coding: utf-8 -*-
# @time: 2021/12/24 16:14
# @Author：lhf

import os


def get_version():
    file = os.path.join(
        os.path.dirname(__file__),
        "VERSIONLOG.md"
    )
    version = '0.0.0'
    with open(file, encoding='utf8') as f:
        while True:
            aline = f.readline()
            if aline == '':
                break

            version = aline.strip()
            if version:
                break

    return version


__version__ = get_version()
