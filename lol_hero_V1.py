#!/usr/bin/python3
"""
@File: lol_hero_V1.py
@Created Time 2022-4-29 9:50
@Modified Time 2022-5-3 9:50
@Author: ROOFTOoOP

TODO:
    1. 更改背景
    2. 实现异常处理
    3. 实现自动版本更新
    4. 实现数据更新功能
"""


from sys import argv, exit
import numpy as np
import datetime
import xlrd
import os
import heapq
import pachong
from lol_hero import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QCompleter, QProgressBar
from PyQt5 import QtCore, QtGui


class rank_hero(object):

    def __init__(self, file_name):
        self.file_name = file_name
        if 'jungle' in self.file_name:
            self.my_pool = ['盲僧', '破败之王', '皎月女神', '永恒梦魇', '影流之镰', '无极剑圣', '永猎双子', '虚空掠夺者', '虚空遁地兽',
                            '圣锤之毅', '蜘蛛女皇', '雪原双子', '痛苦之拥', '不灭狂雷', '灵罗娃娃']
        elif 'mid' in self.file_name:
            self.my_pool = ['冰霜女巫', '愁云使者', '发条魔灵', '机械公敌', '机械先驱', '皎月女神', '解脱者', '九尾妖狐', '魔蛇之拥',
                            '熔岩巨兽', '虚空先知', '影哨', '正义巨像']
        elif 'top' in self.file_name:
            self.my_pool = ['暗裔剑魔', '河流之王', '荒漠屠夫', '酒桶', '解脱者', '狂暴之心', '离群之刺', '蛮族之王', '诺克萨斯之手',
                            '齐天大圣', '熔岩巨兽', '山隐之焰', '圣锤之毅', '铁铠冥魂', '武器大师', '猩红收割者']

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

    def ranking(self, enemy_name):
        my_col, my_row, my_data = self.read_data()
        if enemy_name not in my_row:
            print('奇怪的对手')
            return 0, 0, 0, 0
        number = np.where(my_row == enemy_name)[0][0]
        rank_list = my_data[:, number].tolist()
        re1 = heapq.nlargest(20, rank_list)
        re2 = list(map(rank_list.index, re1))
        rank_res1 = []
        rate_1 = []
        rank_res2 = []
        rate_2 = []
        for i, r in enumerate(re2):
            rank_res1.append(my_col[r])
            rate_1.append(rank_list[r])
            if my_col[r] in self.my_pool:
                rank_res2.append(my_col[r])
                rate_2.append(rank_list[r])
            if len(rank_res2) == 3:
                break
        return rank_res1[:3], rank_res2[:3], rate_1[:3], rate_2[:3]


class Main_Page(QMainWindow, Ui_MainWindow):
    update_fig = QtCore.pyqtSignal()
    update_rul = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.position = ['jungle', 'mid', 'top']
        self.file_path = ".\\data\\"
        self.font = {'family': 'SimHei', 'weight': 'normal', 'size': 10}
        # self.tabWidget_1.setCurrentIndex(0)

        self.init_combobox()
        self.slot_init()  # 信号槽初始化

    def init_combobox(self):
        """
        设置自动补全
        """
        for i, p in enumerate(self.position):
            file_name = self.file_path + p + '.xlsx'
            data = xlrd.open_workbook(file_name)
            table = data.sheet_by_name('Sheet1')
            item_lists = table.row_values(0)[1:]
            eval(f'self.comboBox_{i+1}_1.addItems(item_lists)')
            completer = QCompleter(item_lists)
            completer.setFilterMode(QtCore.Qt.MatchContains)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            eval(f'self.comboBox_{i+1}_1.setCompleter(completer)')
            eval(f'self.comboBox_{i+1}_1.setCurrentIndex(-1)')

    def slot_init(self):
        """
        信号槽函数初始化
        """
        self.progressBar.setVisible(False)
        now_time = '     ' + str(datetime.datetime.now())[:-7]
        with open('.\\data\\version.txt', encoding='UTF-8') as f:
            current_version = f.read()

        for i in range(3):
            eval(f'self.lineEdit_{i+1}_1.setText("       " + current_version + "  ")')   # 初始化版本，自动更新
            eval(f'self.lineEdit_{i+1}_2.setText(now_time)')  # 设置当前时间

        self.queding_1_1.clicked.connect(self.get_parameter1('jungle', 1))  # 获得打野评估结果
        self.queding_2_1.clicked.connect(self.get_parameter1('mid', 2))  # 获得中单评估结果
        self.queding_3_1.clicked.connect(self.get_parameter1('top', 3))  # 获得上单评估结果
        self.pushButton.clicked.connect(self.data_update)

    def my_message_box(self, title=' ', info='是否确认？', y_btn='确认', n_btn='取消', ):
        """
        实现弹出提示框
        """
        messagebox = QMessageBox(QMessageBox.Question, title, info)

        messagebox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        btnY = messagebox.button(QMessageBox.Yes)
        btnY.setText(y_btn)
        btnN = messagebox.button(QMessageBox.No)
        btnN.setText(n_btn)
        messagebox.exec()
        if messagebox.clickedButton() == btnY:
            return True
        else:
            return False

    def get_parameter1(self, current_position, current_page):
        """
        根据所选英雄确定对应胜率结果
        画图
        """
        def get_res():
            current_file = self.file_path + current_position + '.xlsx'
            current_hero = eval(f'self.comboBox_{current_page}_1.currentText()')

            rk = rank_hero(current_file)
            res1, res2, rate1, rate2 = rk.ranking(current_hero)
            if res1 == 0:
                self.my_message_box(title='提示', info='奇怪的对手，随便玩玩8！')
            for i in range(3):
                if i+1 > len(res2):
                    for k in range(i, 3):
                        eval(f'self.lineEdit_{current_page}_{k*2+3}.setText(res1[{i}])')
                        eval(f'self.lineEdit_{current_page}_{k*2+4}.setText(rate1[{i}])')
                    self.my_message_box(title='提示', info='宁的英雄池也太浅了8！')
                    break
                eval(f'self.lineEdit_{current_page}_{i*2+3}.setText(res1[{i}])')
                eval(f'self.lineEdit_{current_page}_{i*2+4}.setText(rate1[{i}])')
                eval(f'self.lineEdit_{current_page}_{i*2+9}.setText(res2[{i}])')
                eval(f'self.lineEdit_{current_page}_{i*2+10}.setText(rate2[{i}])')
                png1 = QtGui.QPixmap('E:\\英雄推荐系统\\data\\image\\' + current_position + '\\' + res1[i] + '.jpg')
                png2 = QtGui.QPixmap('E:\\英雄推荐系统\\data\\image\\' + current_position + '\\' + res2[i] + '.jpg')

                eval(f'self.label_fig_{current_page}_{i+1}.setPixmap(png1)')
                eval(f'self.label_fig_{current_page}_{i+4}.setPixmap(png2)')
            if rate2[0] > '60.00':
                self.my_message_box(title='提示', info='这把不玩'+res2[0]+'就是sb！')
        return get_res

    def data_update(self):
        """
        实现数据更新
        """
        c_p = self.tabWidget_1.currentIndex()
        p = ['jungle', 'mid', 'top'][c_p]
        p1 = ['打野', '中单', '上单'][c_p]
        if self.my_message_box(title='提示', info='是否确定更新' + p1 + '页面数据'):

            self.progressBar.setVisible(True)
            self.progressBar.setValue(0)
            try:
                print('>>>>>' + p + '位置开始爬取')
                dl = pachong.downloader(p)
                dl.get_download_url()
                length = len(dl.heros)
                for u in range(len(dl.urls)):
                    dl.get_contents(dl.urls[u])
                    self.progressBar.setValue(int((u+1)*100//length))
                dl.to_my_data()
                dl.get_hero_image()
                print('>>>>>' + p + '位置爬取完成')
            except:
                self.my_message_box(title='提示', info='由于网络等原因爬取失败')

            self.progressBar.setVisible(False)
            with open('.\\data\\version.txt', encoding='UTF-8') as f:
                current_version = f.read()

            for i in range(3):
                eval(f'self.lineEdit_{i+1}_1.setText("       " + current_version + "  ")')  # 初始化版本，自动更新

            path = '.\\data\image\\' + p
            file = os.listdir(path)
            for f in file:
                name = path + '\\' + f
                pachong.transfer(name, name)



if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)  # 高分辨率适配
    app = QApplication(argv)

    main_page = Main_Page()
    main_page.show()
    exit(app.exec_())
