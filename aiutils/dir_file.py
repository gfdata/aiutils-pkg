"""
目录和文件操作
"""
import os


def print_dir(rootDir):
    """
    按目录结构，递归到最大深度

    E:\TEST\A
    E:\TEST\A\A-A
    E:\TEST\A\A-A\A-A-A.txt
    E:\TEST\A\A-B.txt
    E:\TEST\A\A-C
    E:\TEST\A\A-C\A-B-A.txt
    E:\TEST\A\A-D.txt
    E:\TEST\B.txt
    E:\TEST\C
    E:\TEST\C\C-A.txt
    E:\TEST\C\C-B.txt
    E:\TEST\D.txt
    E:\TEST\E
    """
    for lists in os.listdir(rootDir):
        path = os.path.join(rootDir, lists)
        print(path)
        if os.path.isdir(path):
            print_dir(path)


def print_dir_1(rootDir, level=1):
    """
    E:\TEST
    │--A
    │  │--A-A
    │  │  │--A-A-A.txt
    │  │--A-B.txt
    │  │--A-C
    │  │  │--A-B-A.txt
    │  │--A-D.txt
    │--B.txt
    │--C
    │  │--C-A.txt
    │  │--C-B.txt
    │--D.txt
    │--E
    """
    if level == 1:
        print(rootDir)
    for lists in os.listdir(rootDir):
        path = os.path.join(rootDir, lists)
        print('│  ' * (level - 1) + '│--' + lists)
        if os.path.isdir(path):
            print_dir_1(path, level + 1)


def print_dir_2(rootDir):
    """
    先文件夹后文件，逐级深入

    E:\TEST\A
    E:\TEST\C
    E:\TEST\E
    E:\TEST\B.txt
    E:\TEST\D.txt
    E:\TEST\A\A-A
    E:\TEST\A\A-C
    E:\TEST\A\A-B.txt
    E:\TEST\A\A-D.txt
    E:\TEST\A\A-A\A-A-A.txt
    E:\TEST\A\A-C\A-B-A.txt
    E:\TEST\C\C-A.txt
    E:\TEST\C\C-B.txt

    """

    list_dirs = os.walk(rootDir)
    for root, dirs, files in list_dirs:
        for d in dirs:
            print(os.path.join(root, d))
        for f in files:
            print(os.path.join(root, f))
