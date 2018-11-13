#!/usr/bin/python
# coding:utf-8

"""
@Time: 2018/11/2 上午10:04
@Author: leon
@File: tesseract_demo.py
@Software: PyCharm Community Edition
@参考文献：https://blog.csdn.net/u010670689/article/details/78374623/
"""
import pytesseract
from PIL import Image, ImageEnhance

image = Image.open('./easy_img/changxiangsi.jpeg')
# 增强图片的显示效果，或者将其转换为黑白的，这样可以使其识别率提升不少
enhancer = ImageEnhance.Contrast(image)
image2 = enhancer.enhance(4)
# psm提高识别率
# 0 定向脚本监测（OSD）
# 1 使用OSD自动分页
# 2 自动分页，但是不使用OSD或OCR（Optical Character Recognition，光学字符识别）
# 3 全自动分页，但是没有使用OSD（默认）
# 4 假设可变大小的一个文本列。
# 5 假设垂直对齐文本的单个统一块。
# 6 假设一个统一的文本块。
# 7 将图像视为单个文本行。
# 8 将图像视为单个词。
# 9 将图像视为圆中的单个词。
# 10 将图像视为单个字符。
code = pytesseract.image_to_string(image, lang='chi_sim', config='--psm 6')
print code

if __name__ == "__main__":
    print ""