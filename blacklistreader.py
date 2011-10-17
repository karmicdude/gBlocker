#!/usr/bin/python2.6
# -*- coding: utf-8 -*-

import csv
import os
from abc import ABCMeta, abstractmethod


class BlacklistReader(object):
    """Abstract BlacklistReader class"""
    __metaclass__ = ABCMeta

    readers = {}

    def __init__(self, filename=''):
        self.list = []
        if filename:
            self.initList(filename)

    @abstractmethod
    def initList(self, filename):
        pass

    @classmethod
    def getReader(cls, filename):
        ext = os.path.splitext(filename)[1]
        try:
            return cls.readers[ext](filename)
        except KeyError:
            return None

class BlacklistReaderTXT(BlacklistReader):
    """TXT files blacklist reader"""
    def __init__(self, filename):
        BlacklistReader.__init__(self, filename)

    def initList(self, filename):
        f = open(filename, 'r')
        for line in f.xreadlines():
            if not line in self.list:
                self.list.append(line.replace('\n', '').replace('\r', ''))


class BlacklistReaderCSV(BlacklistReader):
    """CSV files blacklist reader"""
    def __init__(self, filename):
        BlacklistReader.__init__(self, filename)

    def initList(self, filename):
        reader = csv.reader(open(filename, 'rb'))
        for line in reader:
            try:
                line = line[0]
                if not line in self.list:
                    self.list.append(line)
            except IndexError:
                pass


BlacklistReader.readers['.csv'] = BlacklistReaderCSV
BlacklistReader.readers[''] =  BlacklistReaderTXT
BlacklistReader.readers['txt'] =  BlacklistReaderTXT
