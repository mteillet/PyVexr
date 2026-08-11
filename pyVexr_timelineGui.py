# Timeline for PyVexr Gui

# pyVexr_timelineGui.py

import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui

timelineDictInfos = {}


def isFrameNumber(value):
    '''
    The frame label comes from the filename, so for a movie it can be the
    basename rather than a number : int() on it used to raise ValueError in
    the middle of the paint and left the ruler half drawn.
    '''
    try:
        int(value)
    except (TypeError, ValueError):
        return(False)
    return(True)

class _Timeline(QtWidgets.QWidget):
    """
    Here is the modified slider to get the actual timeline
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cachePos = []
        self.maxBuffer = 1
        # Built once : they used to be constructed for every tick of every
        # repaint, and never passed to painter.setFont anyway.
        self.frameFont = QtGui.QFont("Serif", 7, QtGui.QFont.Light)
        self.shotFont = QtGui.QFont("Serif", 10, QtGui.QFont.Bold)
        self.tickFont = QtGui.QFont("Serif", 5, QtGui.QFont.Light)
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

        # Get Values from the slider
        slider = self.parent().slider
        vmin, vmax = slider.minimum(), slider.maximum()
        value = slider.value()
        # int() obligatoire : les versions recentes de PyQt5/sip refusent les
        # flottants la ou Qt attend des entiers (QRect, drawText, ...)
        tickValue = int(value * painter.device().width() / vmax)
        if self.maxBuffer > 2:
            lenMax = self.maxBuffer - 1
        else:
            lenMax = self.maxBuffer

        # Painting the current frame background
        brush.setColor(QtGui.QColor(50,50,50))
        endFrameCurrent = int(painter.device().width() / lenMax + 1)
        rect = QtCore.QRect(tickValue,0,endFrameCurrent, painter.device().height())
        painter.fillRect(rect, brush)


        # Painting the lower bar
        brush.setColor(QtGui.QColor(225,225,225))
        rect = QtCore.QRect(0, int(painter.device().height() - 0.5), painter.device().width(), painter.device().height())
        painter.fillRect(rect, brush)

        # Painting the green buffer
        brush.setColor(QtGui.QColor(10,125,10))
        for i in self.cachePos :
            #brush.setColor(tempList[i%2])
            xStart = int((i) * painter.device().width() / lenMax)
            xEnd = int(painter.device().width() / lenMax + 1)
            rect = QtCore.QRect(xStart, int(painter.device().height() - 0.5), xEnd, painter.device().height())
            painter.fillRect(rect, brush)

        # Color back to white
        brush.setColor(QtGui.QColor(225,225,225))
        pen = painter.pen()
        pen.setColor(QtGui.QColor("white"))
        painter.setPen(pen)

        # Text following slider
        painter.setFont(self.frameFont)
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
            # Each branch fills its own rectangle : the shared fillRect at the
            # end used to re-fill whatever rect was left over from a previous
            # iteration, repainting the playhead grey on the first one.
            brush.setColor(QtGui.QColor(100,100,100))
            for i in timelineDictInfos["slider"]:
                itemPos = int(item * current)
                shotName = timelineDictInfos["slider"][current]["shot"]
                frameName = timelineDictInfos["slider"][current]["frame"]

                if (shotName != previousName):
                    # Drawing the bigger lines and the shot names for every new shot
                    painter.fillRect(
                        QtCore.QRect(itemPos, 0, 1, painter.device().height()-1),
                        brush)
                    # Drawing the shot name
                    painter.setFont(self.shotFont)
                    painter.setPen(QtGui.QColor(200,200,200))
                    painter.drawText(itemPos+1, 30, "Shot : {}".format(shotName))

                    previousName = shotName
                elif isFrameNumber(frameName) and ((int(frameName) % 5) == 0):
                    # Drawing the bigger lines every 5 frames
                    painter.fillRect(QtCore.QRect(itemPos, 6, 1, 19), brush)
                    painter.setFont(self.tickFont)
                    painter.setPen(QtGui.QColor(100,100,100))
                    painter.drawText(itemPos+1, 18, "{}".format(frameName))
                else:
                    # Drawing the other individual frames
                    painter.fillRect(QtCore.QRect(itemPos, 13, 1, 5), brush)
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
        # The width can still be 0 before the first layout, and the previous
        # clamping decremented almost every position by one, so clicking the
        # timeline always landed one frame early (and on -1 at the far left).
        width = max(1, self._timeline.width())
        val = round(pos.x() / width * self.slider.maximum())

        return(max(self.slider.minimum(), min(val, self.slider.maximum())))

    def returnFrame(self, number):
        #print(number)
        try:
            (timelineDictInfos["slider"])
            if number >= len(timelineDictInfos["slider"]):
                return(timelineDictInfos["slider"][number-1]["path"])
            else:
                return(timelineDictInfos["slider"][number]["path"])
        except KeyError:
            #print("returning default image")
            return("imgs/pyVexrSplashScreen_v002.exr")

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


