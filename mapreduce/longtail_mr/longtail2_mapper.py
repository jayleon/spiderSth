#!/usr/bin/python
# coding:utf-8
# 部署命令：
# scp longtail2_mapper.py root@127.0.0.1:/data/leon/python/longtailmr/
# su hdfs
# hadoop jar /usr/lib/hadoop/hadoop-streaming.jar -D mapred.job.name="longtail_2" \
# -file /data/leon/python/longtailmr/longtail2_mapper.py -mapper /data/leon/python/longtailmr/longtail2_mapper.py \
# -file /data/leon/python/longtailmr/longtail2_reducer.py -reducer /data/leon/python/longtailmr/longtail2_reducer.py \
# -input /data/leon/mrout_6000001-6001000/* -output /data/leon/mrout_3_6000001-6001000

import sys
import numpy as np

def main():
    for line in sys.stdin:
        line = line.strip()
        word = line.split('\t', 1)[0]
        count = line.split('\t', 1)[1]
        if word:
            count = float(count)
            # O(1)
            n=100
            bin = int((count + 0.1) * n)
            if(bin<0):
                bin=0
            if(bin>2*n):
                bin=2*n
            print("{0}\t{1}".format(bin, 1))

if __name__ == "__main__":
    main()
    # print list(np.arange(-10, 10, 0.1))
