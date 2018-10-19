#!/usr/bin/python
# coding:utf-8
# 部署命令：
# scp longtail_reducer.py root@127.0.0.1:/data/leon/python/longtailmr/

import sys

simple_price = 0
max_price = 0
min_price = 0

for line in sys.stdin:
    word = line.split('\t',1)[0]
    count = line.split('\t',1)[1]
    count = float(count)
    if count > max_price:
        max_price = count
    if count < min_price:
        min_price = count

if max_price:
    print("{0}\t{1}".format("max_price",max_price))

if min_price:
    print("{0}\t{1}".format("min_price", min_price))