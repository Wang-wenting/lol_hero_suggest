#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Time    : 2022/4/27 16:04
# @Author  : RooFTOooOP
# @FileName: 1_1.py
# @Software: PyCharm


from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import re
import time
from tqdm import tqdm
import xlrd
import heapq
from contextlib import closing
from PIL import Image as ImagePIL
import os


"""
类说明:op.gg爬取英雄数据
Parameters:
    无
Returns:
    无
Modify:
    2022-04-28
"""


class downloader(object):

    def __init__(self, position):

        self.server = 'https://www.op.ggxxx/counters'
        self.target = 'https://www.op.gg/champions?position=' + position
        self.data_path = '.\\data\\' + position + '.xlsx'
        self.image_path = '.\\data\\image\\' + position + '\\'
        self.heros = []  # 存放英雄名
        self.results = {}  # 存放爬虫结果
        self.urls = []  # 存放对应链接
        self.hero_images = [] # 存放对应英雄头像
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
                        'Accept-Language': 'zh-CN'}


    """
    函数说明:获取各英雄链接
    Parameters:
        无
    Returns:
        无
    Modify:
        2022-04-28
    """

    def get_download_url(self):
        try:
            req = requests.get(url=self.target, verify=False, headers=self.headers)
        except Exception as e:
            print(e)
        html = req.text
        div_bf = BeautifulSoup(html)
        version_bf = str(div_bf.find_all('div', class_='css-coswxu e1lgbf0v0')[0])
        version_if = re.search('Korea(.*?)</em>', version_bf)[1][-5:]
        with open(".\\data\\version.txt", 'w', encoding='UTF-8') as f:
            f.write(version_if)

        div = div_bf.find_all('tbody')
        a_bf = BeautifulSoup(str(div[0]))
        a = a_bf.find_all('a')
        for each in a:
            url = re.match('<a href="(.*?)">', str(each))
            hero_image = re.search('src="(.*?)"', str(each))
            hero_name = re.search('<strong>(.*?)</strong>', str(each))
            self.heros.append(hero_name[1])
            self.urls.append(url[1])
            self.hero_images.append(hero_image[1])

    """
    函数说明:获取对应胜率关系
    Parameters:
        无
    Returns:
        
    Modify:
        2022-04-28
    """

    def get_contents(self, url):
        target = self.server.replace('xxx', url)
        req = requests.get(url=target, headers=self.headers)
        html = req.text
        bf = BeautifulSoup(html)
        texts = bf.find_all('ul', class_='css-1v96p32 eglybw60')
        li_bf = BeautifulSoup(str(texts[0]))
        li = li_bf.find_all('li')
        hero_names = []
        for each in li:
            hero_name = re.search('name">(.*?)<', str(each))
            win_rate = re.search('win">(.*?)<', str(each))
            hero_names.append(hero_name[1])
            if hero_name[1] in self.results:
                self.results[hero_name[1]].append(win_rate[1])
            else:
                self.results[hero_name[1]] = [win_rate[1]]
        time.sleep(1)
        remain_names = list(set(self.heros) - set(hero_names))
        for r in remain_names:
            if r in self.results:
                self.results[r].append('0')
            else:
                self.results[r] = ['0']

    def to_my_data(self):
        df = pd.DataFrame(self.results, index=self.heros)
        file_path = self.data_path
        df.to_excel(file_path, encoding='utf-8')

        """
            函数说明:爬取英雄头像
            Parameters:
                无
            Returns:

            Modify:
                2022-04-29
        """

    def get_hero_image(self):
        for i, image in enumerate(self.hero_images):
            with closing(requests.get(url=image, stream=True, verify=False, headers=self.headers)) as r:
                with open(self.image_path + self.heros[i] + '.jpg', 'ab+') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()


"""
类说明:得到排序结果，以lol_hero_V1中的实现版本为标准
Parameters:
    无
Returns:
    无
Modify:
    2022-04-28
"""


class rank_hero(object):

    def __init__(self, file_name):
        self.file_name = file_name
        self.my_pool = ['盲僧', '破败之王', '皎月女神', '永恒梦魇', '影流之镰', '无极剑圣', '永猎双子', '虚空掠夺者', '虚空遁地兽',
                        '圣锤之毅', '蜘蛛女皇', '雪原双子', '痛苦之拥', '不灭狂雷', '灵罗娃娃']

    def read_data(self):
        data = xlrd.open_workbook(self.file_name)
        table = data.sheet_by_name('Sheet1')
        nrows = table.nrows
        data = []
        for i in range(nrows):
            data.append(table.row_values(i)[:])
        data = np.array(data)
        my_row = data[0, 1:]
        my_col = data[1:, 0]
        my_data = data[1:, 1:]
        return my_col, my_row, my_data

    def ranking(self, my_row, my_col, my_data, enemy_name):
        if enemy_name not in my_row:
            print('奇怪的对手')
            return 0, 0
        number = np.where(my_row == enemy_name)[0][0]
        rank_list = my_data[:, number].tolist()
        re1 = heapq.nlargest(20, rank_list)
        re2 = list(map(rank_list.index, re1))
        rank_res1 = []
        rank_res2 = []
        for r in re2:
            rank_res1.append(my_col[r])
            if my_col[r] in self.my_pool:
                rank_res2.append(my_col[r])
        return rank_res1[:5], rank_res2[:5]


def transfer(infile, outfile):
    '''
    实现图片dpi的更改
    :param infile: 输入图片名称
    :param outfile: 输入图片名称
    :return: 无
    '''
    im = ImagePIL.open(infile)
    im.save(outfile, dpi=(96.0, 96.0))  # 500.0,500.0分别为想要设定的dpi值


if __name__ == "__main__":
    position = ['jungle', 'top', 'mid']
    for p in position:
        print('>>>>>' + p + '位置开始爬取')
        dl = downloader(p)
        dl.get_download_url()
        dl.get_contents()
        dl.get_hero_image()
        print('>>>>>' + p + '位置爬取完成')
    # rk = rank_hero('name.xlsx')
    # col, row, data = rk.read_data()
    # enery_name = input()
    # res1, res2 = rk.ranking(row, col, data, enery_name)

    # path = '.\\data\image\\top'
    # file = os.listdir(path)
    # for f in file:
    #     print(f)
    #     name = path + '\\' + f
    #     transfer(name, name)
