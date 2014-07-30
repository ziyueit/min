#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Ma'
import jieba
import redis
import hashlib
import min_nlp


class Min:
    """
    搜索引擎
    """
    connection = None

    def __init__(self, host='127.0.0.1', port=6379, db=0, password=None, socket_timeout=None, ):
        self.connection = redis.StrictRedis(host, port, db, password, socket_timeout)

    def search(self, keywords, start=0, length=20):
        """
        搜索关键字
        """
        seg_list = list(jieba.cut_for_search(keywords))
        key_list = self.search_by_words(seg_list, start, length)
        return key_list

    def add_content(self, content, obj_key):
        """
        添加文档到索引
        """
        seg_list = jieba.cut_for_search(content)
        seg_list = min_nlp.get_weight(seg_list)
        self.add_word_index(seg_list, obj_key)

    def md5_for_word(self, word):
        """
        关键字md5
        """
        return hashlib.md5('w:' + word.encode('utf-8')).hexdigest()

    def add_word_index(self, seg_list, key):
        """
        添加关键字，到索引
        """
        for i in seg_list:
            self.connection.zadd(self.md5_for_word(i[1]), i[0], key)

    def search_by_words(self, words, start=0, length=20):
        """
        搜索
        """
        key_list = None

        if len(words) is 1:
            key_list = self.connection.zrange(self.md5_for_word(words[0]), start, start + length, True)

        else:
            key_count = self.connection.zunionstore(self.md5_for_word('min_word_search'),
                                                    [self.md5_for_word(i) for i in words])
            key_list = self.connection.zrange(self.md5_for_word('min_word_search'), start, start + length, True)

        return key_list
