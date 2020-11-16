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


class BoundingBox():
    def __init__(self):
        self.__tlx = 0
        self.__tly = 0
        self.__brx = 0
        self.__bry = 0
        self.__width = 0
        self.__height = 0

    def setPoints(self, tlx, tly, brx, bry):
        self.__tlx = tlx
        self.__tly = tly
        self.__brx = brx
        self.__bry = bry
        self.__width = self.__brx - self.__tlx
        self.__height = self.__bry - self.__tly

    def setSize(self, tlx, tly, width, height):
        self.__tlx = tlx
        self.__tly = tly
        self.__width = width
        self.__height = height
        self.__brx = self.__tlx + self.__width
        self.__bry = self.__tly + self.__height

    ########################  左上角点 - x  ########################
    @property
    def tlx(self):
        return self.__tlx

    @tlx.setter
    def tlx(self, value):
        self.__tlx = value
        self.__width = self.__brx - self.__tlx

    ########################  左上角点 - y  ########################
    @property
    def tly(self):
        return self.__tly

    @tly.setter
    def tly(self, value):
        self.__tly = value
        self.__height = self.__bry - self.__tly

    ########################  右下角点 - x  ########################
    @property
    def brx(self):
        return self.__brx

    @brx.setter
    def brx(self, value):
        self.__brx = value
        self.__width = self.__brx - self.__tlx

    ########################  右下角点 - y  ########################
    @property
    def bry(self):
        return self.__bry

    @bry.setter
    def bry(self, value):
        self.__bry = value
        self.__height = self.__bry - self.__tly

    ########################  左上角 、 右下角 、 大小  ########################
    @property
    def topLeft(self):
        return (self.__tlx, self.__tly)

    @property
    def bottomRight(self):
        return (self.__brx, self.__bry)

    @property
    def size(self):
        return (self.__width, self.__height)

    ########################  宽度 - w  ########################
    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, value):
        self.__width = value
        self.__brx = self.__tlx + self.__width

    ########################  高度 - h  ########################
    @property
    def height(self):
        return self.__height

    @height.setter
    def height(self, value):
        self.__height = value
        self.__bry = self.__tly + self.__height

    ########################  是否合法  ########################
    @property
    def isValid(self):
        return self.__tlx > 0

class setupUIFunctions():
    def __init__(self, Window):
        self.Window = Window
        self.pathReady = [ 0, 0, 0 ]
        self.pathRemenber = 'C:'
        self.pathImage = None
        self.pathAnnotation = None
        self.pathGenerate = None
        self.PresentPage = 1
        self.BBColor = (255, 0, 0)
        self.bbox = BoundingBox()
        self.version = " v1.1"
        self.setupUIFunctions()

    def setupUIFunctions(self):
        self.connectSignals2Slots()

    def connectSignals2Slots(self):
        self.Window.pushButton_Image.clicked.connect(lambda: self.getDirectory(0))
        self.Window.pushButton_Labelling.clicked.connect(lambda: self.getDirectory(1))
        self.Window.pushButton_Generate.clicked.connect(lambda: self.getDirectory(2))
        self.Window.pushButton_refresh.clicked.connect(self.refreshDirectory)
        self.Window.pushButton_color.clicked.connect(self.selectColor)

    def enableButtons(self):
        self.Window.pushButton_prior.clicked.connect(self.priorImage)
        self.Window.pushButton_next.clicked.connect(self.nextImage)
        self.Window.pushButton_Checked.clicked.connect(self.passImage)
        self.Window.pushButton_ClearDirectory.clicked.connect(self.clearDirectory)
        self.Window.action_A.triggered.connect(self.priorImage)
        self.Window.action_D.triggered.connect(self.nextImage)
        self.Window.action_E.triggered.connect(self.deleteImage)

        self.Window.spinBox_tl_x.valueChanged.connect(self.changetlx)
        self.Window.spinBox_tl_y.valueChanged.connect(self.changetly)
        self.Window.spinBox_br_x.valueChanged.connect(self.changebrx)
        self.Window.spinBox_br_y.valueChanged.connect(self.changebry)

        self.Window.lineEdit_present_page.editingFinished.connect(self.JumpPages)
        self.Window.checkBox_Undone.stateChanged.connect(self.DisplaySwitch)

        QShortcut(QKeySequence(self.Window.tr("Ctrl+d")), self.Window, self.passImage)

    def disableButtons(self):
        self.Window.pushButton_prior.clicked.disconnect(self.priorImage)
        self.Window.pushButton_next.clicked.disconnect(self.nextImage)
        self.Window.pushButton_Checked.clicked.disconnect(self.passImage)
        self.Window.pushButton_ClearDirectory.clicked.disconnect(self.clearDirectory)
        self.Window.action_A.triggered.disconnect(self.priorImage)
        self.Window.action_D.triggered.disconnect(self.nextImage)
        self.Window.action_E.triggered.disconnect(self.deleteImage)

        self.Window.spinBox_tl_x.valueChanged.disconnect(self.changetlx)
        self.Window.spinBox_tl_y.valueChanged.disconnect(self.changetly)
        self.Window.spinBox_br_x.valueChanged.disconnect(self.changebrx)
        self.Window.spinBox_br_y.valueChanged.disconnect(self.changebry)

        self.Window.lineEdit_present_page.editingFinished.disconnect(self.JumpPages)
        self.Window.checkBox_Undone.stateChanged.disconnect(self.DisplaySwitch)

    ####################################################################################
    #                                   路径相关                                       #
    ####################################################################################

    def getDirectory(self, rtype):
        info = ["请选择标注图像 jpg 路径", "请选择标注文件 xml & txt 路径", "请选择核验 txt 存放路径"]
        dirt = QFileDialog.getExistingDirectory(None, info[rtype], self.pathRemenber)
        if dirt == "":
            return
        if rtype == 0:
            self.pathImage = dirt
            self.checkImageDirectory()
        if rtype == 1:
            self.pathAnnotation = dirt
            self.checkAnnotationDirectory()
        if rtype == 2:
            self.pathGenerate = dirt
            self.checkGenerateDirectory()
        if sum(self.pathReady) == 3:
            self.checkMatches()
        self.pathRemenber = dirt

    def checkImageDirectory(self):
        if self.CheckImageFolder():
            self.setRightPath(0)
            self.pathReady[0] = 1
        else:
            self.pathReady[0] = 0
            self.setWrongPath(0)
            self.pathImage = ""
            return
        
        self.Window.label_path_image.setText(self.pathImage)
        self.Images = [elem for elem in os.listdir(self.pathImage) if elem.endswith('.jpg')]
        self.ImageOrders = [elem.replace('.jpg', '') for elem in self.Images]

    def checkAnnotationDirectory(self):
        if self.CheckAnnotationFolder():
            self.setRightPath(1)
            self.pathReady[1] = 1
        else:
            self.pathReady[1] = 0
            self.setWrongPath(1)
            self.pathAnnotation = ""
            return
        
        self.Window.label_path_annotation.setText(self.pathAnnotation)
        self.Annotations = [elem for elem in os.listdir(self.pathAnnotation) if elem.endswith('.xml') or elem.endswith('.txt')]

    def checkGenerateDirectory(self):
        self.setRightPath(2)
        self.pathReady[2] = 1
        self.Window.label_generate.setText(self.pathGenerate)

    def checkMatches(self):
        AnnotationOrders = []
        for elem in self.Annotations:
            if elem.endswith('.txt'):
                at_order = elem.replace('.txt', '')
            elif elem.endswith('.xml'):
                at_order = elem.replace('.xml', '')
            AnnotationOrders.append(at_order)
        unmatchedImages = [elem for elem in self.ImageOrders if not elem in AnnotationOrders]
        if unmatchedImages:
            with open('./未标注图像.txt', 'w+') as file:
                for elem in unmatchedImages:
                    file.write(elem + '.jpg\n')
            print("in")
            msg = QMessageBox(QMessageBox.Warning, '警告', '有图像文件未标注，未标注图像见软件目录下“未标注图像.txt”\r\n补全标注后点击刷新按钮!', QMessageBox.Yes)
            msg.exec()
            self.setWrongPath(1)
            return False
        else:
            if os.path.exists('./未标注图像.txt'):
                os.remove('./未标注图像.txt')
            self.setRightPath(1)
            self.analyseData()
            self.enableButtons()
            return True

    def refreshDirectory(self):
        if sum(self.pathReady) == 3:
            self.Annotations = [elem for elem in os.listdir(self.pathAnnotation) if elem.endswith('.xml') or elem.endswith('.txt')]
            self.checkMatches()
        else:
            return

    def clearDirectory(self):
        self.disableButtons()
        self.Window.label_path_image.clear()
        self.Window.label_path_annotation.clear()
        self.Window.label_generate.clear()
        self.Window.label_Image.clear()
        self.Window.spinBox_tl_x.setValue(0)
        self.Window.spinBox_tl_y.setValue(0)
        self.Window.spinBox_br_x.setValue(0)
        self.Window.spinBox_br_y.setValue(0)
        self.Window.label_w.clear()
        self.Window.label_h.clear()
        self.Window.label_page.clear()
        self.Window.lineEdit_present_page.clear()
        self.Window.checkBox_Undone.setCheckState(Qt.Unchecked)
        self.PresentPage = 1
        self.presentImage = None
        self.setWaitingPath()
        self.pathReady = [0, 0, 0]
        self.pathImage = ""
        self.pathAnnotation = ""
        self.pathGenerate = ""

    def setWrongPath(self, pos):
        if pos == 0:
            icon = self.Window.label_img
            label = self.Window.label_path_image
        if pos == 1:
            icon = self.Window.label_ant
            label = self.Window.label_path_annotation
        if pos == 2:
            icon = self.Window.label_gnt
            label = self.Window.label_generate

        icon.setStyleSheet("border-image: url(:/Icons/Resources/close_600px_1181428_easyicon.net.png);")
        label.setStyleSheet(    "background-color: rgba(255, 0, 0, 100);\n"
                                "border-style:solid;\n"
                                "border-bottom-width:1px;\n"
                                "border-top-width:0px;\n"
                                "border-right-width:0px;\n"
                                "border-left-width:0px;") 

    def setRightPath(self, pos):
        if pos == 0:
            icon = self.Window.label_img
            label = self.Window.label_path_image
        if pos == 1:
            icon = self.Window.label_ant
            label = self.Window.label_path_annotation
        if pos == 2:
            icon = self.Window.label_gnt
            label = self.Window.label_generate
            
        icon.setStyleSheet("border-image: url(:/Icons/Resources/yes_600px_1181432_easyicon.net.png);")
        label.setStyleSheet("background:transparent;\n"
                                "border-style:solid;\n"
                                "border-bottom-width:1px;\n"
                                "border-top-width:0px;\n"
                                "border-right-width:0px;\n"
                                "border-left-width:0px;") 

    def setWaitingPath(self):
        self.Window.label_img.setStyleSheet("border-image: url(:/Icons/Resources/hourglass_155px_1201105_easyicon.net.png);")
        self.Window.label_ant.setStyleSheet("border-image: url(:/Icons/Resources/hourglass_155px_1201105_easyicon.net.png);")
        self.Window.label_gnt.setStyleSheet("border-image: url(:/Icons/Resources/hourglass_155px_1201105_easyicon.net.png);")
        self.Window.label_path_image.setStyleSheet("background:transparent;\n"
                                "border-style:solid;\n"
                                "border-bottom-width:1px;\n"
                                "border-top-width:0px;\n"
                                "border-right-width:0px;\n"
                                "border-left-width:0px;") 
        self.Window.label_path_annotation.setStyleSheet("background:transparent;\n"
                                "border-style:solid;\n"
                                "border-bottom-width:1px;\n"
                                "border-top-width:0px;\n"
                                "border-right-width:0px;\n"
                                "border-left-width:0px;") 
        self.Window.label_generate.setStyleSheet("background:transparent;\n"
                                "border-style:solid;\n"
                                "border-bottom-width:1px;\n"
                                "border-top-width:0px;\n"
                                "border-right-width:0px;\n"
                                "border-left-width:0px;") 

    def CheckImageFolder(self):
        file_info = '.jpg'
        files = os.listdir(self.pathImage)
        if not files:
            return False
        for elem in files:
            if elem.endswith(file_info):
                return True
        return False

    def CheckAnnotationFolder(self):
        files = os.listdir(self.pathAnnotation)
        if not files:
            return False
        for elem in files:
            if elem.endswith('.xml') or elem.endswith('.txt'):
                return True
        return False

    def CheckIsAllDone(self):
        txt_orders = [elem.replace('.txt', '') for elem in os.listdir(self.pathGenerate) if elem.endswith('.txt')]
        if txt_orders == self.ImageOrders:
            return True
        else:
            return False

    ####################################################################################
    #                                   读入图像                                       #
    ####################################################################################

    def analyseData(self):
        self.Txts = [elem.replace('.jpg', '.txt') for elem in self.Images]
        self.ImagesPath = [os.path.join(self.pathImage, elem) for elem in self.Images]
        self.TxtsPath = [os.path.join(self.pathGenerate, elem) for elem in self.Txts]
        self.TotalImages = len(self.Images)

        if self.CheckIsAllDone():
            self.Window.checkBox_Undone.setCheckable(False)
        else:
            self.Window.checkBox_Undone.setCheckable(True)

        self.locateFirstUnlabelled()
        self.setTitle()
        self.refreshPages()
        self.Window.lineEdit_present_page.setText("{}".format(self.PresentPage))
        self.showImage()

    def locateFirstUnlabelled(self):
        labelledImages = os.listdir(self.pathGenerate)
        UnLabelledImages = [elem for elem in self.Images if elem.replace('.jpg', '.txt') not in labelledImages]
        if UnLabelledImages:
            self.PresentPage = self.Images.index(UnLabelledImages[0].replace('.txt', '.jpg')) + 1
        else:
            self.PresentPage = 1
    
    def refreshPages(self):
        info = "({}/{})".format(self.PresentPage, self.TotalImages)
        self.Window.label_page.setText(info)

    def setTitle(self):
        title = "图像标注" + self.version + "  -  " + self.Images[self.PresentPage - 1]
        self.Window.setWindowTitle(title)

    ####################################################################################
    #                                   图像显示                                       #
    ####################################################################################

    def getXml(self, xmlFile):
        domTree = parse(xmlFile)
        rootNode = domTree.documentElement
        if rootNode.getElementsByTagName("object") == []:
            return -1, -1, -1, -1
        objects = rootNode.getElementsByTagName("object")[0]
        bndbox = objects.getElementsByTagName("bndbox")[0]
        xmin = int(bndbox.childNodes[1].firstChild.data)
        ymin = int(bndbox.childNodes[3].firstChild.data)
        xmax = int(bndbox.childNodes[5].firstChild.data)
        ymax = int(bndbox.childNodes[7].firstChild.data)
        return xmin, ymin, xmax, ymax

    def getTxt(self, txtFile):
        with open(txtFile, 'r') as file:
            line = file.read()
            if not line:
                return -1, -1, -1, -1
            line = line.replace('\n', '')
            if ',' in line:
                data = line.split(',')
                tl_col = int(data[1])
                tl_row = int(data[2])
                bb_width = int(data[3])
                bb_height = int(data[4])
        return tl_col, tl_row, bb_width, bb_height

    def annotateImage(self, image, refine=False):
        if os.path.exists(self.TxtsPath[self.PresentPage - 1]):
            self.bbox.setSize(*self.getTxt(self.TxtsPath[self.PresentPage - 1]))
        else:
            xml_filename = os.path.join(self.pathAnnotation, self.Images[self.PresentPage - 1].replace('.jpg', '.xml'))
            txt_filename = os.path.join(self.pathAnnotation, self.Images[self.PresentPage - 1].replace('.jpg', '.txt'))
            if os.path.exists(xml_filename):
                self.bbox.setPoints(*self.getXml(xml_filename))
            if os.path.exists(txt_filename):
                self.bbox.setSize(*self.getTxt(txt_filename))

        if not self.bbox.isValid:
            return image
        else:
            return cv2.rectangle(image, self.bbox.topLeft, self.bbox.bottomRight, self.BBColor)

    def ProcessImage(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_cvt = QImage(image_rgb[:], image_rgb.shape[1], image_rgb.shape[0], image_rgb.shape[1] * 3, QImage.Format_RGB888)
        image_show = QPixmap(image_cvt).scaled(960, 540)
        return image_show

    def refreshInfo(self):
        self.Window.spinBox_tl_x.setValue(self.bbox.tlx)
        self.Window.spinBox_tl_y.setValue(self.bbox.tly)
        self.Window.spinBox_br_x.setValue(self.bbox.brx)
        self.Window.spinBox_br_y.setValue(self.bbox.bry)
        self.Window.label_w.setText(str(self.bbox.width))
        self.Window.label_h.setText(str(self.bbox.height))

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

    def showImage(self):
        self.presentImage = cv2.imdecode(np.fromfile(self.ImagesPath[self.PresentPage - 1], dtype=np.uint8), cv2.IMREAD_COLOR)
        image_show = self.ProcessImage(self.annotateImage(self.presentImage.copy()))
        self.Window.label_Image.setPixmap(QPixmap(image_show))
        self.refreshInfo()
        self.changeLabelState()

    ####################################################################################
    #                                   功能操作                                       #
    ####################################################################################

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

    def saveFile(self):
        if self.bbox.isValid:
            sentence = "0,{},{},{},{}".format(self.bbox.tlx, self.bbox.tly, self.bbox.width, self.bbox.height)
        else:
            sentence = ""
        with open(self.TxtsPath[self.PresentPage - 1], 'w+') as file:
            file.write(sentence)

    def deleteImage(self):
        del self.Images[self.PresentPage - 1]
        del self.Txts[self.PresentPage - 1]
        self.TotalImages = len(self.Images)

        delImage = self.ImagesPath.pop(self.PresentPage - 1)
        delTxt = self.TxtsPath.pop(self.PresentPage - 1)

        delAnnotation = delImage.replace('.jpg', '.xml')
        if not os.path.exists(delAnnotation):
            delAnnotation = delImage.replace('.jpg', '.txt')

        os.remove(delImage)
        os.remove(delAnnotation)
        if os.path.exists(delTxt):
            os.remove(delTxt)
        self.refreshPages()
        self.setTitle()
        self.Window.lineEdit_present_page.setText("{}".format(self.PresentPage))
        self.showImage()

    def DisplaySwitch(self, state):
        if self.CheckIsAllDone():
            return
        if state == Qt.Checked:
            self.ChangeToUnlabelled()
        if state == Qt.Unchecked:
            self.ChangeToAll()
        self.analyseData()
        
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

    def ChangeToAll(self):
        self.Images = self.BackupImages

    def ChangeToUnlabelled(self):
        labelledImages = os.listdir(self.pathGenerate)
        UnLabelledImages = [elem for elem in self.Images if elem.replace('.jpg', '.txt') not in labelledImages]
        self.BackupImages = self.Images
        self.Images = UnLabelledImages

    ####################################################################################
    #                             Bounding Box Refine                                  #
    ####################################################################################

    def changetlx(self):
        if self.Window.spinBox_tl_x.value() >= self.bbox.brx:
            self.Window.spinBox_tl_x.setValue(self.bbox.brx - 1)
            return
        else:
            self.bbox.tlx = self.Window.spinBox_tl_x.value()
        self.refreshBoundingBox()

    def changetly(self):
        if self.Window.spinBox_tl_y.value() >= self.bbox.bry:
            self.Window.spinBox_tl_y.setValue(self.bbox.bry - 1)
            return
        else:
            self.bbox.tly = self.Window.spinBox_tl_y.value()
        self.refreshBoundingBox()

    def changebrx(self):
        if self.Window.spinBox_br_x.value() <= self.bbox.tlx:
            self.Window.spinBox_br_x.setValue(self.bbox.tlx - 1)
            return
        else:
            self.bbox.brx = self.Window.spinBox_br_x.value()
        self.refreshBoundingBox()

    def changebry(self):
        if self.Window.spinBox_br_y.value() <= self.bbox.tly:
            self.Window.spinBox_br_y.setValue(self.bbox.tly - 1)
            return
        else:
            self.bbox.bry = self.Window.spinBox_br_y.value()
        self.refreshBoundingBox()

    def refreshBoundingBox(self):
        self.Window.label_w.setText(str(self.bbox.width))
        self.Window.label_h.setText(str(self.bbox.width))
        annotated_image = cv2.rectangle(self.presentImage.copy(), self.bbox.topLeft, self.bbox.bottomRight, self.BBColor)
        image_show = self.ProcessImage(annotated_image)
        self.Window.label_Image.setPixmap(QPixmap(image_show))

    def selectColor(self):
        color = QColorDialog.getColor().name()
        color = color.replace("#", '')
        blue = eval('0x' + color[0:2])
        green = eval('0x' + color[2:4])
        red = eval('0x' + color[4:6])
        self.BBColor = (red, green, blue)
        self.showImage()









    