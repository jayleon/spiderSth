#!/usr/bin/python
# coding:utf-8
# 部署命令：
# scp longtail_mapper.py root@192.168.0.15:/data/leon/python/longtailmr/
# su hdfs
# hadoop jar /usr/lib/hadoop/hadoop-streaming.jar -D mapred.job.name="longtail_1" \
# -file /data/leon/python/longtailmr/longtail_mapper.py -mapper /data/leon/python/longtailmr/longtail_mapper.py \
# -file /data/leon/python/longtailmr/longtail_reducer.py -reducer /data/leon/python/longtailmr/longtail_reducer.py \
# -input /user/leon/mrout_6000001-6001000/* -output /user/leon/mrout_2_6000001-6001000

import sys

for line in sys.stdin:
    line = line.strip()
    word = line.split('\t', 1)[0]
    count = line.split('\t', 1)[1]
    if word:
        print("{0}\t{1}".format("price",count))