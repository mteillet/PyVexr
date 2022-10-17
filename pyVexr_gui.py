# Main GUI for pyVexr

# PyVexr_gui.py

import sys
import os
import json
import time
from math import sqrt
from PyQt5 import QtWidgets, QtCore, QtGui
from pyVexr_main import loadImg, interpretRectangle, exrListChannels, seqFromPath, initOcio2, getLooks, bufferBackEnd 
from pyVexr_timelineGui import Timeline

# Subclassing graphicsView in order to be able to track mouse movements in the scene
class graphicsView(QtWidgets.QGraphicsView):
    '''
    Graphics view, window displaying the actual image
    '''
    def __init__ (self, parent=None):
        super(graphicsView, self).__init__ (parent)
        #self.setAcceptDrops(True)
        
        # Initial scene rect
        self.defaultSceneRect = []

        # SHORTCUTS
        self.openShortCut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self)
        self.openShortCut.activated.connect(self.openFilesShortcut)
        self.channelShortCut = QtWidgets.QShortcut(QtGui.QKeySequence("C"), self)
        self.channelShortCut.activated.connect(self.channelsShortcut)
        self.versionShortCut = QtWidgets.QShortcut(QtGui.QKeySequence("V"), self)
        self.versionShortCut.activated.connect(self.versionsShortcut)



        # Active keys dictionnary
        self.activeKeys = {}
        self.activeKeys[QtCore.Qt.Key_A] = False
        self.activeKeys[QtCore.Qt.Key_B] = False
        self.activeKeys[QtCore.Qt.Key_C] = False
        self.activeKeys[QtCore.Qt.Key_D] = False
        self.activeKeys[QtCore.Qt.Key_E] = False
        self.activeKeys[QtCore.Qt.Key_F] = False
        # Alt key
        self.activeKeys[16777251] = False
        # Ctrl key
        self.activeKeys[16777249] = False
        # Shitf key 
        self.activeKeys[16777248] = False
        # + and - keys
        self.activeKeys[43] = False
        self.activeKeys[45] = False


        # Active mouse dictionnary
        self.activeMouse = {}
        self.activeMouse[QtCore.Qt.LeftButton] = False
        self.activeMouse[QtCore.Qt.RightButton] = False

        # Last Action dict
        self.lastAction = {}
        self.lastAction["click"] = None

        # Mouse Move list [x, y]
        self.mouseMove = [[],[]]

        self.installEventFilter(self)
        self.setSceneRect(-1000, -1000, 11000, 11000)

    ###############################
    # Code for the Slot functions #
    ###############################
    @QtCore.pyqtSlot()
    def eventFilter(self, object, event):
        '''
        Forcing focus on itself if it is lost in order to avoid press and release of the Alt Key 2 in times
        '''
        if event.type() == QtCore.QEvent.FocusIn:
            pass
        elif (event.type() == QtCore.QEvent.FocusOut) & (self.activeKeys[16777251] == True):
            #print("Focus is lost")
            self.setFocus()
            self.activeKeys[16777251] = False
            #print(app.focusWidget().objectName())

        return(False)



    def mousePressEvent(self, event):
        if event.button() in self.activeMouse:
            self.activeMouse[event.button()] = True
        self.update()


    def mouseReleaseEvent(self, event):
        if event.button() in self.activeMouse:
            self.activeMouse[event.button()] = False
        self.mouseMove[0] = []
        self.mouseMove[1] = []
            
        if (self.lastAction["click"] == "exposure") | (self.lastAction["click"] == "saturation"):
            widget.refreshImg()
            # Reset the last action
            self.lastAction["click"] == None

        self.update()

    def keyPressEvent(self, event):
        #print("GraphicsView " + str(event.key()))
        if event.key() in self.activeKeys:
            self.activeKeys[event.key()] = True
        #print("pressed {}".format(event.key()))
        if event.key() == QtCore.Qt.Key_E:
            widget.showExposureText()
        if event.key() == QtCore.Qt.Key_S:
            widget.showSaturationText()
        # Expo change if key hit is + of -
        if (event.key() == 43) | (event.key() == 45) | (event.key() == 48):
            # Boost expo
            widget.exposureChange(event.key())
            widget.satChange(event.key())
        # Mirror image on X if Shift + X
        if ((self.activeKeys[16777248]) & (event.key() == 88)):
            widget.mirrorXToggle()
        if ((self.activeKeys[16777248]) & (event.key() == 89)):
            widget.mirrorYToggle()
        # RGBA switch channels
        if (event.key() == 82):
            widget.switchChannelR()
        if (event.key() == 71):
            widget.switchChannelG()
        if (event.key() == 66):
            widget.switchChannelB()
        if (event.key() == 65):
            widget.switchChannelA()
        if (event.key() == 76):
            widget.switchChannelY()
        # Play and frame jumps
        if (event.key() == 16777236):
            if (self.activeKeys[16777248]):
                widget.jumpGapForward()
            elif (self.activeKeys[16777249]):
                print("jump end of shot")
            else:
                widget.jumpFrameForward()
        if (event.key() == 16777234):
            if (self.activeKeys[16777248]):
                widget.jumpGapBackward()
            elif (self.activeKeys[16777249]):
                print("jump start of shot")
            else:
                widget.jumpFrameBack()


    def keyReleaseEvent(self, event):
        if event.key() in self.activeKeys:
            self.activeKeys[event.key()] = False   
        #print("released {}".format(event.key()))

        # F for recenter
        if str(event.key()) == str(70):
            #print("Key is F")
            # Reset zoom
            self.resetTransform()
            # Reset position
            widget.FrameInView()

    
    def mouseMoveEvent(self, event):
        # Storing the initial scene rect
        if len(self.defaultSceneRect) == 0:
            temp = interpretRectangle(str(self.sceneRect()))
            #print(self.sceneRect())
            for val in temp:
                self.defaultSceneRect.append(val)
            #print(self.defaultSceneRect)

        # Slide values
        if (self.activeKeys[16777251] == False) & (self.activeMouse[QtCore.Qt.LeftButton] == True) & (self.activeKeys[16777249] == False):
            self.mouseMove[0].append(event.x())
            if (len(self.mouseMove[0]) >= 2):
                mouseMoveX = (self.mouseMove[0][1] - self.mouseMove[0][0])
                # Exposure slide
                if (widget.exposureText.isVisible() == True):
                    widget.imgDict["exposure"] = widget.imgDict["exposure"] + (mouseMoveX * 0.01)
                    widget.updateExposure()
                    # Setting last action as exposure
                    self.lastAction["click"] = "exposure"
                # Saturation slide
                elif (widget.saturationText.isVisible() == True):
                    widget.imgDict["saturation"] = widget.imgDict["saturation"] + (mouseMoveX * 0.01)
                    widget.updateSaturation()
                    # Setting last action as exposure
                    self.lastAction["click"] = "saturation"
                # Frame slide
                else:
                    widget.frameNumber.slider.setValue(widget.frameNumber.slider.value() + mouseMoveX)
                # Reset mouse move X
                self.mouseMove[0] = []
                #print(mouseMoveX)

        # Translate view
        sceneCoordinates = interpretRectangle(str(self.sceneRect()))
        if (self.activeKeys[16777251] == True) & (self.activeMouse[QtCore.Qt.LeftButton] == True):
            #print("translate {} - {}".format(event.x(), event.y()))
            sceneCoordinates = interpretRectangle(str(self.sceneRect()))
            position = QtCore.QPointF(event.pos())
            self.mouseMove[0].append(event.x())
            self.mouseMove[1].append(event.y())
            #print(self.mouseMove)
            if ((len(self.mouseMove[0]) >= 2) & (len(self.mouseMove[1]) >= 2) ):
                #print("SHOULD MOVE")
                mouseMoveX =  (self.mouseMove[0][1] - self.mouseMove[0][0])
                mouseMoveY =  (self.mouseMove[1][1] - self.mouseMove[1][0]) 
                # Moving the Graphics view adding the mousemov vars to the current coordinates of the scene rect
                sceneCoordinates = interpretRectangle(str(self.sceneRect()))
                #self.setSceneRect(sceneCoordinates[0]-mouseMoveX,sceneCoordinates[1]-mouseMoveY,sceneCoordinates[2]-mouseMoveX,sceneCoordinates[3]-mouseMoveY)
                self.horizontalScrollBar().setSliderPosition(self.horizontalScrollBar().sliderPosition() - mouseMoveX)
                self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition() - mouseMoveY)
                self.mouseMove[0] = []
                self.mouseMove[1] = []

        # Zoom view
        if (self.activeKeys[16777249] == True) & (self.activeMouse[QtCore.Qt.LeftButton] == True):
            #print("zoom ! {} - {}".format(event.x(), event.y()))
            # Storing the mouse moves in a declared list
            position = QtCore.QPointF(event.pos())
            
            self.mouseMove[0].append(event.x())
            self.mouseMove[1].append(event.y())

            if(len(self.mouseMove[0]) >= 2) & (len(self.mouseMove[1]) >= 2):
                #print("Mouse Moved")
                direction = (self.mouseMove[1][1] - self.mouseMove[1][0]) + (self.mouseMove[0][1] - self.mouseMove[0][0])
                sceneCoordinates = interpretRectangle(str(self.sceneRect()))

                # Exception for too high mouse moves
                if (direction > 10) | (direction < -10):
                    direction = 0

                # Zooming the view
                self.scale(1.0 + direction * 0.025, 1.0 + direction * 0.025)

                # Reset the mouse move lists
                self.mouseMove[0] = []
                self.mouseMove[1] = []

            
        self.update()

    def dragEnterEvent(self, event):
        if (event.mimeData().hasUrls()):
            event.accept()

    def dropEvent(self, event):
        filenames = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            # Check if file exists and is an exr
            if os.path.exists(path) == True:
                if path.endswith(".exr") == True:
                    #print("File exists {}".format(path))
                    filenames.append(url.toLocalFile())
                else:
                    # Append the default pyVexr logo
                    filenames.append("/home/martin/Documents/PYTHON/PyVexr/imgs/pyVexrSplashScreen_v002.exr")
        #print(filenames)
        widget.updateImgDict(filenames)
        widget.totalFrameLabel.setText("{}".format(widget.frameNumber.slider.maximum()))

        event.accept()

    def openFilesShortcut(self):
        #print("Open File")
        widget.openFiles()

    def channelsShortcut(self):
        #print("channels toggle")
        widget.channelsClicked()

    def versionsShortcut(self):
        #print("versionsShortcul")
        widget.versionsClicked()

class MyWidget(QtWidgets.QWidget):
    '''
    Main UI part, responsible for assembly and menus
    '''
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyVexr -- OpenExr Viewer") 
        self.setWindowIcon(QtGui.QIcon("/home/martin/Documents/PYTHON/PyVexr/imgs/pyVexr_Icon_512.jpeg"))
        self.setAcceptDrops(True)

        # ThreadPool
        self.threadpool = QtCore.QThreadPool()
        self.threadpool.setMaxThreadCount(self.threadpool.maxThreadCount() - 4)
        #self.threadpool.setMaxThreadCount(2)
        print(("Multithreading with maximum {} threads").format(self.threadpool.maxThreadCount()))

        # StyleSheet settings
        self.setStyleSheet("color: white; background-color: rgb(11,11,11)")
        self.setMouseTracking(True)
        self._zoom = 0
        
        # Global dict image related:
        self.imgDict = {}
        self.imgDict["buffer"] = []
        self.imgDict["path"] = []
        self.imgDict["ocioVar"] = "ocio/config.ocio"
        self.imgDict["ocio"] = {}
        self.imgDict["ocio"]["ocioIn"] = "Linear"
        self.imgDict["ocio"]["ocioOut"] = "Standard"
        self.imgDict["ocio"]["ocioLook"] = "None"
        self.imgDict["ocio"]["ocioDisplay"] = None
        self.imgDict["ocioToggle"] = True
        self.imgDict["channel"] = None
        self.imgDict["exposure"] = 0
        self.imgDict["saturation"] = 1
        self.imgDict["flipX"] = False
        self.imgDict["flipY"] = False
        self.imgDict["RGBA"] = "rgba"
        self.imgDict["previousShot"] = None
        self.p = None

        self.checkIfJsonExists()

        ####################################
        # Code for the PyVexr Main windows #
        ####################################

        # Focus Tracking
        app.focusChanged.connect(self.on_focusChanged)

        # Menu bar area
        self.file = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.menuBar = QtWidgets.QMenuBar()
        self.fileMenu = self.menuBar.addMenu('&File')
        self.editMenu = self.menuBar.addMenu('&Edit')
        self.windowsMenu = self.menuBar.addMenu('&Windows')
        self.expoSatMenu = self.menuBar.addMenu('&Expo/Sat')
        self.ociioMenu = self.menuBar.addMenu('&OCIO')
        # File Menu & Action
        self.openAction = self.fileMenu.addAction("Open        &-&C&t&r&l&+&O")
        self.openAction.triggered.connect(self.openFiles)
        self.openPlaylist = self.fileMenu.addAction("Open playlist")
        self.fileMenu.addSeparator()
        self.savePlaylist = self.fileMenu.addAction("Save as playlist")
        self.exportMp4 = self.fileMenu.addAction("Export as mp4")
        self.fileMenu.addSeparator()
        self.exit = self.fileMenu.addAction("Exit PyVexr")
        # Mirror Action
        self.channelMenu = self.editMenu.addMenu("Current Channel")
        self.channelRGBA = self.channelMenu.addAction("RGBA")
        self.channelRGBA.triggered.connect(self.switchChannelRGBA)
        self.channelR = self.channelMenu.addAction("Red               &-&R")
        self.channelR.triggered.connect(self.switchChannelR)
        self.channelG = self.channelMenu.addAction("Green           &-&G")
        self.channelG.triggered.connect(self.switchChannelG)
        self.channelB = self.channelMenu.addAction("Blue              &-&B")
        self.channelB.triggered.connect(self.switchChannelB)
        self.channelA = self.channelMenu.addAction("Alpha            &-&A")
        self.channelA.triggered.connect(self.switchChannelA)
        self.channelL = self.channelMenu.addAction("Luminance  &-&L")
        self.channelL.triggered.connect(self.switchChannelY)
        self.mirror = self.editMenu.addMenu("Mirror/Flip image")
        self.mirrorX = self.mirror.addAction("Flip X              &-&S&h&i&f&t&+&X")
        self.mirrorX.triggered.connect(self.mirrorXToggle)
        self.mirrorY = self.mirror.addAction("Flip Y              &-&S&h&i&f&t&+&Y")
        self.contactSheet = self.editMenu.addAction("Contact Sheet")
        self.mirrorY.triggered.connect(self.mirrorYToggle)
        self.fileMenu.addSeparator()
        self.infosAction = self.editMenu.addAction("Help")
        # Exposure Actions
        self.exposureAction = self.expoSatMenu.addMenu("Exposure                  &-&E")
        self.expoUpAction = self.exposureAction.addAction("Increase Exposure      &+")
        self.expoUpAction.triggered.connect(self.exposureMenu)
        self.expoDownAction = self.exposureAction.addAction("Decrease Exposure     &-")
        self.expoDownAction.triggered.connect(self.exposureMenu)
        self.expoResetAction = self.exposureAction.addAction("Reset Exposure           &0")
        self.expoResetAction.triggered.connect(self.exposureMenu)
        self.expoCustomAction = self.exposureAction.addAction("Custom Exposure")
        self.expoCustomAction.triggered.connect(self.customExpoMenu)
        # Saturation Actions
        self.saturationAction = self.expoSatMenu.addMenu("Saturation                &-&S")
        self.satUp = self.saturationAction.addAction("Increase Saturation        &+")
        self.satUp.triggered.connect(self.saturationMenu)
        self.satDown = self.saturationAction.addAction("Decrease Saturation       &-")
        self.satDown.triggered.connect(self.saturationMenu)
        self.satReset = self.saturationAction.addAction("Reset Saturation             &0")
        self.satReset.triggered.connect(self.saturationMenu)
        self.satCustom = self.saturationAction.addAction("Custom Saturation")
        self.satCustom.triggered.connect(self.customSatMenu)
        self.channelsAction = self.windowsMenu.addAction("Channels Pannel    &-&C")
        self.versionsAction = self.windowsMenu.addAction("Versions Pannel     &-&V")
        self.channelsAction.triggered.connect(self.channelsClicked)
        self.versionsAction.triggered.connect(self.versionsClicked)
        #self.colorspaceMenu = self.menuBar.addMenu('&Colorspace')
        self.openColorIoAction = self.ociioMenu.addAction("OpenColorIO Settings")
        self.openColorIoAction.triggered.connect(self.ocioMenu)

        # Setup dict in order to retrieve selected items
        self.ocioToggle = QtWidgets.QPushButton("OCIO")
        self.ocioToggle.setCheckable(True)
        self.ocioToggle.clicked.connect(self.ocioToggleClicked)
        # init it with a click at the beginning
        self.ocioToggle.setChecked(True)
        self.ocioToggle.setStyleSheet("background-color : blue")



        # Channel area 
        self.channels = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.channels.setText("Exr Channels : ")
        self.channelsGroupBox = QtWidgets.QGroupBox()
        self.channelsDock = QtWidgets.QDockWidget("EXR Channels", self)
        self.channelsDock.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable)
        self.channelsDock.hide()
        self.channelsDock.setWidget(self.channelsGroupBox)

        # Version area 
        self.version = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.version.setText("Versions : ")
        self.versionsGroupBox = QtWidgets.QGroupBox()
        self.versionsDock = QtWidgets.QDockWidget("Versions Panne", self)
        self.versionsDock.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable)
        self.versionsDock.hide()
        self.versionsDock.setWidget(self.versionsGroupBox)


        # Graphics Scene used to have a virtual space for the objects
        self.imgZone = QtWidgets.QGraphicsScene()

        # RectWidget for tracking the view relative to the image
        self.viewArea = QtWidgets.QGraphicsRectItem(0,0,10,10)
        self.viewArea.setAcceptDrops(True)
        # Giving a color to the default rect -- only for debugging purposes
        #self.viewArea.setBrush(QtGui.QColor(255, 0, 0, 30))

        # Margins
        self.margins = QtWidgets.QGraphicsRectItem(-1000, -1000, 11000, 11000)
        #self.margins.setBrush(QtGui.QColor(0,255,0,30))

        # Exposure text, hidden by default
        self.exposureText = QtWidgets.QGraphicsTextItem("Exposure : ")
        self.exposureText.setScale(2)
        self.exposureText.setDefaultTextColor(QtGui.QColor("white"))
        self.exposureText.hide()

        # Saturation Text
        self.saturationText = QtWidgets.QGraphicsTextItem("Saturation : ")
        self.saturationText.setScale(2)
        self.saturationText.setDefaultTextColor(QtGui.QColor("white"))
        self.saturationText.hide()

        self.textCard = QtWidgets.QGraphicsRectItem(0,0,250,50)
        self.textCard.setBrush(QtGui.QColor(0,0,0,225))
        self.textCard.hide()
        
        # Putting the objects in the scene
        self.image = QtWidgets.QGraphicsPixmapItem()
        self.imgZone.addItem(self.margins)
        self.imgZone.addItem(self.image)
        self.imgZone.addItem(self.viewArea)
        self.imgZone.addItem(self.textCard)
        self.imgZone.addItem(self.exposureText)
        self.imgZone.addItem(self.saturationText)
        
        self.imgViewer = graphicsView(self)
        self.imgViewer.setScene(self.imgZone)
        self.imgViewer.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.imgViewer.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.imgViewer.setAcceptDrops(True)

        # Version area - Need to replace with a floating window
        self.version = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.version.setText("Versions")

        # Slider for the frame sequence
        #self.frameNumber = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.frameNumber = Timeline()
        self.frameNumber.slider.valueChanged.connect(self.sliderChanged)
        #self.frameNumber.setValue(101)
        #self.frameNumber.setMinimum(101)
        #self.frameNumber.setMaximum(111)
        #self.frameNumber.setTickPosition(QtWidgets.QSlider.TicksAbove)
        #self.frameNumber.setStyleSheet("color: white")
        
        # Player buttons area
        self.totalFrameLabel = QtWidgets.QLabel("Total")
        self.totalFrameLabelNext = QtWidgets.QLabel(" frames")
        self.totalFrameLabelNext.setStyleSheet("QLabel{color : grey;}")
        self.totalFrameLabelNext.setFont(QtGui.QFont("Times", 10))
        self.previousBtn = QtWidgets.QPushButton("|<")
        self.previousBtn.clicked.connect(self.jumpFrameBack)
        self.playBackBtn = QtWidgets.QPushButton("<")
        self.playBackBtn.clicked.connect(self.playBack)
        self.frameCurrent = QtWidgets.QLabel("101")
        currentPos = (self.frameNumber.slider.value())
        self.frameCurrent.setText(str(self.frameNumber.slider.value()).zfill(4))
        self.playBtn = QtWidgets.QPushButton(">")
        self.playBtn.clicked.connect(self.playForward)
        self.nextBtn = QtWidgets.QPushButton(">|")
        self.nextBtn.clicked.connect(self.jumpFrameForward)
        self.jumpBack = QtWidgets.QPushButton("<<")
        self.jumpBack.clicked.connect(self.jumpGapBackward)
        self.jumpLabel = QtWidgets.QSpinBox()
        self.jumpLabel.setValue(10)
        self.jumpForward = QtWidgets.QPushButton(">>")
        self.jumpForward.clicked.connect(self.jumpGapForward)

        #############################
        # Layout for the PyVexr GUI #
        #############################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        
        # Top Bar
        self.topBarLayout = QtWidgets.QHBoxLayout()
        self.topBarLayout.addWidget(self.menuBar)
        self.topBarLayout.addStretch()
        self.topBarLayout.addWidget(self.ocioToggle)

        # Main Center layout #
        self.centerLayout = QtWidgets.QHBoxLayout()
        self.channelsLayout = QtWidgets.QVBoxLayout()
        self.channelsLayout.addStretch()
        self.channelsLayout.addWidget(self.channels)
        self.channelsGroupBox.setLayout(self.channelsLayout)
        
        self.imgLayout = QtWidgets.QVBoxLayout()
        self.imgLayout.addWidget(self.imgViewer)
        
        self.versionsLayout = QtWidgets.QVBoxLayout()
        self.versionsLayout.addStretch()
        self.versionsLayout.addWidget(self.version)
        self.versionsGroupBox.setLayout(self.versionsLayout)

        self.centerLayout.addWidget(self.channelsDock)
        self.centerLayout.addLayout(self.imgLayout, stretch = 1)
        self.centerLayout.addWidget(self.versionsDock)

        # Bottom bars

        self.frameNumLayout = QtWidgets.QHBoxLayout()
        self.frameNumLayout.addWidget(self.frameNumber, stretch = 1)
        
        self.totalFramesLayout = QtWidgets.QHBoxLayout()
        self.totalFramesLayout.addWidget(self.totalFrameLabel)
        self.totalFramesLayout.addWidget(self.totalFrameLabelNext)


        self.playBtnsLayout = QtWidgets.QHBoxLayout()
        self.playBtnsLayout.addWidget(self.previousBtn)
        self.playBtnsLayout.addWidget(self.playBackBtn)
        self.playBtnsLayout.addWidget(self.frameCurrent)
        self.playBtnsLayout.addWidget(self.playBtn)
        self.playBtnsLayout.addWidget(self.nextBtn)

        self.jumpLayout = QtWidgets.QHBoxLayout()
        self.jumpLayout.addWidget(self.jumpBack)
        self.jumpLayout.addWidget(self.jumpLabel)
        self.jumpLayout.addWidget(self.jumpForward)

        self.playerLayout = QtWidgets.QHBoxLayout()
        self.playerLayout.addLayout(self.totalFramesLayout)
        self.playerLayout.addStretch(5)
        self.playerLayout.addLayout(self.playBtnsLayout)
        self.playerLayout.addStretch(4)
        self.playerLayout.addLayout(self.jumpLayout)

        # Main Layout
        self.mainLayout.addLayout(self.topBarLayout)
        self.mainLayout.addLayout(self.centerLayout, stretch = 1)
        self.mainLayout.addLayout(self.frameNumLayout)
        self.mainLayout.addLayout(self.playerLayout)

    ###############################
    # Code for the Slot functions #
    ###############################
    @QtCore.pyqtSlot()
    def on_focusChanged(self):
        #print(app.focusWidget().objectName())
        pass

    def bufferInit(self, seqDict):
        '''
        Init buffer size using the seqDict length
        '''
        # Reinitialize buffer
        if (len(self.imgDict["buffer"]) >> 0):
            #print("Reset Buffer")
            self.imgDict["buffer"] = []

        # Create empty buffer slots
        for shot in seqDict:
            #print(len(seqDict[shot]))
            for frame in seqDict[shot]:
                self.imgDict["buffer"].append(None)

        self.frameNumber._timeline.resetCacheDraw()

    def createBufferState(self):
        '''
        Creating a buffer state that will be used to compare
        Buffer settings and know if it needs to be reset
        '''
        # Check if there are frames in the seqDict
        if (len(self.seqDict) >> 0):
            self.bufferState = {}
            self.bufferState["frame"] = (self.seqDict.keys())
            self.bufferState["ocioIn"] = self.imgDict["ocio"]["ocioIn"]
            self.bufferState["ocioOut"] = self.imgDict["ocio"]["ocioOut"]
            self.bufferState["ocioLook"] = self.imgDict["ocio"]["ocioLook"] 
            self.bufferState["ocioDisplay"] = self.imgDict["ocio"]["ocioDisplay"]
            self.bufferState["ocioToggle"] = self.imgDict["ocioToggle"]
            self.bufferState["channel"] = self.imgDict["channel"]
            self.bufferState["exposure"] = self.imgDict["exposure"]
            self.bufferState["saturation"] = self.imgDict["saturation"]
            self.bufferState["RGBA"] = self.imgDict["RGBA"]

            #print(self.bufferState)

    def checkIfBufferStateChanged(self):
        '''
        Compares the self.bufferState with the current buffer settings
        in order to see if buffer needs to be reset or not
        '''
        #TODO
        pass


    def bufferLoad(self, seqDict):
        #print("bufferload")
        # Clear the queue if any workers have not been created yet
        self.threadpool.clear()
        # Frame path list from seqDict
        frameList = []
        for shot in seqDict:
            for frame in seqDict[shot]:
                frameList.append(frame)
        current = self.frameNumber.slider.value()

        count = 0
        if (len(frameList) >> 0):
            #for i in range(10):
            for i in frameList:
                # Reset the curent + count to not get out of list range
                if (current+count >> self.frameNumber.slider.maximum()):
                    print("NEED TO RESET THE CURRENT + COUNT")
                    current = self.frameNumber.slider.minimum()
                    count = 0
                worker = Worker(frameList, current+count, **self.imgDict)
                worker.signals.result.connect(self.queueResult)
                self.threadpool.start(worker)
                count += 1

    def queueResult(self, resultA, resultB):
        self.imgDict["buffer"][resultB] = resultA
        self.frameNumber._timeline.paintBuffer(resultB, len(self.imgDict["buffer"]))
        #print("Finished loading buffer at pos {}".format(resultB))
        

    def loadFile(self):
        #Loading frames from same nomenclature
        seqDict = seqFromPath(self.imgDict["path"])
        self.seqDict = seqDict

        self.bufferInit(seqDict)
        self.createBufferState()

        #Init the slider
        self.initSlider(seqDict)

        # Calculating the actual image from the backend
        tempImg = loadImg(self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"],self.imgDict["path"], self.imgDict["exposure"], self.imgDict["saturation"], self.imgDict["channel"], self.imgDict["RGBA"], self.imgDict["ocioVar"], self.imgDict["ocio"]["ocioDisplay"], self.imgDict["ocioToggle"])

        if len(self.imgDict["buffer"]) >> 0:
            self.imgDict["buffer"][(self.frameNumber.slider.value())] = tempImg
            #print(len(self.imgDict["buffer"]))

        #print(type(tempImg))
        convertToQt = QtGui.QImage(tempImg[0], tempImg[1], tempImg[2], tempImg[3], QtGui.QImage.Format_RGB888)

        # Set pixmap in self.image
        self.image.setPixmap(QtGui.QPixmap.fromImage(convertToQt))


        # Give the rectangle view area the coordinates of the pixmap image after the image has been loaded
        imgCoordinates = interpretRectangle(str(self.image.boundingRect()))
        self.margins.setRect(imgCoordinates[0]-imgCoordinates[2],imgCoordinates[1]-imgCoordinates[3],imgCoordinates[2] * 3,imgCoordinates[3]*3)
        self.viewArea.setRect(imgCoordinates[0]-(imgCoordinates[2]/3),imgCoordinates[1]-(imgCoordinates[3]/3),imgCoordinates[2] * 1.66,imgCoordinates[3]*1.66)

        # Fit in view after first load
        self.imgViewer.fitInView(self.viewArea, QtCore.Qt.KeepAspectRatio)

        # Check mirror state
        self.mirrorToggles()

        # Sart to fill buffer
        self.bufferLoad(seqDict)


    def FrameInView(self):
        self.imgViewer.fitInView(self.viewArea, QtCore.Qt.KeepAspectRatio)

    def changeFrame(self, frame, currentPos):
        t0 = (time.time())
        #print(self.imgDict["buffer"][currentPos])
        if (self.imgDict["buffer"][currentPos] != None):
            tempImg = self.imgDict["buffer"][currentPos]
        else:
            self.imgDict["path"][0] = frame
            self.bufferLoad(self.seqDict)
            #tempImg = self.imgDict["buffer"][currentPos]
            tempImg = loadImg(self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"],self.imgDict["path"], self.imgDict["exposure"], self.imgDict["saturation"], self.imgDict["channel"], self.imgDict["RGBA"], self.imgDict["ocioVar"], self.imgDict["ocio"]["ocioDisplay"], self.imgDict["ocioToggle"])
        convertToQt = QtGui.QImage(tempImg[0], tempImg[1], tempImg[2], tempImg[3], QtGui.QImage.Format_RGB888)

        # Set pixmap in self.image
        self.image.setPixmap(QtGui.QPixmap.fromImage(convertToQt))

        t1 = time.time()
        #print(t1 - t0)

        # Give the rectangle view area the coordinates of the pixmap image after the image has been loaded
        imgCoordinates = interpretRectangle(str(self.image.boundingRect()))
        self.viewArea.setRect(imgCoordinates[0],imgCoordinates[1],imgCoordinates[2],imgCoordinates[3])
        

    def sliderChanged(self):
        currentPos = (self.frameNumber.slider.value())
        frame = self.frameNumber.returnFrame(currentPos)
        #print(self.frameNumber)
        positionMax = (self.frameNumber.slider.maximum())
        isSameShot = True

        # Updating the layers on the new shot
        # Adding exception in case first drag and drop and the timeLineDict has not been created yet (avoid errors on splashcreen)
        try :
            if (self.timeLineDict[currentPos]["shot"] != self.imgDict["previousShot"]):
                isSameShot = False
                self.imgDict["channel"] = None
                self.imgDict["previousShot"] = self.timeLineDict[currentPos]["shot"]
                #print("DifferentShot")

        except KeyError:
            isSameShot = False
            self.imgDict["channel"] = None
            self.imgDict["previousShot"] = None


        self.changeFrame(frame, currentPos)
        self.frameCurrent.setText(str(self.frameNumber.slider.value()).zfill(4))
        self.mirrorToggles()

        if isSameShot != True:
            self.listChannels()
        
    def playForward(self):
        print("Play forward -- need multithreading for it to work")

    def playBack(self):
        print("Play back -- need multithreading for it to work")

    def jumpFrameForward(self):
        self.frameNumber.slider.setValue(self.frameNumber.slider.value()+1)

    def jumpFrameBack(self):
        self.frameNumber.slider.setValue(self.frameNumber.slider.value()-1)

    def jumpGapForward(self):
        self.frameNumber.slider.setValue(self.frameNumber.slider.value() + self.jumpLabel.value())

    def jumpGapBackward(self):
        self.frameNumber.slider.setValue(self.frameNumber.slider.value() - self.jumpLabel.value())


    def initSlider(self, seqDict):
        shotRange = {}
        # print(seqDict)
        self.timeLineDict = self.getFrames(seqDict)

        sliderStyleSheet = """
        QSlider,QSlider:enabled,QSlider:focus     {
                  background: qcolor(50,50,50,50);   }
        QSlider:item:hover    {   background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #eaa553);
                  color: #000000;              }
        QWidget:item:selected {   background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);      }
         QSlider::groove:horizontal {
                 border: 1px solid #222222;
                 background: qcolor(0,0,0,0);
                  }
          QSlider::handle:horizontal {
                  background:  qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255,255,255, 141), stop:0.497175 rgba(255,255,255, 255), stop:0.497326 rgba(255,255,255,255), stop:1 rgba(255,255,255,255));
                  width: 3px;
                   }
         """
        self.frameNumber.updateSlider(self.timeLineDict)
        #self.frameNumber.setTickInterval(1)
        self.frameNumber.setStyleSheet(sliderStyleSheet)

    def switchChannelRGBA(self):
        self.imgDict["RGBA"] = "rgba"
        #print(self.imgDict["RGBA"])
        self.updateRGBA()

    def switchChannelR(self):
        if (self.imgDict["RGBA"] != "red"):
            self.imgDict["RGBA"] = "red"
            self.updateRGBA()
        else:
            self.switchChannelRGBA()
        #print(self.imgDict["RGBA"])

    def switchChannelG(self):
        if (self.imgDict["RGBA"] != "green"):
            self.imgDict["RGBA"] = "green"
            self.updateRGBA()
        else:
            self.switchChannelRGBA()

    def switchChannelB(self):
        if (self.imgDict["RGBA"] != "blue"):
            self.imgDict["RGBA"] = "blue"
            self.updateRGBA()
        else:
            self.switchChannelRGBA()

    def switchChannelA(self):
        if (self.imgDict["RGBA"] != "alpha"):
            self.imgDict["RGBA"] = "alpha"
            self.updateRGBA()
        else:
            self.switchChannelRGBA()

    def switchChannelY(self):
        if (self.imgDict["RGBA"] != "luma"):
            self.imgDict["RGBA"] = "luma"
            self.updateRGBA()
        else:
            self.switchChannelRGBA()

    def updateRGBA(self):
        # Update display
        if self.imgDict["RGBA"] == "rgba":
            self.frameNumber.channelLabelR.setStyleSheet(self.frameNumber.styleRed)
            self.frameNumber.channelLabelG.setStyleSheet(self.frameNumber.styleGreen)
            self.frameNumber.channelLabelB.setStyleSheet(self.frameNumber.styleBlue)
            self.frameNumber.channelLabelA.setStyleSheet(self.frameNumber.styleWhite)
        if self.imgDict["RGBA"] == "red":
            self.frameNumber.channelLabelR.setStyleSheet(self.frameNumber.styleRed)
            self.frameNumber.channelLabelG.setStyleSheet(self.frameNumber.styleBlack)
            self.frameNumber.channelLabelB.setStyleSheet(self.frameNumber.styleBlack)
            self.frameNumber.channelLabelA.setStyleSheet(self.frameNumber.styleBlack)
        if self.imgDict["RGBA"] == "green":
            self.frameNumber.channelLabelR.setStyleSheet(self.frameNumber.styleBlack)
            self.frameNumber.channelLabelG.setStyleSheet(self.frameNumber.styleGreen)
            self.frameNumber.channelLabelB.setStyleSheet(self.frameNumber.styleBlack)
            self.frameNumber.channelLabelA.setStyleSheet(self.frameNumber.styleBlack)
        if self.imgDict["RGBA"] == "blue":
            self.frameNumber.channelLabelR.setStyleSheet(self.frameNumber.styleBlack)
            self.frameNumber.channelLabelG.setStyleSheet(self.frameNumber.styleBlack)
            self.frameNumber.channelLabelB.setStyleSheet(self.frameNumber.styleBlue)
            self.frameNumber.channelLabelA.setStyleSheet(self.frameNumber.styleBlack)
        if self.imgDict["RGBA"] == "alpha":
            self.frameNumber.channelLabelR.setStyleSheet(self.frameNumber.styleBlack)
            self.frameNumber.channelLabelG.setStyleSheet(self.frameNumber.styleBlack)
            self.frameNumber.channelLabelB.setStyleSheet(self.frameNumber.styleBlack)
            self.frameNumber.channelLabelA.setStyleSheet(self.frameNumber.styleWhite)
        if self.imgDict["RGBA"] == "luma":
            self.frameNumber.channelLabelLuma.show()
            self.frameNumber.channelLabelR.hide()
            self.frameNumber.channelLabelG.hide()
            self.frameNumber.channelLabelB.hide()
            self.frameNumber.channelLabelA.hide() 
        if self.imgDict["RGBA"] != "luma":
            self.frameNumber.channelLabelLuma.hide()
            self.frameNumber.channelLabelR.show()
            self.frameNumber.channelLabelG.show()
            self.frameNumber.channelLabelB.show()
            self.frameNumber.channelLabelA.show() 
        self.refreshImg()

    def mirrorXToggle(self):
        """
        Toggling the imgDict FlipX 
        """
        if self.imgDict["flipX"] == False:
            self.imgDict["flipX"] = True
        else:
            self.imgDict["flipX"] = False
        self.mirrorXAction()
        
    def mirrorXAction(self):
        """
        Actually Mirroring the image
        """
        image = (self.image.pixmap())
        mirrored = image.transformed(QtGui.QTransform().scale(-1, 1))
        self.image.setPixmap(mirrored)

    def mirrorYToggle(self):
        """
        Toggling the imgDict FlipX 
        """
        if self.imgDict["flipY"] == False:
            self.imgDict["flipY"] = True
        else:
            self.imgDict["flipY"] = False
        self.mirrorYAction()

    def mirrorYAction(self):
        """
        Actually Mirroring the image
        """
        image = (self.image.pixmap())
        mirrored = image.transformed(QtGui.QTransform().scale(1, -1))
        self.image.setPixmap(mirrored)

       
    def mirrorToggles(self):
        if self.imgDict["flipX"] == True:
            self.mirrorXAction()
        if self.imgDict["flipY"] == True:
            self.mirrorYAction()

    def getFrames(self,seqDict):
        #print(seqDict)
        self.timeLineDict = {}
        current = 0

        for shot in seqDict:
            for frame in seqDict[shot]:
                self.timeLineDict[current] = {}
                self.timeLineDict[current]["position"] = current
                self.timeLineDict[current]["shot"] = shot
                realFrame = frame.split("/")
                realFrame = ((realFrame[-1]).split("."))[-2]
                self.timeLineDict[current]["frame"] = realFrame
                self.timeLineDict[current]["path"] = frame
                current += 1

        return(self.timeLineDict)


    def updateImgDict(self, path):
        self.imgDict["path"] = path
        self.imgDict["channel"] = None
        self.loadFile()
        self.listChannels()
        self.imgDict["previousShot"] = (self.frameNumber.label.text()[7:])

    def dragEnterEvent(self, event):
        #print("drag")
        if (event.mimeData().hasFormat("text/plain")):
            #print(event)
            event.accept()

    def dropEvent(self, event):
        print("drop")
        print(event.mimeData().text())
        event.accept()


    def openFiles(self):
        dialog = QtWidgets.QFileDialog(self, caption = "Open Image")
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)

        if dialog.exec():
            filenames = dialog.selectedFiles()
            #print(filenames)
            self.imgDict["path"] = filenames
            self.loadFile()
            self.listChannels()

    def channelsClicked(self):
        #print(self.channelsDock.isVisible())
        if self.channelsDock.isVisible() == False:
            self.channelsDock.show()
        else:
            self.channelsDock.hide()

    def versionsClicked(self):
        if self.versionsDock.isVisible() == False:
            self.versionsDock.show()
        else:
            self.versionsDock.hide()

    def listChannels(self):
        channels = exrListChannels(self.imgDict["path"])
        #print(channels)

        # Removing old channelBtns if the channel Btns Var was created
        removeList = []
        for i in range(self.channelsLayout.count()):
            currentWidget = (self.channelsLayout.itemAt(i).widget())
            #print(currentWidget.__class__.__name__)
            if ((currentWidget.__class__.__name__) == "QPushButton"):
                #print("Will remove : {0}".format(currentWidget))
                removeList.append(currentWidget)
        if len(removeList) > 1:
            separator = self.channelsLayout.itemAt(self.channelsLayout.count() - 1).widget()
            self.channelsLayout.removeWidget(separator)
        for widget in removeList:
            widget.setParent(None)
            #self.channelsLayout.removeWidget(widget)

        channelBtns = []
        for chan in channels:
            self.btn = QtWidgets.QPushButton(chan)
            self.btn.clicked.connect(self.channelChange)
            self.channelsLayout.addWidget(self.btn)
        self.channelsLayout.addStretch(2)

    def channelChange(self):
        sender = self.sender()
        self.imgDict["channel"] = sender.text()
        self.imageUpdate()

    def refreshImg(self):
        # TODO
        # NEED TO CORRECT BUG
        # REFRESH IMG IS CALLED ON FRAME CHANGE IF EXPO != 0 and if SAT != 1
        #print("refreshIMG")
        # Stop threadpool in case a buffer is in progress
        self.threadpool.clear()
        self.bufferInit(self.seqDict)
        # Need to send the correct buffer frame to tempImg function instead of self.imgDict["path"]
        currentPos = (self.frameNumber.slider.value())
        frame = self.frameNumber.returnFrame(currentPos)

        self.imgDict["path"] = [frame]

        tempImg = loadImg(self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"],self.imgDict["path"], self.imgDict["exposure"], self.imgDict["saturation"],self.imgDict["channel"], self.imgDict["RGBA"], self.imgDict["ocioVar"], self.imgDict["ocio"]["ocioDisplay"], self.imgDict["ocioToggle"])
        convertToQt = QtGui.QImage(tempImg[0], tempImg[1], tempImg[2], tempImg[3], QtGui.QImage.Format_RGB888)
        self.image.setPixmap(QtGui.QPixmap.fromImage(convertToQt))
        self.mirrorToggles()

    def imageUpdate(self):
        #print("Updating image using the dictionnary")
        self.refreshImg()

    def resizeEvent(self, event):
        #print("Resize")
        # Fit image in view based on resize of the window
        self.imgViewer.fitInView(self.viewArea, QtCore.Qt.KeepAspectRatio)


    def satChange(self, key):
        if (self.saturationText.isVisible() == True):
            #print("saturation change {}".format(key))
            if key == 43:
                self.imgDict["saturation"] += 0.1
                self.updateSaturation()
                self.refreshImg()

            if key == 45:
                self.imgDict["saturation"] -= 0.1
                self.updateSaturation()
                self.refreshImg()

            if key == 48:
                self.imgDict["saturation"] = 1
                self.updateSaturation()
                self.refreshImg()


    def exposureChange(self, key):
        # Tweak expo only if E has been pressed before, and therefore the text is toggled on
        if (self.exposureText.isVisible() == True):
            #print(key)
            if key == 43:
                #print("Boost expo")
                self.imgDict["exposure"] += 0.1

            if key == 45:
                #print("Lower expo")
                self.imgDict["exposure"] -= 0.1

            if key == 48:
                #print("Reset Exposure")
                self.imgDict["exposure"] = 0

            self.updateExposure()
            self.refreshImg()

    def exposureMenu(self):
        menuSent = (self.sender().text())
        
        if (self.exposureText.isVisible() == False):
            self.showExposureText()
        key = 0
        if menuSent.startswith("Increase Exposure") == True:
            #print("Boost Expo")
            key = 43
        elif menuSent.startswith("Decrease Exposure") == True:
            #print("Decrease Expo")
            key = 45
        elif menuSent.startswith("Reset Exposure") == True:
            #print("Reset expo")
            key = 48
        self.exposureChange(key)

    def customExpoMenu(self):
        self.expoPop = ExposurePopup()
        self.expoPop.show()
        self.expoPop.spin.valueChanged.connect(self.updateCustomExpo)
        
    def updateCustomExpo(self):
        self.imgDict["exposure"] = self.expoPop.spin.value()
        self.updateExposure()
        self.refreshImg()

    def customSatMenu(self):
        self.satPop = SaturationPopup()
        self.satPop.show()
        self.satPop.spin.valueChanged.connect(self.updateCustomSat)
        
    def updateCustomSat(self):
        self.imgDict["saturation"] = (self.satPop.spin.value())
        self.updateSaturation()
        self.refreshImg()

    def ocioMenu(self):
        self.ocioPop = OcioPopup()
        self.ocioPop.resize(500, 220)
        self.ocioPop.show()

    def saturationMenu(self):
        menuSent = self.sender().text()

        if (self.saturationText.isVisible() == False):
            self.showSaturationText()
        key = 0
        if menuSent.startswith("Increase Sat") == True:
            key = 43
        elif menuSent.startswith("Decrease Sat") == True:
            key = 45
        elif menuSent.startswith("Reset Sat") == True:
            key = 48
        self.satChange(key)

    def updateExposure(self):
        self.exposureText.setPlainText("Exposure : {}".format(round(self.imgDict["exposure"], 2)))

    def updateSaturation(self):
        self.saturationText.setPlainText("Saturation : {}".format(round(self.imgDict["saturation"], 2)))

    def showExposureText(self):
        if (self.exposureText.isVisible() == False):
            self.exposureText.show()
            self.textCard.show()
            self.updateExposure()
        else:
            self.exposureText.hide()
            self.textCard.hide()

    def updateSaturation(self):
        self.saturationText.setPlainText("Saturation : {}".format(round(self.imgDict["saturation"], 2)))

    def showSaturationText(self):
        if (self.saturationText.isVisible() == False):
            self.saturationText.show()
            self.textCard.show()
            self.updateSaturation()
        else:
            self.saturationText.hide()
            self.textCard.hide()

    def checkIfJsonExists(self):
        jsonPath = "config.json"
        if (os.path.exists(jsonPath) == True):
            print("Loaded ocio config and preferences")
            with open(jsonPath, "r") as file:
                config = json.load(file)
            file.close()
            self.imgDict["ocioVar"] = (config["ocioVar"])
            self.imgDict["ocio"]["ocioIn"] = (config["ocioIn"])
            self.imgDict["ocio"]["ocioOut"] = (config["ocioOut"])
            self.imgDict["ocio"]["ocioDisplay"] = (config["ocioDisplay"])
            self.imgDict["ocio"]["ocioLook"] = (config["ocioLook"])
        else:
            pass

    def ocioToggleClicked(self):
        if (self.ocioToggle.isChecked() == True):
            self.ocioToggle.setStyleSheet("background-color : blue")
            self.imgDict["ocioToggle"] = True
        else:
            self.ocioToggle.setStyleSheet("background-color : red")
            self.imgDict["ocioToggle"] = False

        self.refreshImg()


class WorkerSignals(QtCore.QObject):
    '''
    Defines signals available from running worker thread

    finished
        No data

    result
        tuple, int (img and its buffer index)
    '''
    finished = QtCore.pyqtSignal()
    result = QtCore.pyqtSignal(tuple, object)

class Worker(QtCore.QRunnable):
    '''
    Worker thread

    :param args: Arguments containing the current and framelist
    :param kwargs: Keywords arguments containing the imgDict
    '''

    #result = QtCore.pyqtSignal(tuple, int)

    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self, *args, **kwargs):
        #print(self.args)
        #print(self.kwargs)
        t0 = time.time()
        img= bufferBackEnd(self.kwargs, self.args[0], self.args[1])
        t1 = time.time()
        #print("img obtained in {}".format(t1-t0))

        self.signals.finished.emit()
        if (type(img) == tuple):
            self.signals.result.emit(img[0], img[1])



class QueueThread(QtCore.QThread):
    '''
    Thread class responsible for dispatching data to the BufferThread
    '''
    queueResult = QtCore.pyqtSignal(tuple, int)

    def __init__(self, *args, **kwargs):
        super(QueueThread, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        thread = BufferThread()
        thread.result.connect(self.bufferResult)
        temp = 0
        for i in range(5):
            thread.run(args[0], args[1]+temp, kwargs = kwargs["kwargs"])
            temp += 1

    def bufferResult(self, resultA, resultB):
        #print("got something")
        self.queueResult.emit(resultA, resultB)




class BufferThread(QtCore.QThread):
    '''
    Thread class responsible for image calculation
    '''
    result = QtCore.pyqtSignal(tuple, int)

    def __init__(self, *args, **kwargs):
        super(BufferThread, self).__init__(*args, **kwargs)

    def run(self,*args, **kwargs):
        #time.sleep(1)
        #img = None
        img= bufferBackEnd(kwargs["kwargs"], args[0], args[1])
        if (type(img) == tuple):
            self.result.emit(img[0], img[1])



class ExposurePopup(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
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
    def __init__(self, *args, **kwargs):
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

class OcioPopup(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
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
        self.ocioPath = QtWidgets.QLineEdit("ocio/config.ocio")
        self.ocioPath.textChanged.connect(self.pathChanged)
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

        self.pathChanged()
        self.checkIfJsonExists()

        colorSpaces,inputInterp,displays = initOcio2(widget.imgDict["ocioVar"])
        for i in colorSpaces:
            self.comboCS.addItem(i)
        for i in inputInterp:
            self.comboInput.addItem(i)
        for i in displays:
            self.comboDisplay.addItem(i)


        self.okBtn = QtWidgets.QPushButton("Ok")
        self.okBtn.clicked.connect(self.okClicked)
        self.cancelBtn = QtWidgets.QPushButton("Cancel")
        self.cancelBtn.clicked.connect(self.cancelClicked)
        self.saveBtn = QtWidgets.QPushButton("Save Config")
        self.saveBtn.clicked.connect(self.saveConfigClicked)
        self.okBtn.setFocus()


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
        self.dropDownLayout.addLayout(self.displayLayout)
        self.dropDownLayout.addLayout(self.viewLayout)
        self.dropDownLayout.addStretch()
        self.dropDownLayout.addLayout(self.btnsLayout)

        layout.addLayout(self.dropDownLayout)

        self.setLayout(layout)

    ###############################
    # Code for the Slot functions #
    ###############################
    @QtCore.pyqtSlot()
    def pathChanged(self):
        widget.imgDict["ocioVar"] = self.ocioPath.text()
        self.comboCS.clear()
        self.comboInput.clear()
        self.comboDisplay.clear()
        self.comboView.clear()

        colorSpaces,inputInterp,displays = initOcio2(widget.imgDict["ocioVar"])
        for i in colorSpaces:
            self.comboCS.addItem(i)
        for i in inputInterp:
            self.comboInput.addItem(i)
        for i in displays:
            self.comboDisplay.addItem(i)

        self.onCsChanged()
        self.onAnyChanged()

    def onCsChanged(self):
        cs = (self.comboCS.currentText())
        looks = getLooks(widget.imgDict["ocioVar"], cs)
        self.comboView.clear()
        
        for i in looks:
            self.comboView.addItem(i)

    def onAnyChanged(self):
        #print(self.comboInput.currentText())
        widget.imgDict["ocio"]["ocioIn"] = self.comboInput.currentText()
        widget.imgDict["ocio"]["ocioOut"] = self.comboCS.currentText()
        widget.imgDict["ocio"]["ocioDisplay"] = self.comboDisplay.currentText()
        widget.imgDict["ocio"]["ocioLook"] = self.comboView.currentText()

    def okClicked(self):
        widget.refreshImg()

    def saveConfigClicked(self):
        # Check if a config.json exists 
        jsonPath = "config.json"
        if (os.path.exists(jsonPath) == True):
            print("Config exists, overriding")
        else:
            print("Creating new config")
        jsonData = {}
        jsonData["ocioVar"] = self.ocioPath.text()
        jsonData["ocioIn"] = self.comboInput.currentText()
        jsonData["ocioOut"] = self.comboCS.currentText()
        jsonData["ocioDisplay"] = self.comboDisplay.currentText()
        jsonData["ocioLook"] = self.comboView.currentText()
        #print(jsonData)
        with open(jsonPath, "w") as file:
            json.dump(jsonData, file)
        file.close()

    def checkIfJsonExists(self):
        jsonPath = "config.json"
        if (os.path.exists(jsonPath) == True):
            with open(jsonPath, "r") as file:
                config = json.load(file)
            file.close()
            self.ocioPath.setText(config["ocioVar"])
            self.comboInput.setCurrentText(config["ocioIn"])
            self.comboCS.setCurrentText(config["ocioOut"])
            self.comboDisplay.setCurrentText(config["ocioDisplay"])
            self.comboView.setCurrentText(config["ocioLook"])
        else:
            pass


    def cancelClicked(self):
        self.close()



if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800,600)
    widget.show()

    # Init the gui with the default pyVexr splashcreen in order to enable drag and drop from the start
    filenames = ["/home/martin/Documents/PYTHON/PyVexr/imgs/pyVexrSplashScreen_v001.exr"]
    widget.updateImgDict(filenames)

    sys.exit(app.exec())
