#!/usr/bin/python
# coding:utf-8

"""
@Time: 2018/11/1 下午7:21
@Author: leon
@File: PythonMagick_demo.py
@Software: PyCharm Community Edition
"""
import PythonMagick;
from PyPDF2 import PdfFileReader;

C_RESOURCE_FILE = r'C:\workspace\python\converter\resource';
C_PDFNAME = r'6p.pdf';
C_JPGNAME = r'6p%s.jpg';

input_stream = file(C_RESOURCE_FILE + '\\' + C_PDFNAME, 'rb');
pdf_input = PdfFileReader(input_stream, strict=False);  # 错误1
page_count = pdf_input.getNumPages();

img = PythonMagick.Image()  # empty object first
img.density('300');  # set the density for reading (DPI); must be as a string

for i in range(page_count):
    try:
        img.read(C_RESOURCE_FILE + '\\' + C_PDFNAME + ('[%s]' % i));  # 分页读取 PDF
        imgCustRes = PythonMagick.Image(img);  # make a copy
        imgCustRes.sample('x1600');
        imgCustRes.write(C_RESOURCE_FILE + '\\' + (C_JPGNAME % i));
    except Exception, e:
        print e;
        pass;

print 'done';
if __name__ == "__main__":
    print ""