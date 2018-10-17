#!/usr/bin/env python
# coding:utf-8
# 坐标转换工具类

import math

x_pi = 3.14159265358979324 * 3000.0 / 180.0

# 坐标转换，腾讯地图转换成百度地图坐标;lat 腾讯纬度 ;lon 腾讯经度 ;返回结果：经度,纬度
def map_tx2bd(lat,lon):
    x = lon
    y = lat
    z = math.sqrt(x * x + y * y) + 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) + 0.000003 * math.cos(x * x_pi)
    bd_lon = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006

    print "bd_lat:%s" % bd_lat
    print "bd_lon:%s" % bd_lon
    return '%s,%s' % (bd_lon,bd_lat)

# 坐标转换，百度地图坐标转换成腾讯地图坐标;lat  百度坐标纬度;lon  百度坐标经度;返回结果：纬度,经度
def map_bd2tx(lat, lon):
        x = lon - 0.0065
        y = lat - 0.006
        z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
        theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
        tx_lon = z * math.cos(theta)
        tx_lat = z * math.sin(theta)
        return '%s,%s' % (tx_lat, tx_lon)

if __name__ == "__main__":

    print map_tx2bd(39.905288,116.265137)
    print map_bd2tx(39.911520729,116.271550922)