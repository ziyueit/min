#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os


__author__ = 'Ma'
import jieba
from operator import itemgetter


idf_freq = {}
path = os.path.join(os.path.dirname(__file__), "dict/idf.txt"),
content = open('dict/idf.txt', 'rb').read().decode('utf-8')
lines = content.split('\n')
for line in lines:
    word, freq = line.split(' ')
    idf_freq[word] = float(freq)

median_idf = sorted(idf_freq.values())[len(idf_freq) / 2]
stop_words = set([
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'can',
    'for', 'from', 'have', 'if', 'in', 'is', 'it', 'may',
    'not', 'of', 'on', 'or', 'tbd', 'that', 'the', 'this',
    'to', 'us', 'we', 'when', 'will', 'with', 'yet',
    'you', 'your', u'的', u'了', u'和', u'呢', u'啊', u'哦', u'恩', u'嗯', u'吧'
])


def load_idf():
    """
    加载 idf 字典
    """
    pass


def extract_tags(content, num=20):
    """
    提取关键字
    """
    seg_list = jieba.cut(content)
    seg_list = get_weight(seg_list, True)
    seg_list = seg_list[:num]
    tags = [a[1] for a in seg_list]
    return tags


def get_weight(seg_list, sort=False):
    """
    获取权重，返回值 已经排序
    """
    freq = {}
    for w in seg_list:

        if len(w.strip()) < 2: continue  # 判断关键字长度
        if w.lower() in stop_words: continue  # 是否是停用词
        freq[w] = freq.get(w, 0.0) + 1.0

    total = sum(freq.values())
    freq = [(k, v / total) for k, v in freq.iteritems()]

    tf_idf_list = [[v * idf_freq.get(k, median_idf), k] for k, v in freq]  # 计算权重
    if sort:
        tf_idf_list = sorted(tf_idf_list, reverse=True)
    return tf_idf_list


def cut_clause(content, punctuation=True):
    """
    中文分句
    \u4e00-\u9fa5
    """
    content = list(content)
    cut_list = list("[。，,！……!《》<>\"':：？\?、\|“”‘’；]{}（）{}【】()｛｝（）：？！。，;、~——+％%`:“”＂'‘\n\r".decode('utf-8'))
    clause = []
    words = []
    for i in content:
        if i in cut_list:  #
            if len(words) < 1:  # 处理连续出现多个标点
                continue

            if punctuation: words.append(i)  # 是否添加标点
            clause.append(''.join(words))
            words = []
        else:
            words.append(i)
    return clause


def get_cluster(words, tags):
    """
    获取簇的权重
    """
    weight = 0  # 簇的权重
    key_word_count = 0  # 包含关键字数量
    word_index = 0  # 词语位置
    last_key_word = start_key_word = 0
    for word in words:
        if word in tags:
            key_word_count += 1
            if start_key_word == 0:  # 如果没有开始的关键字，记录下来
                last_key_word = start_key_word = word_index
            else:
                if word_index - start_key_word < 5:  # 簇之间阈值小于4
                    last_key_word = word_index
                else:  # 簇之间阈值超过4
                    # 首先计算原有簇的权重
                    count = (last_key_word - start_key_word) + 1
                    if key_word_count > 1:  # 避免一个簇只包含一个关键字的情况
                        weight_temp = (key_word_count ** 2) / float(count)
                        weight = max(weight, weight_temp)

                    key_word_count = 1  # 重新计算关键字数量
                    last_key_word = start_key_word = word_index
        else:
            continue
        word_index += 1

    count = (last_key_word - start_key_word) + 1

    if key_word_count > 1:  # 避免一个簇只包含一个关键字的情况

        weight_temp = (key_word_count ** 2) / float(count)
        weight = max(weight, weight_temp)

    return weight


def summarize(document, max_length=100):
    """
    自动摘要
    """
    result = {}
    document = document.decode('utf-8')
    tags = extract_tags(document)  # 关键字
    clause = cut_clause(document)  # 分句
    weight = dict()  # 存储每个句子包含簇的最大权重
    clause_index = 0  # 句子索引

    for i in clause:
        words = list(jieba.cut(i))

        weight[clause_index] = get_cluster(words, tags)
        clause_index += 1

    weight = sorted(weight.iteritems(), key=itemgetter(1), reverse=True)

    for i in weight:
        if len(clause[i[0]]) < max_length:
            result[i[0]] = clause[i[0]]
            max_length -= len(clause[i[0]])
        else:
            break
    return ''.join(result.values())


def update_dict(one={}, other={}):
    """
    递归合并两个字典，
    """
    temp = {}
    keys = one.keys()
    keys.extend(other.keys())

    for i in keys:
        if one.has_key(i) and other.has_key(i):
            if isinstance(one[i], dict) and isinstance(other[i], dict):
                temp[i] = update_dict(one[i], other[i])
            else:
                temp[i] = one[i] if isinstance(one[i], dict) else other[i]

        else:
            temp[i] = one.get(i) if one.has_key(i) else other.get(i)
    return temp


correction_dict = {}  # 加载纠错词典

for lines in file(os.path.join(os.path.dirname(__file__), "dict/movie_key.txt")):
    temp = {}
    word, num = lines.decode('utf-8').split(' ')
    num = int(num.strip())
    word = list(word.strip())
    i = len(word) - 1
    if i < 1: continue

    while i >= 0:
        if not temp:
            temp = {word[i]: {'value': num}}
        else:
            val = temp
            temp = {}
            temp[word[i]] = val
        i -= 1
    correction_dict = update_dict(correction_dict, temp)


def correction(word):
    r = {}  # 结果
    word = word.strip().decode('utf-8')
    i = 0
    length = len(word)
    while i < length:
        r.update(get_word_one(word, i))
        i += 1
    return r


def get_word_one(words, index):
    """
    每个元素处理
    """
    temp = correction_dict
    temp_old = temp
    length = len(words)
    i = 0
    r = {}  # 结果
    while i < index:
        temp_old = temp
        if temp.has_key(words[i:i + 1]):
            temp = temp.get(words[i:i + 1])
        else:
            temp = {}
        i += 1

    if (index + 2) >= length or temp.has_key(words[index + 1:index + 2]):  # 删除法可行，就继续验证是否只有一步距离
        r.update(get_word_one_delete(words, temp, i + 1, length))  # 尝试删除法
        r.update(get_word_one_swap(words, temp_old, i, length))  # 尝试交换法

    r.update(get_word_one_replace(words, temp_old, index, length))  # 尝试替换
    r.update(get_word_one_insert(words, temp, index, length))  # 插入法
    return r


def get_word_one_delete(words, data, i_delete, length):
    """
    删除法
    """
    if not data:
        return {}
    i = i_delete

    while i < length:
        #print '---', words[i_delete:i_delete + 1]
        if data.has_key(words[i:i + 1]):
            data = data.get(words[i:i + 1])
            i += 1
            continue
        else:
            return {}
    if data and data.has_key('value'):
        return {words[0:i_delete - 1] + words[i_delete:]: data['value']}
    else:
        return {}


def get_word_one_swap(words, data, i_swap, length):
    """
    交换法
    """

    if (not i_swap) or (not data):
        return {}

    if data.has_key(words[i_swap:i_swap + 1]):
        data = data.get(words[i_swap:i_swap + 1])
        if data.has_key(words[i_swap - 1:i_swap]):
            data = data.get(words[i_swap - 1:i_swap])
        else:
            return {}
    else:
        return {}

    i = i_swap + 1

    while i <= length - 1:
        #print '---', words[i_delete:i_delete + 1]
        if data.has_key(words[i:i + 1]):
            data = data.get(words[i:i + 1])
            i += 1
            continue
        else:
            return {}

    if data and data.has_key('value'):
        words = words[0:i_swap - 1] + words[i_swap:i_swap + 1] + words[i_swap - 1:i_swap] + words[i_swap + 1:]
        return {words: data['value']}
    else:
        return {}


def get_word_one_replace(words, data, i_replace, length):
    """
    替换法
    """

    check_temp = {}
    temp = {}
    return_temp = {}
    start = words[0:i_replace - 1] if i_replace > 0 else ''
    end = words[i_replace:]

    if (i_replace > length) or (not data):
        return {}

    for i in data:
        if not isinstance(data[i], dict):
            continue
        if data[i].has_key(words[i_replace:i_replace + 1]):
            temp[i] = data[i].get(words[i_replace:i_replace + 1])

    for i_data in temp:
        i = i_replace + 1
        while i < length:
            #print '---', words[i:i + 1],words[i_replace:i_replace + 1]#

            if temp[i_data].has_key(words[i:i + 1]):
                temp[i_data] = temp[i_data].get(words[i:i + 1])
                i += 1
                continue
            else:
                break
        if i == length and temp[i_data].has_key('value'):
            check_temp[i_data] = temp[i_data].get('value')


    # 专门处理最后一个文字的情况。最后一个文字只需要返回有value的 START
    if i_replace == length - 1:
        if data.has_key(words[i_replace - 1:i_replace]):
            start = words[0:i_replace]  # 变换开始的截取位置
            end = ''  # 变换开始的截取位置
            for i in data[words[i_replace - 1:i_replace]]:
                if not isinstance(data[words[i_replace - 1:i_replace]][i], dict):
                    continue
                if data[words[i_replace - 1:i_replace]][i].has_key('value'):
                    check_temp[i] = data[words[i_replace - 1:i_replace]][i]['value']


    # 专门处理最后一个文字的情况。最后一个文字只需要返回有value END
    for i in check_temp:
        return_temp[start + i + end] = check_temp[i]
    return return_temp


def get_word_one_insert(words, data, i_insert, length):
    """
    插入法
    """
    if (i_insert < 1) or (not data):
        return {}
    temp = {}
    return_temp = {}
    for i in data:
        if not isinstance(data[i], dict):
            continue
        if data[i].has_key(words[i_insert:i_insert + 1]):
            temp[i] = data[i][words[i_insert:i_insert + 1]]

    for i_data in temp:
        i = i_insert + 1

        while i <= length:
            if temp[i_data].has_key(words[i:i + 1]):
                temp[i_data] = temp[i_data].get(words[i:i + 1])
                i += 1
                continue
            else:
                break
        if i == length and temp[i_data].has_key('value'):
            return_temp[words[0:i_insert] + i_data + words[i_insert:]] = temp[i_data].get('value')
    return return_temp
