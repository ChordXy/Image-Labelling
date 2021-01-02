'''
Author: Cabrite
Date: 2021-01-02 00:19:29
LastEditors: Cabrite
LastEditTime: 2021-01-02 12:20:55
Description: Do not edit
'''

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys


class ImageLabel(QtWidgets.QLabel):
    # function, x, y
    LeftClick = QtCore.pyqtSignal(int, int, int)
    RightClick = QtCore.pyqtSignal(int, int, int)
    MidRoll = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)
        self.num = 0

    def mousePressEvent(self, event):
        if QtWidgets.QApplication.keyboardModifiers () == QtCore.Qt.ControlModifier:
            if event.buttons() == QtCore.Qt.LeftButton:
                self.setText ("单击鼠标左键的事件: 自己定义 ({}, {})".format(event.x(), event.y()))
                print("单击鼠标左键 ({}, {})".format(event.x(), event.y()))
            elif event.buttons() == QtCore.Qt.RightButton:
                self.setText ("单击鼠标右键的事件: 自己定义 ({}, {})".format(event.x(), event.y()))
                print("单击鼠标右键 ({}, {})".format(event.x(), event.y()))

    def wheelEvent(self, event):
        angle = event.angleDelta() / 8
        angleY = angle.y()
        if angleY > 0:
            self.num += 1
            self.setText("滚轮向上滚动的事件: {}".format(self.num))
            print("鼠标滚轮上滚 {}".format(self.num))
        else:
            self.num -= 1
            self.setText("滚轮向下滚动的事件: {}".format(self.num))
            print("鼠标滚轮下滚 {}".format(self.num))
 
    def mouseReleaseEvent(self, event):
        self.setText("鼠标释放事件: 自己定义 ({}, {})".format(event.x(), event.y()))
        print("鼠标释放 ({}, {})".format(event.x(), event.y()))
 
    def mouseMoveEvent(self, event):
        x, y = event.x(), event.y()
        self.setText("鼠标移动事件: 自己定义 ({}, {})".format(event.x(), event.y()))
        print("鼠标移动, ({}, {})".format(x, y))

