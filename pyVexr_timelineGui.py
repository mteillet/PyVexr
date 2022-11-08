# Timeline for PyVexr Gui

# pyVexr_timelineGui.py

import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui

timelineDictInfos = {}

class _Timeline(QtWidgets.QWidget):
    """
    Here is the modified slider to get the actual timeline
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cachePos = []
        self.maxBuffer = 1
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )
        
    def sizeHint(self):
        return QtCore.QSize(500, 35)

    def _trigger_refresh(self):
        self.update()

    def paintEvent(self, event):
        # Init and background of widget
        painter = QtGui.QPainter(self)
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor(25,25,25))
        brush.setStyle(QtCore.Qt.SolidPattern)
        rect = QtCore.QRect(0,0, painter.device().width(), painter.device().height())
        painter.fillRect(rect, brush)

        # Painting the lower bar
        brush.setColor(QtGui.QColor(225,225,225))
        rect = QtCore.QRect(0 ,painter.device().height()-0.5 , painter.device().width(), painter.device().height())
        painter.fillRect(rect, brush)
        #print(self.cachePos)
        #tempList = [QtGui.QColor(10, 125, 10), QtGui.QColor(10, 255,10)]
        brush.setColor(QtGui.QColor(10,125,10))
        if self.maxBuffer >> 2:
            lenMax = self.maxBuffer - 1
        else:
            lenMax = self.maxBuffer
        for i in self.cachePos :
            #brush.setColor(tempList[i%2])
            xStart = ( (i-1) * painter.device().width() / lenMax )
            xEnd = (painter.device().width() / lenMax + 1)
            rect = QtCore.QRect(xStart, painter.device().height() - 0.5, xEnd, painter.device().height())
            painter.fillRect(rect, brush)

        # Color back to white
        brush.setColor(QtGui.QColor(225,225,225))
        # Get Values from the slider
        slider = self.parent().slider
        vmin, vmax = slider.minimum(), slider.maximum()
        value = slider.value()
        tickValue = value * painter.device().width() / vmax

        pen = painter.pen()
        pen.setColor(QtGui.QColor("white"))
        painter.setPen(pen)

        # Text following slider
        font = QtGui.QFont("Serif", 7, QtGui.QFont.Light)
        painter.setFont(font)
        try:
            (timelineDictInfos["slider"][0])
            painter.drawText(tickValue+2, 13, "{}".format(timelineDictInfos["slider"][value]["frame"]))
        except KeyError:
            painter.drawText(tickValue+2, 13, "{}".format("Unknow Frame Number"))

        # Bar following slider
        rect = QtCore.QRect(tickValue,0,1, painter.device().height())
        painter.fillRect(rect, brush)

        # Drawing lines depending on the len of the dict
        try:
            (timelineDictInfos["slider"][0])
            total = (len(timelineDictInfos["slider"]))-1
            item = painter.device().width() / (total+0.00001)
            current = 0
            previousName = "pyVexrTempName"
            for i in timelineDictInfos["slider"]:
                if (timelineDictInfos["slider"][current]["shot"] != previousName):
                    # Drawing the bigger lines and the shot names for every new shot
                    shotRect = QtCore.QRect(item*current, 0, 1, painter.device().height()-1)
                    brush.setColor(QtGui.QColor(100,100,100))
                    painter.fillRect(shotRect, brush)
                    # Drawing the shot name
                    font = QtGui.QFont("Serif", 10, QtGui.QFont.Bold)
                    painter.setPen(QtGui.QColor(200,200,200))
                    painter.drawText(item*current+1, 30, "Shot : {}".format(timelineDictInfos["slider"][current]["shot"]))

                    previousName = timelineDictInfos["slider"][current]["shot"]
                elif (((int(timelineDictInfos["slider"][current]["frame"])) % 5) == 0):
                    # Drawing the bigger lines every 5 frames
                    brush.setColor(QtGui.QColor(100,100,100))
                    rect = QtCore.QRect(item*current, 6, 1, 19)
                    font = QtGui.QFont("Serif", 5, QtGui.QFont.Light)
                    painter.setPen(QtGui.QColor(100,100,100)) 
                    painter.drawText(item*current+1, 18, "{}".format(timelineDictInfos["slider"][current]["frame"]))
                else:
                    # Drawing the other individual frames
                    brush.setColor(QtGui.QColor(100,100,100))
                    rect = QtCore.QRect(item*current, 13, 1, 5)
                painter.fillRect(rect, brush)
                current += 1
        except KeyError:
            pass

        painter.end()

    def paintBuffer(self, position, maxBuffer):
        self.cachePos.append(position)
        self.maxBuffer = maxBuffer
        self._trigger_refresh()

    def resetCacheDraw(self):
        self.cachePos = []
        self._trigger_refresh()

class Timeline(QtWidgets.QWidget):
    """
    Custom Qt Widget to show a timeline supporting multiple shots
    """

    def __init__(self, *args, **kwargs):
        super(Timeline, self).__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        textLayout = QtWidgets.QHBoxLayout()
        mainLayout = QtWidgets.QVBoxLayout()

        self.label = QtWidgets.QLabel("ShotName")
        self.frameNumber = QtWidgets.QLabel("Frame : Number")
        self.channelLabel = QtWidgets.QLabel("Channel : ")
        self.styleRed = "QLabel {color : red; }"
        self.styleGreen = "QLabel {color : green; }"
        self.styleBlue = "QLabel {color : blue; }"
        self.styleBlack = "QLabel {color : black; }"
        self.styleWhite = "QLabel {color : white; }"
        self.channelLabelR = QtWidgets.QLabel("R")
        self.channelLabelR.setStyleSheet(self.styleRed)
        self.channelLabelG = QtWidgets.QLabel("G")
        self.channelLabelG.setStyleSheet(self.styleGreen)
        self.channelLabelB = QtWidgets.QLabel("B")
        self.channelLabelB.setStyleSheet(self.styleBlue)
        self.channelLabelA = QtWidgets.QLabel("A")
        self.channelLabelLuma = QtWidgets.QLabel("Luma")
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.hide()
        self._timeline= _Timeline()
        self.slider.valueChanged.connect(self.refreshSliderInfos)
        self.slider.valueChanged.connect(self._timeline._trigger_refresh)

        textLayout.addWidget(self.label)
        textLayout.setSpacing(0)
        textLayout.addStretch()
        textLayout.addWidget(self.frameNumber)
        textLayout.addStretch()
        textLayout.addWidget(self.channelLabel)
        textLayout.addWidget(self.channelLabelR)
        textLayout.addWidget(self.channelLabelG)
        textLayout.addWidget(self.channelLabelB)
        textLayout.addWidget(self.channelLabelA)
        textLayout.addWidget(self.channelLabelLuma)
        # Hiding luma by default
        self.channelLabelLuma.hide()
        layout.addWidget(self._timeline)
        layout.addWidget(self.slider)

        mainLayout.addLayout(textLayout)
        mainLayout.addLayout(layout)

        # Left btn clicked toggle
        self.leftBtnClicked = False

        self.setLayout(mainLayout)

    def refreshSliderInfos(self):
        #print("update")
        #print(timelineDictInfos["slider"])
        try:
            (timelineDictInfos["slider"][self.slider.value()])
            self.label.setText("Shot : {}".format(timelineDictInfos["slider"][self.slider.value()]["shot"]))
            self.frameNumber.setText("Frame : {}".format(timelineDictInfos["slider"][self.slider.value()]["frame"]))
        except KeyError:
            pass

    def mousePressEvent(self, event):
        if(event.button() == QtCore.Qt.LeftButton):
            #print("clicked left")
            self.leftBtnClicked = True
            val = self.pixelPosToRangeValue(event.pos())
            self.slider.setValue(val)

    def mouseReleaseEvent(self, event):
        if(event.button() == QtCore.Qt.LeftButton):
            self.leftBtnClicked = False

    def mouseMoveEvent(self, event):
        if(self.leftBtnClicked == True):
            val = self.pixelPosToRangeValue(event.pos())
            self.slider.setValue(val)

    def pixelPosToRangeValue(self, pos):
        val = round(pos.x() / self._timeline.size().width() * self.slider.maximum())
        if (val > self.slider.maximum()):
            val = self.slider.maximum()
        elif (val < self.slider.maximum()-1):
            val -= 1

        return(val)

    def returnFrame(self, number):
        #print(number)
        try:
            (timelineDictInfos["slider"])
            if number >= len(timelineDictInfos["slider"]):
                return(timelineDictInfos["slider"][number-1]["path"])
            else:
                return(timelineDictInfos["slider"][number]["path"])
        except KeyError:
            print("returning default image")
            return("/home/martin/Documents/PYTHON/PyVexr/imgs/pyVexrSplashScreen_v002.exr")

    def updateSlider(self, timeLineDict):
        timelineDictInfos["slider"] = timeLineDict
        self.slider.setMinimum(0)
        # In order to avoid divinding by
        if (len(timeLineDict) < 2):
            self.slider.setMaximum(1)
        else:
            self.slider.setMaximum(len(timeLineDict)-1)
        try :
            (timeLineDict[0])
            self.label.setText("Shot : {}".format(timeLineDict[0]["shot"]))
            self.frameNumber.setText("Frame : {}".format(timeLineDict[0]["frame"]))
        except KeyError:
            self.label.setText("SplashScreen")
            self.frameNumber.setText("PyVexr")


