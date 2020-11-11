#-*-coding:utf-8-*-
from xml.dom.minidom import parse
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
import threading
import datetime
import time
import cv2
import os


class setupUIFunctions():
    def __init__(self, Window):
        self.Window = Window
        self.pathImage = None
        self.pathAnnotation = None
        self.pathGenerate = None
        self.PresentPage = 1
        self.logFile = './Labelling.log'
        self.setupUIFunctions()

    def setupUIFunctions(self):
        self.connectSignals2Slots()
        self.InitialEnv()

    def connectSignals2Slots(self):
        self.Window.pushButton_Image.clicked.connect(lambda:self.getDirectory(0))
        self.Window.pushButton_Labelling.clicked.connect(lambda:self.getDirectory(1))
        self.Window.pushButton_Generate.clicked.connect(lambda:self.getDirectory(2))

        self.Window.pushButton_prior.clicked.connect(self.priorImage)
        self.Window.pushButton_next.clicked.connect(self.nextImage)
        self.Window.pushButton_Checked.clicked.connect(self.passImage)
        self.Window.action_A.triggered.connect(self.priorImage)
        self.Window.action_D.triggered.connect(self.nextImage)
        self.Window.action_E.triggered.connect(self.deleteImage)

        self.Window.spinBox_tl_x.valueChanged.connect(self.changetlx)
        self.Window.spinBox_tl_y.valueChanged.connect(self.changetly)
        self.Window.spinBox_br_x.valueChanged.connect(self.changebrx)
        self.Window.spinBox_br_y.valueChanged.connect(self.changebry)

        self.Window.lineEdit_present_page.editingFinished.connect(self.JumpPages)
        self.Window.checkBox_Undone.stateChanged.connect(self.DisplaySwitch)

    def InitialEnv(self):
        self.readEnv()

    ####################################################################################
    #                               UI Functions                                       #
    ####################################################################################

    def getDirectory(self, type):
        info = ["请选择标注图像 jpg 路径", "请选择标注文件 xml 路径", "请选择转换文件 txt 存放路径"]
        dirt = QFileDialog.getExistingDirectory(None, info[type], r"D:\实验室\无人机数据\红外数据")
        if dirt == "":
            return
        if type == 0:
            self.pathImage = dirt
            self.Window.label_path_image.setText(dirt)
        if type == 1:
            self.pathAnnotation = dirt
            self.Window.label_path_annotation.setText(dirt)
        if type == 2:
            self.pathGenerate = dirt
            self.Window.label_generate.setText(dirt)

        if self.pathImage != None and self.pathAnnotation != None and self.pathGenerate != None:
            self.analyseData()
            self.writeEnv()

    def priorImage(self):
        if self.PresentPage == 1:
            return
        else:
            self.PresentPage -= 1
            self.setTitle()
            self.refreshPages()
            self.Window.lineEdit_present_page.setText("{}".format(self.PresentPage))
            self.showImage()

    def nextImage(self):
        if self.PresentPage == self.TotalImages:
            return
        else:
            self.PresentPage += 1
            self.setTitle()
            self.refreshPages()
            self.Window.lineEdit_present_page.setText("{}".format(self.PresentPage))
            self.showImage()

    def passImage(self):
        self.saveFile()
        if self.PresentPage == self.TotalImages:
            self.changeLabelState()
            return
        else:
            self.PresentPage += 1
            self.setTitle()
            self.refreshPages()
            self.Window.lineEdit_present_page.setText("{}".format(self.PresentPage))
            self.showImage()

    def deleteImage(self):
        pass

    def DisplaySwitch(self, state):
        if state == Qt.Checked:
            self.ChangeToUnlabelled()
        if state == Qt.Unchecked:
            self.ChangeToAll()
        
    def JumpPages(self):
        page = int(self.Window.lineEdit_present_page.text())
        if page > self.TotalImages:
            page = self.TotalImages
        elif page < 1:
            page = 1
        self.PresentPage = page
        self.refreshPages()
        self.Window.lineEdit_present_page.setText("{}".format(self.PresentPage))
        self.showImage()
        self.setTitle()

    def changetlx(self):
        if self.Window.spinBox_tl_x.value() >= self.bottomRight[0]:
            self.Window.spinBox_tl_x.setValue(self.bottomRight[0] - 1)
            return
        else:
            self.topLeft = (self.Window.spinBox_tl_x.value(), self.topLeft[1])
        self.refreshBoundingBox()

    def changetly(self):
        if self.Window.spinBox_tl_y.value() >= self.bottomRight[1]:
            self.Window.spinBox_tl_y.setValue(self.bottomRight[1] - 1)
            return
        else:
            self.topLeft = (self.topLeft[0], self.Window.spinBox_tl_y.value())
        self.refreshBoundingBox()

    def changebrx(self):
        if self.Window.spinBox_br_x.value() <= self.topLeft[0]:
            self.Window.spinBox_br_x.setValue(self.topLeft[0] - 1)
            return
        else:
            self.bottomRight = (self.Window.spinBox_br_x.value(), self.bottomRight[1])
        self.refreshBoundingBox()

    def changebry(self):
        if self.Window.spinBox_br_y.value() <= self.topLeft[1]:
            self.Window.spinBox_br_y.setValue(self.topLeft[1] - 1)
            return
        else:
            self.bottomRight = (self.bottomRight[0], self.Window.spinBox_br_y.value())
        self.refreshBoundingBox()

    ####################################################################################
    #                              Process Functions                                   #
    ####################################################################################

    def refreshBoundingBox(self):
        self.bbsize = (self.bottomRight[0] - self.topLeft[0], self.bottomRight[1] - self.topLeft[1])
        self.Window.label_w.setText(str(self.bbsize[0]))
        self.Window.label_h.setText(str(self.bbsize[1]))
        image_show = self.ProcessImage(self.annotateImage(self.presentImage.copy(), True))
        self.Window.label_Image.setPixmap(QPixmap(image_show))

    def refreshInfo(self):
        self.Window.spinBox_tl_x.setValue(self.topLeft[0])
        self.Window.spinBox_tl_y.setValue(self.topLeft[1])
        self.Window.spinBox_br_x.setValue(self.bottomRight[0])
        self.Window.spinBox_br_y.setValue(self.bottomRight[1])
        self.Window.label_w.setText(str(self.bbsize[0]))
        self.Window.label_h.setText(str(self.bbsize[1]))

    def refreshPages(self):
        info = "({}/{})".format(self.PresentPage, self.TotalImages)
        self.Window.label_page.setText(info)

    def analyseData(self, isInit=True):
        if isInit:
            self.Images = os.listdir(self.pathImage)
        self.Annotations = [elem.replace('.jpg', '.xml') for elem in self.Images]
        self.Txts = [elem.replace('.jpg', '.txt') for elem in self.Images]
        self.ImagesPath = [os.path.join(self.pathImage, elem) for elem in self.Images]
        self.AnnotationsPath = [os.path.join(self.pathAnnotation, elem) for elem in self.Annotations]
        self.TxtsPath = [os.path.join(self.pathGenerate, elem) for elem in self.Txts]

        self.TotalImages = len(self.Images)

        self.locateFirstUnlabelled()
        self.refreshPages()
        self.Window.lineEdit_present_page.setText("{}".format(self.PresentPage))
        self.showImage()
        self.setTitle()

    def ProcessImage(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_cvt = QImage(image_rgb[:], image_rgb.shape[1], image_rgb.shape[0], image_rgb.shape[1] * 3, QImage.Format_RGB888)
        image_show = QPixmap(image_cvt).scaled(960, 540)
        return image_show

    def getAnnotation(self, annotationFile):
        domTree = parse(annotationFile)
        rootNode = domTree.documentElement
        if rootNode.getElementsByTagName("object") == []:
            return (-1, -1), (-1, -1)
        objects = rootNode.getElementsByTagName("object")[0]
        bndbox = objects.getElementsByTagName("bndbox")[0]
        xmin = int(bndbox.childNodes[1].firstChild.data)
        ymin = int(bndbox.childNodes[3].firstChild.data)
        xmax = int(bndbox.childNodes[5].firstChild.data)
        ymax = int(bndbox.childNodes[7].firstChild.data)
        return (xmin, ymin), (xmax, ymax)

    def getTxt(self, txtFile):
        with open(txtFile, 'r') as file:
            line = file.read()
            line = line.replace('\n', '')
            if ',' in line:
                data = line.split(',')
                tl_col = int(data[1])
                tl_row = int(data[2])
                bb_width = int(data[3])
                bb_height = int(data[4])
        return (tl_col, tl_row), (tl_col + bb_width, tl_row + bb_height)

    def annotateImage(self, image, refine=False):
        if os.path.exists(self.TxtsPath[self.PresentPage - 1]):
            tl, br = self.getTxt(self.TxtsPath[self.PresentPage - 1])
        else:
            tl, br = self.getAnnotation(self.AnnotationsPath[self.PresentPage - 1])

        if tl[0] == -1:
            return image
        else:
            if not refine:
                self.topLeft = tl
                self.bottomRight = br
                self.bbsize = (br[0] - tl[0], br[1] - tl[1])
            return cv2.rectangle(image, self.topLeft, self.bottomRight, (255, 0, 0))
    
    def showImage(self):
        self.presentImage = cv2.imdecode(np.fromfile(self.ImagesPath[self.PresentPage - 1], dtype=np.uint8), cv2.IMREAD_COLOR)
        image_show = self.ProcessImage(self.annotateImage(self.presentImage.copy()))
        self.Window.label_Image.setPixmap(QPixmap(image_show))
        self.refreshInfo()
        self.changeLabelState()

    def saveFile(self):
        sentence = "0,{},{},{},{}".format(*self.topLeft, *self.bbsize)
        with open(self.TxtsPath[self.PresentPage - 1], 'w+') as file:
            file.write(sentence)

    def setTitle(self):
        title = "图像标注  -  " + self.Images[self.PresentPage - 1]
        self.Window.setWindowTitle(title)

    def writeEnv(self):
        with open(self.logFile, 'w+') as file:
            file.write(self.pathImage + '\n')
            file.write(self.pathAnnotation + '\n')
            file.write(self.pathGenerate + '\n')

    def readEnv(self):
        if not os.path.exists(self.logFile):
            return
        with open(self.logFile, 'r') as file:
            self.pathImage, self.pathAnnotation, self.pathGenerate = [elem.replace('\n', '') for elem in file.readlines()]
        self.Window.label_path_image.setText(self.pathImage)
        self.Window.label_path_annotation.setText(self.pathAnnotation)
        self.Window.label_generate.setText(self.pathGenerate)
        self.analyseData()

    def isCheckedImage(self):
        if os.path.exists(self.TxtsPath[self.PresentPage - 1]):
            return True
        else:
            return False

    def changeLabelState(self):
        if self.isCheckedImage():
            self.Window.label_isCheck.setText('已查验')
            self.Window.label_isCheckImage.setStyleSheet("border-image: url(:/Icons/Resources/yes_600px_1181432_easyicon.net.png);")
        else:
            self.Window.label_isCheck.setText('未查验')
            self.Window.label_isCheckImage.setStyleSheet("border-image: url(:/Icons/Resources/close_600px_1181428_easyicon.net.png);")

    def locateFirstUnlabelled(self):
        labelledImages = os.listdir(self.pathGenerate)
        UnLabelledImages = [elem for elem in self.Images if elem.replace('.jpg', '.txt') not in labelledImages]
        if UnLabelledImages:
            self.PresentPage = self.Images.index(UnLabelledImages[0].replace('.txt', '.jpg')) + 1
        else:
            self.PresentPage = 1

    def ChangeToAll(self):
        self.Images = self.BackupImages
        self.analyseData()

    def ChangeToUnlabelled(self):
        labelledImages = os.listdir(self.pathGenerate)
        UnLabelledImages = [elem for elem in self.Images if elem.replace('.jpg', '.txt') not in labelledImages]
        self.BackupImages = self.Images
        self.Images = UnLabelledImages
        self.analyseData(False)