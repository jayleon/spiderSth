#!/usr/bin/python
# coding:utf-8
# 部署命令：
# scp longtail_reducer.py root@192.168.0.15:/data/leon/python/longtailmr/

import sys
from itertools import groupby
from operator import itemgetter

def read_mapper_output(file, separator = '\t'):
    for line in file:
        yield line.split(separator, 1)

def main(separator = '\t'):
    data = read_mapper_output(sys.stdin, separator = separator)
    list1 = []
    list2 = []
    map1 = {}
    for current_word, group in groupby(data, itemgetter(0)):
        try:
            total_count = sum(float(count) for current_word, count in group)
            map1[float(current_word)] = total_count
        except Exception:
            pass
    items = map1.items()
    items.sort()
    for key, value in items:
        list1.append(key)
        list2.append(value)
    print "list1%s%s" % (separator, list1)
    print "list2%s%s" % (separator, list2)


if __name__ == "__main__":

    main()
