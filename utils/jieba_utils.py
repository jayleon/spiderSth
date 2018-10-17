#!/usr/bin/python
# coding:utf-8
# 结巴分词工具类

import jieba
import jieba.posseg as pseg

# 加载自定义词典
jieba.load_userdict("./userdict.txt")

class jiebaUtil:

    def cutCont(self, content):
        result = jieba.cut(content)
        return result

    # 词性标注也叫词类标注。POS tagging是part-of-speech tagging的缩写
    def psegCont(self, content):
        result = pseg.cut(content)
        return result

if __name__ == "__main__":
    ju = jiebaUtil()

    words = ju.cutCont("这是一个伸手不见五指的黑夜。我叫孙悟空，我爱北京，我爱Python和C++。")
    for word in words:
        print("%s" % word)

    print("-------------------我是分割线--------------------")

    words = ju.psegCont("伸手不见五指的黑夜。我叫孙悟空，我爱北京，我爱Python和C++。")
    for word,flag in words:
        print("%s  %s"%(word, flag))
