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
        painter.drawText(tickValue+2, 13, "{}".format(str(value).zfill(4)))

        # Bar following slider
        rect = QtCore.QRect(tickValue,0,1, painter.device().height())
        painter.fillRect(rect, brush)

        painter.end()


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
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._timeline= _Timeline()
        self.slider.valueChanged.connect(self.refreshSliderInfos)
        self.slider.valueChanged.connect(self._timeline._trigger_refresh)

        textLayout.addWidget(self.label)
        textLayout.addStretch()
        textLayout.addWidget(self.frameNumber)
        layout.addWidget(self._timeline)
        layout.addWidget(self.slider)

        mainLayout.addLayout(textLayout)
        mainLayout.addLayout(layout)

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

    def returnFrame(self, number):
        #print(number)
        try:
            (timelineDictInfos["slider"])
            if number >= len(timelineDictInfos["slider"]):
                return(timelineDictInfos["slider"][number-1]["path"])
            else:
                return(timelineDictInfos["slider"][number]["path"])
        except KeyError:
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


