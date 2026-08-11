# Secondary windows of PyVexr

# pyVexr_popups.py
#
# These used to live in pyVexr_gui.py and reach for its module level "widget"
# global. They now receive the main window as their first argument.

import os

from PyQt5 import QtCore, QtGui, QtWidgets

import json

import PyOpenColorIO as OCIO

from pyVexr_main import (exrListChannels, getLooks, initOcio2,
                         layerContactSheetBackend)
from pyVexr_paths import readPreferences, writableConfigPath


class ExposurePopup(QtWidgets.QWidget):
    def __init__(self, viewer, *args, **kwargs):
        self.viewer = viewer
        super(ExposurePopup, self).__init__(*args, **kwargs)
        self.setWindowTitle("Set custom Exposure")
        self.setFixedWidth(500)
        self.setFixedHeight(50)

        self.setStyleSheet("color: white; background-color: rgb(11,11,11)")

        layout = QtWidgets.QVBoxLayout()
        textLayout = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel("Enter Exposure : ")
        self.spin = QtWidgets.QDoubleSpinBox()
        self.spin.setLocale(QtCore.QLocale("English"))
        self.spin.setSingleStep(0.5)
        self.spin.setMinimum(-1000)
        self.spin.setMaximum(1000)

        textLayout.addWidget(self.label)
        textLayout.addStretch()
        textLayout.addWidget(self.spin)
        
        layout.addLayout(textLayout)

        self.setLayout(layout)

class SaturationPopup(QtWidgets.QWidget):
    def __init__(self, viewer, *args, **kwargs):
        self.viewer = viewer
        super(SaturationPopup, self).__init__(*args, **kwargs)
        self.setWindowTitle("Set custom saturation")
        self.setFixedWidth(500)
        self.setFixedHeight(50)

        self.setStyleSheet("color: white; background-color: rgb(11,11,11)")

        layout = QtWidgets.QVBoxLayout()
        textLayout = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel("Enter Saturation : ")
        self.spin = QtWidgets.QDoubleSpinBox()
        self.spin.setLocale(QtCore.QLocale("English"))
        self.spin.setSingleStep(0.25)
        self.spin.setValue(1)
        self.spin.setMinimum(0)
        self.spin.setMaximum(1000)

        textLayout.addWidget(self.label)
        textLayout.addStretch()
        textLayout.addWidget(self.spin)
        
        layout.addLayout(textLayout)

        self.setLayout(layout)

class ContactSheetPopup(QtWidgets.QWidget):
    def __init__(self, viewer, *args, **kwargs):
        self.viewer = viewer
        super(ContactSheetPopup, self).__init__()
        self.setWindowTitle("Layer Contact Sheet Menu")

        self.setStyleSheet("color: white; background-color: rgb(11,11,11)")

        self.channelSelection = []

        layout = QtWidgets.QVBoxLayout()

        self.toggleLayout = QtWidgets.QHBoxLayout()
        self.titleLayout = QtWidgets.QHBoxLayout()
        self.channelsLayout = QtWidgets.QGridLayout()
        self.okLayout = QtWidgets.QHBoxLayout()

        self.titleLabel = QtWidgets.QLabel("Select layers you want to have for contact sheet \n Warning, the more layers you select, the slower it will be to compute")
        #self.hintLabel = QtWidgets.QLabel("Warning, the more layers you select, the slower it will be to compute")

        # Listing the channels
        currentPos = (self.viewer.frameNumber.slider.value())
        frame = self.viewer.frameNumber.returnFrame(currentPos)
        investigate = [frame]
        channelList = exrListChannels(investigate)
        #print(channels)
        channelBtns = []
        for chan in channelList:
            currentBtn = QtWidgets.QPushButton(chan)
            currentBtn.setCheckable(True)
            currentBtn.clicked.connect(self.chanBtnClicked)
            channelBtns.append(currentBtn)

        self.toggleBtn = QtWidgets.QPushButton("Toggle Layer Contact Sheet Mode")
        self.toggleBtn.setCheckable(True)
        self.toggleBtn.setChecked(self.viewer.imgDict["ContactSheet"])
        self.toggleBtn.clicked.connect(self.contactSheetMode)
        # No synthetic click here : a fresh checkable button is always
        # unchecked, so this used to switch the viewer into contact sheet mode
        # and reset the whole cache merely by opening the window.
        self.okBtn = QtWidgets.QPushButton("Ok")
        self.okBtn.clicked.connect(self.okBtnClicked)

        
        # LAYOUT
        self.toggleLayout.addWidget(self.toggleBtn)
        self.titleLayout.addStretch()
        self.titleLayout.addWidget(self.titleLabel)
        #self.titleLayout.addWidget(self.hintLabel)
        self.titleLayout.addStretch()

        #self.channelsLayout.addStretch()
        for i in channelBtns:
            self.channelsLayout.addWidget(i)
        #self.channelsLayout.addStretch()
        
        self.okLayout.addStretch()
        self.okLayout.addWidget(self.okBtn)
        self.okLayout.addStretch()

        layout.addLayout(self.toggleLayout)
        layout.addStretch()
        layout.addLayout(self.titleLayout)
        layout.addStretch()
        layout.addLayout(self.channelsLayout)
        layout.addStretch()
        layout.addLayout(self.okLayout)


        self.setLayout(layout)

    ###############################
    # Code for the Slot functions #
    ###############################
    @QtCore.pyqtSlot()
    def chanBtnClicked(self):
        '''
        Responsible for adding the selected channels to the self.channelSelection list
        Also changes the btns color depending on their pressed state
        '''
        #self.channelSelection
        sender = self.sender()
        chanClicked = sender.text()

        #print(sender.isChecked())
        if (sender.isChecked()):
            sender.setStyleSheet("background-color: rgb(1,1,221)")
        else:
            sender.setStyleSheet("background-color: rgb(11,11,11)")


        if (chanClicked in self.channelSelection):
            self.channelSelection.remove(chanClicked)
        else:
            self.channelSelection.append(chanClicked)

        self.viewer.imgDict["ContactSheetChannels"] = self.channelSelection

    def contactSheetMode(self):
        '''
        Responsible for switching the image buffer generation to layercontactsheet mode
        '''
        if self.toggleBtn.isChecked():
            #print("LayerContactSheet mode is on")
            self.toggleBtn.setStyleSheet("background-color: rgb(1,1,221)")
            self.viewer.imgDict["ContactSheet"] = True
        else:
            #print("LayerContactSheet mode is off")
            self.toggleBtn.setStyleSheet("background-color: rgb(11,11,11)")
            self.viewer.imgDict["ContactSheet"] = False
            
        # Reset buffer for change
        self.viewer.checkIfBufferStateChanged()

    def okBtnClicked(self):
        '''
        Responsible for sending the list to backend and returning the image to put in the viewer
        '''
        currentPos = (self.viewer.frameNumber.slider.value())
        frame = self.viewer.frameNumber.returnFrame(currentPos)

        # Passing the chan list again to the widget imgList dict
        self.viewer.imgDict["ContactSheetChannels"] = self.channelSelection

        self.viewer.imgDict["path"] = [frame]

        #print(self.channelSelection)
        tempImg = layerContactSheetBackend(self.channelSelection, self.viewer.imgDict)
        
        convertToQt = QtGui.QImage(tempImg[0], tempImg[1], tempImg[2], tempImg[3], QtGui.QImage.Format_RGB888)
        self.viewer.image.setPixmap(QtGui.QPixmap.fromImage(convertToQt))

        self.viewer.checkIfBufferStateChanged()

        self.viewer.imgDict["buffer"][currentPos] = tempImg 


class InfosPopup(QtWidgets.QWidget):
    def __init__(self, viewer, *args, **kwargs):
        self.viewer = viewer
        super(InfosPopup, self).__init__(*args, **kwargs)
        self.setWindowTitle("Infos:")

        self.setStyleSheet("color: white; background-color: rgb(11,11,11)")

        layout = QtWidgets.QVBoxLayout()
        self.titleLayout = QtWidgets.QHBoxLayout()
        self.aboutLayout = QtWidgets.QHBoxLayout()
        self.thanksLayout = QtWidgets.QHBoxLayout()
        self.contactLayout = QtWidgets.QVBoxLayout()
        self.versionLayout = QtWidgets.QHBoxLayout()

        self.infoTitle = QtWidgets.QLabel("About:")
        self.aboutLabel = QtWidgets.QLabel("PyVexr is a lighthweight, simple GUI application to preview your EXR shots\nor sequences easily with an easy to access OCIO setup.\n\nBuilt using Python, C++, PyQt5, OpenCV2, OpenExr, and OCIO version2.")
        self.thanksLabel = QtWidgets.QLabel("\nThanks to Dorian Douaud for making the PyVexr logo.\nThanks to Elsksa and MrLixm for their feedback, advices,\nand help concerning OCIO and how it is handleld in the PyVexr.\nThanks to Sacha Duru for his help regarding PyQt.")
        self.contactLabel = QtWidgets.QLabel("\nContact :")
        self.mailLabel = QtWidgets.QLabel("Mail : <a href='mailto::martin.teillet@hotmail.fr'>martin.teillet@hotmail.fr</a>")
        self.githubLabel = QtWidgets.QLabel("Github : <a href='https://github.com/mteillet/PyVexr'>https://github.com/mteillet/PyVexr</a>")
        self.versionLabel = QtWidgets.QLabel("PyVexr - Python Open Exr Viewer - version 0.0.5-Alpha.\nDeveloped by Martin Teillet.")
        self.mailLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.githubLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.titleLayout.addWidget(self.infoTitle)
        self.aboutLayout.addWidget(self.aboutLabel)
        self.thanksLayout.addWidget(self.thanksLabel)
        self.contactLayout.addWidget(self.contactLabel)
        self.contactLayout.addWidget(self.mailLabel)
        self.contactLayout.addWidget(self.githubLabel)
        self.versionLayout.addWidget(self.versionLabel)
        self.titleLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.aboutLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.thanksLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.versionLayout.setAlignment(QtCore.Qt.AlignCenter)

        layout.addLayout(self.titleLayout)
        layout.addLayout(self.aboutLayout)
        layout.addStretch()
        layout.addLayout(self.thanksLayout)
        layout.addStretch()
        layout.addLayout(self.contactLayout)
        layout.addStretch()
        layout.addLayout(self.versionLayout)
        self.setLayout(layout)

class BufferPopup(QtWidgets.QWidget):
    def __init__(self, viewer, *args, **kwargs):
        self.viewer = viewer
        super(BufferPopup, self).__init__(*args, **kwargs)
        self.setWindowTitle("Buffer Settings")

        self.setStyleSheet("color: white; background-color: rgb(11,11,11)")

        layout = QtWidgets.QVBoxLayout()
        self.threadLayout = QtWidgets.QHBoxLayout()
        self.batchLayout = QtWidgets.QHBoxLayout()
        self.memoryLayout = QtWidgets.QHBoxLayout()

        # Number of threads. The minimum is one and the signal is connected
        # after setValue : the box used to accept zero, which stops buffering
        # for good, and applied its default value on the way in.
        self.threadNumberLabel = QtWidgets.QLabel("Number of threads :")
        self.threadNumber = QtWidgets.QSpinBox()
        self.threadNumber.setMinimum(1)
        self.threadNumber.setMaximum(max(1, self.viewer.maxThreads))
        self.threadNumber.setValue(self.viewer.threadpool.maxThreadCount())
        self.threadNumber.valueChanged.connect(self.updateThreads)

        # Size of buffer batch
        self.threadBatchLabel = QtWidgets.QLabel("Buffer Batch Size for heavy EXRs :")
        self.threadBatch = QtWidgets.QSpinBox()
        self.threadBatch.setMinimum(1)
        self.threadBatch.setMaximum(9999)
        self.threadBatch.setValue(self.viewer.bufferRange)
        self.threadBatch.valueChanged.connect(self.updateBatchSize)

        # Memory the cache is allowed to hold
        self.memoryLabel = QtWidgets.QLabel("Cache memory budget (MB) :")
        self.memoryBudget = QtWidgets.QSpinBox()
        self.memoryBudget.setMinimum(64)
        self.memoryBudget.setMaximum(1024 * 1024)
        self.memoryBudget.setSingleStep(256)
        self.memoryBudget.setValue(int(self.viewer.bufferBudgetBytes / (1024 * 1024)))
        self.memoryBudget.valueChanged.connect(self.updateMemoryBudget)

        self.threadLayout.addWidget(self.threadNumberLabel)
        self.threadLayout.addStretch()
        self.threadLayout.addWidget(self.threadNumber)
        self.batchLayout.addWidget(self.threadBatchLabel)
        self.batchLayout.addStretch()
        self.batchLayout.addWidget(self.threadBatch)
        self.memoryLayout.addWidget(self.memoryLabel)
        self.memoryLayout.addStretch()
        self.memoryLayout.addWidget(self.memoryBudget)
        layout.addLayout(self.threadLayout)
        layout.addLayout(self.batchLayout)
        layout.addLayout(self.memoryLayout)
        self.setLayout(layout)

    ###############################
    # Code for the Slot functions #
    ###############################
    @QtCore.pyqtSlot()
    def updateThreads(self):
        #print("updating thread numbers")
        #print(self.threadNumber.value())
        self.viewer.threadpool.setMaxThreadCount(self.threadNumber.value())

    def updateBatchSize(self):
        #print(self.threadBatch.value())
        self.viewer.bufferRange = self.threadBatch.value()

    def updateMemoryBudget(self):
        self.viewer.bufferBudgetBytes = self.memoryBudget.value() * 1024 * 1024
        self.viewer.enforceBufferBudget()
 
class OcioPopup(QtWidgets.QWidget):
    def __init__(self, viewer, *args, **kwargs):
        self.viewer = viewer
        super(OcioPopup, self).__init__(*args, **kwargs)
        self.setWindowTitle("OpenColorIO Settings")

        self.setStyleSheet("color: white; background-color: rgb(11,11,11)")

        layout = QtWidgets.QVBoxLayout()
        self.dropDownLayout = QtWidgets.QVBoxLayout()
        self.ocioLayout = QtWidgets.QHBoxLayout()
        self.csLayout = QtWidgets.QHBoxLayout()
        self.inputLayout = QtWidgets.QHBoxLayout()
        self.displayLayout = QtWidgets.QHBoxLayout()
        self.viewLayout = QtWidgets.QHBoxLayout()
        self.btnsLayout = QtWidgets.QHBoxLayout()

        self.ocioLabel = QtWidgets.QLabel("Ocio Path")
        self.ocioPath = QtWidgets.QLineEdit(self.viewer.imgDict["ocioVar"])
        self.ocioPath.returnPressed.connect(self.pathChanged)
        self.labelCS = QtWidgets.QLabel("Color Space")
        self.comboCS = QtWidgets.QComboBox()
        self.comboCS.currentIndexChanged.connect(self.onCsChanged)
        self.labelInput = QtWidgets.QLabel("Input Interpretation")
        self.comboInput = QtWidgets.QComboBox()
        self.comboInput.currentIndexChanged.connect(self.onAnyChanged)
        self.labelDisplay = QtWidgets.QLabel("Display")
        self.comboDisplay = QtWidgets.QComboBox()
        self.comboDisplay.currentIndexChanged.connect(self.onAnyChanged)
        self.labelView = QtWidgets.QLabel("Look")
        self.comboView = QtWidgets.QComboBox()
        self.comboView.currentIndexChanged.connect(self.onAnyChanged)

        

        # Settings as they were when the window opened, so Cancel can put them
        # back. Filling the combos below emits currentIndexChanged, which used
        # to overwrite the viewer settings with the first item of each list
        # before the user had touched anything.
        self.previousOcio = dict(self.viewer.imgDict["ocio"])

        # Clearing the previous contents of menus
        for combo in (self.comboCS, self.comboInput, self.comboDisplay,
                      self.comboView):
            combo.blockSignals(True)
            combo.clear()

        colorSpaces,inputInterp,displays = initOcio2(self.viewer.imgDict["ocioVar"])
        for i in colorSpaces:
            self.comboCS.addItem(i)
        for i in inputInterp:
            self.comboInput.addItem(i)
        for i in displays:
            self.comboDisplay.addItem(i)

        # Show what the viewer is actually using rather than the first entry.
        self.comboCS.setCurrentText(self.previousOcio["ocioOut"])
        self.comboInput.setCurrentText(self.previousOcio["ocioIn"])
        self.comboDisplay.setCurrentText(self.previousOcio["ocioDisplay"])
        for look in getLooks(self.viewer.imgDict["ocioVar"],
                             self.comboCS.currentText()):
            self.comboView.addItem(look)
        self.comboView.setCurrentText(self.previousOcio["ocioLook"])

        for combo in (self.comboCS, self.comboInput, self.comboDisplay,
                      self.comboView):
            combo.blockSignals(False)


        self.okBtn = QtWidgets.QPushButton("Ok")
        self.okBtn.clicked.connect(self.okClicked)
        self.cancelBtn = QtWidgets.QPushButton("Cancel")
        self.cancelBtn.clicked.connect(self.cancelClicked)
        self.saveBtn = QtWidgets.QPushButton("Save Config")
        self.saveBtn.clicked.connect(self.saveConfigClicked)
        self.okBtn.setFocus()

        self.checkIfJsonExists()

        self.ocioLayout.addWidget(self.ocioLabel)
        self.ocioLayout.addStretch()
        self.ocioLayout.addWidget(self.ocioPath)
        self.csLayout.addWidget(self.labelCS)
        self.csLayout.addStretch()
        self.csLayout.addWidget(self.comboCS)
        self.inputLayout.addWidget(self.labelInput)
        self.inputLayout.addStretch()
        self.inputLayout.addWidget(self.comboInput)
        self.displayLayout.addWidget(self.labelDisplay) 
        self.displayLayout.addStretch()
        self.displayLayout.addWidget(self.comboDisplay)
        self.viewLayout.addWidget(self.labelView)
        self.viewLayout.addStretch()
        self.viewLayout.addWidget(self.comboView)
        self.btnsLayout.addWidget(self.okBtn)
        self.btnsLayout.addStretch()
        self.btnsLayout.addWidget(self.saveBtn)
        self.btnsLayout.addStretch()
        self.btnsLayout.addWidget(self.cancelBtn)

        self.dropDownLayout.addLayout(self.ocioLayout)
        self.dropDownLayout.addStretch()
        self.dropDownLayout.addLayout(self.csLayout)
        self.dropDownLayout.addLayout(self.inputLayout)
        self.dropDownLayout.addLayout(self.viewLayout)
        self.dropDownLayout.addLayout(self.displayLayout)
        self.dropDownLayout.addStretch()
        self.dropDownLayout.addLayout(self.btnsLayout)

        layout.addLayout(self.dropDownLayout)

        self.setLayout(layout)

    ###############################
    # Code for the Slot functions #
    ###############################
    @QtCore.pyqtSlot()
    def pathChanged(self):
        previousOCIOvar = self.viewer.imgDict["ocioVar"]
        self.viewer.imgDict["ocioVar"] = self.ocioPath.text()

        try :
            colorSpaces,inputInterp,displays = initOcio2(self.viewer.imgDict["ocioVar"])
            #print(colorSpaces)
            #print(inputInterp)
            #print(displays)
            self.comboCS.clear()
            self.comboInput.clear()
            self.comboDisplay.clear()
            self.comboView.clear()
            for i in colorSpaces:
                self.comboCS.addItem(i)
            for i in inputInterp:
                self.comboInput.addItem(i)
            for i in displays:
                self.comboDisplay.addItem(i)

            self.onCsChanged()
            self.onAnyChanged()
        except (OSError, ValueError, OCIO.Exception):
            self.errorOcio(self.viewer.imgDict["ocioVar"])
            self.viewer.imgDict["ocioVar"] = previousOCIOvar
            # Turn off OCIO button
            #if self.viewer.ocioToggle.isChecked():
            #    self.viewer.ocioToggle.click()

    def errorOcio(self, path):
        err = QtWidgets.QMessageBox()
        err.setIcon(QtWidgets.QMessageBox.Critical)
        err.setText("ERROR : {} is not a valid ocio file".format(path))
        err.setWindowTitle("OCIO path error !")
        err.exec()

    def onCsChanged(self):
        cs = (self.comboCS.currentText())
        looks = getLooks(self.viewer.imgDict["ocioVar"], cs)
        self.comboView.clear()
        
        for i in looks:
            self.comboView.addItem(i)

    def onAnyChanged(self):
        #print(self.comboInput.currentText())
        self.viewer.imgDict["ocio"]["ocioIn"] = self.comboInput.currentText()
        self.viewer.imgDict["ocio"]["ocioOut"] = self.comboCS.currentText()
        self.viewer.imgDict["ocio"]["ocioDisplay"] = self.comboDisplay.currentText()
        self.viewer.imgDict["ocio"]["ocioLook"] = self.comboView.currentText()

    def okClicked(self):
        self.viewer.refreshImg()

    def saveConfigClicked(self):
        jsonPath = writableConfigPath()
        absoluteOcioPath = (os.path.realpath(self.ocioPath.text()))

        # The ocio config has to exist, otherwise the saved preferences make
        # the next start fall back to the defaults anyway.
        if (not os.path.exists(absoluteOcioPath)):
            print("Not saving : {} does not exist".format(absoluteOcioPath))
            return

        if (os.path.exists(jsonPath)):
            print("Config exists, overriding")
        else:
            print("Creating new config")

        jsonData = {}
        jsonData["ocioVar"] = absoluteOcioPath
        jsonData["ocioIn"] = self.comboInput.currentText()
        jsonData["ocioOut"] = self.comboCS.currentText()
        jsonData["ocioDisplay"] = self.comboDisplay.currentText()
        jsonData["ocioLook"] = self.comboView.currentText()
        #print(jsonData)
        try:
            with open(jsonPath, "w") as file:
                json.dump(jsonData, file)
        except OSError as error:
            # Happens on a read only install (system package, /opt...).
            print("Could not save the preferences : {}".format(error))

    def checkIfJsonExists(self):
        # Same reader as the main window : incomplete or stale preferences are
        # ignored rather than raising in the middle of building the window.
        config = readPreferences()
        if config is None:
            return

        self.ocioPath.setText(config["ocioVar"])
        self.comboInput.setCurrentText(config["ocioIn"])
        self.comboCS.setCurrentText(config["ocioOut"])
        self.comboDisplay.setCurrentText(config["ocioDisplay"])
        self.comboView.setCurrentText(config["ocioLook"])


    def cancelClicked(self):
        # Put back the settings the viewer had when the window opened : the
        # combos apply their changes live, so closing without this left the
        # image on whatever was last hovered in the menus.
        self.viewer.imgDict["ocio"].update(self.previousOcio)
        self.viewer.refreshImg()
        self.close()
