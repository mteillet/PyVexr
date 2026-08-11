# Main GUI for pyVexr

# PyVexr_gui.py

import sys
import os
import json
import time
import getpass
from PyQt5 import QtWidgets, QtCore, QtGui
from pyVexr_main import loadImg, interpretRectangle, exrListChannels, seqFromPath, initOcio2, getLooks, bufferBackEnd, layerContactSheetBackend, createVideoWriter, createImgWriter
from pyVexr_timelineGui import Timeline

from pyVexr_paths import (ocioConfigPath, readableConfigPath, resource,
                          writableConfigPath)

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
        # Buffer key actions
        # TODO
        if (event.key() == 16777216):
            widget.stopBuffer()
        if ((event.key() == QtCore.Qt.Key_R) & (self.activeKeys[16777249] == True)):
            if (self.activeKeys[16777248] == True):
                widget.cacheCurrentFrame()
            else:
                widget.cacheAllFrames()
        else:
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
        # Mirror image on X if Shift + X
        if ((self.activeKeys[16777248]) & (event.key() == 88)):
            widget.mirrorXToggle()
        if ((self.activeKeys[16777248]) & (event.key() == 89)):
            widget.mirrorYToggle()

        # Play and frame jumps
        if (event.key() == 32):
            widget.playBtn.click()
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
                    # Allowing looping in the timeline while scrubbing
                    if (mouseMoveX > 0) and (mouseMoveX + widget.frameNumber.slider.value() > widget.frameNumber.slider.maximum()):
                        widget.frameNumber.slider.setValue(widget.frameNumber.slider.minimum())
                    elif (mouseMoveX < 0) and (mouseMoveX + widget.frameNumber.slider.value() < widget.frameNumber.slider.minimum()):
                        widget.frameNumber.slider.setValue(widget.frameNumber.slider.maximum())
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
                #print("File exists {}".format(path))
                filenames.append(url.toLocalFile())
            else:
                # Append the default pyVexr logo
                filenames.append(resource("imgs", "pyVexrSplashScreen_v002.exr"))
        widget.updateImgDict(filenames)
        widget.totalFrameLabel.setText("{}".format(widget.frameNumber.slider.maximum()))
        widget.initOnDrop()
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
        self.setWindowIcon(QtGui.QIcon(resource("imgs", "pyVexr_Icon_512.jpeg")))
        self.setAcceptDrops(True)

        # ThreadPool
        self.threadpool = QtCore.QThreadPool()
        self.maxThreads = self.threadpool.maxThreadCount()
        self.threadpool.setMaxThreadCount(self.bufferThreadCount(4))
        #self.threadpool.setMaxThreadCount(2)
        #print(("Multithreading with maximum {} threads").format(self.threadpool.maxThreadCount()))

        # StyleSheet settings
        self.setStyleSheet("color: white; background-color: rgb(11,11,11)")
        self.setMouseTracking(True)
        self._zoom = 0
        
        # Global dict image related:
        self.imgDict = {}
        self.imgDict["buffer"] = []
        self.imgDict["path"] = []
        self.imgDict["ocioVar"] = ocioConfigPath()
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
        self.imgDict["ContactSheet"] = False
        self.imgDict["ContactSheetChannels"] = []
        self.imgDict["version"] = {} 
        self.diagnostic = False
        self.bufferRange = 2
        # Buffer bookkeeping : generation counter used to drop results of
        # workers started for a previous sequence, and memory accounting so
        # the cache cannot grow without bound.
        self.bufferEpoch = 0
        self.bufferBytes = 0
        self.bufferBudgetBytes = 4096 * 1024 * 1024

        # Playback is driven by a timer on the GUI thread rather than by a
        # pool of sleeping runnables.
        self.playbackFps = 24
        self.playTimer = QtCore.QTimer(self)
        self.playTimer.setTimerType(QtCore.Qt.PreciseTimer)
        self.playTimer.setInterval(int(1000 / self.playbackFps))

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
        self.bufferMenu = self.menuBar.addMenu('&Buffer')
        # Buffer menu & actions
        self.bufferAllAction = self.bufferMenu.addAction("Cache all frames             &-&C&t&r&l&+&R")
        self.bufferAllAction.triggered.connect(self.cacheAllFrames)
        self.stopBufferAction = self.bufferMenu.addAction("Stop Buffer                      &-&E&s&c")
        self.stopBufferAction.triggered.connect(self.stopBuffer)
        self.reloadFrameAction = self.bufferMenu.addAction("Reload Current Frame  &-&S&h&i&f&t&+&C&t&r&l&+&R")
        self.reloadFrameAction.triggered.connect(self.cacheCurrentFrame)
        self.resetBufferAction = self.bufferMenu.addAction("Reset Buffer")
        self.resetBufferAction.triggered.connect(self.resetBuffer)
        self.bufferSettingsAction = self.bufferMenu.addAction("Buffer settings")
        self.bufferSettingsAction.triggered.connect(self.bufferPopup)
        # File Menu & Action
        self.openAction = self.fileMenu.addAction("Open        &-&C&t&r&l&+&O")
        self.openAction.triggered.connect(self.openFiles)
        self.addAction = self.fileMenu.addAction("Add Shot to session")
        self.addAction.triggered.connect(self.addShot)
        self.openPlaylist = self.fileMenu.addAction("Open playlist")
        self.openPlaylist.triggered.connect(self.getOpenPlaylist)
        self.fileMenu.addSeparator()
        self.savePlaylist = self.fileMenu.addAction("Save as playlist")
        self.savePlaylist.triggered.connect(self.exportPlaylist)
        self.exportMp4 = self.fileMenu.addAction("Export as mp4")
        self.exportMp4.triggered.connect(self.movieExport)
        self.exportImg = self.fileMenu.addAction("Export as Image")
        self.exportImg.triggered.connect(self.imgExport)
        self.fileMenu.addSeparator()
        self.exit = self.fileMenu.addAction("Exit PyVexr")
        # Mirror Action
        self.autoLoadMenu = QtWidgets.QAction("Auto load sequences", self.editMenu, checkable=True)
        self.autoLoadMenu.setChecked(True)
        self.autoLoadMenuTrigger = self.editMenu.addAction(self.autoLoadMenu)
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
        self.contactSheet.triggered.connect(self.contactSheetWindow)
        self.mirrorY.triggered.connect(self.mirrorYToggle)
        self.fileMenu.addSeparator()
        self.infosAction = self.editMenu.addAction("About / Help")
        self.infosAction.triggered.connect(self.infosPopup)
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
        self.versionsDock = QtWidgets.QDockWidget("Versions Pannel", self)
        self.versionsDock.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable)
        self.versionsDock.hide()
        self.versionsDock.setWidget(self.versionsGroupBox)

        # Add version button
        self.addVersion = QtWidgets.QPushButton("Add Version")
        self.addVersion.clicked.connect(self.addNewVersion)


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
        # Allowing antialiasing on the QGraphicsPixmap
        self.image.setTransformationMode(QtCore.Qt.SmoothTransformation)
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
        self.version.setText("")

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
        self.playBackBtn.setCheckable(True)
        self.playBackBtn.clicked.connect(self.playBack)
        self.frameCurrent = QtWidgets.QLabel("101")
        currentPos = (self.frameNumber.slider.value())
        self.frameCurrent.setText(str(self.frameNumber.slider.value()).zfill(4))
        self.playBtn = QtWidgets.QPushButton(">")
        self.playBtn.setCheckable(True)
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
        self.versionsLayout.addWidget(self.addVersion)
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

    def stopBuffer(self):
        '''
        Deleting the Queued buffer operations
        '''
        self.threadpool.clear()

    def closeEvent(self, event):
        '''
        Stops playback and waits for the workers before letting Python tear
        the interpreter down. Quitting mid buffering used to leave running
        workers touching Python objects during finalisation, which hangs or
        crashes on exit.
        '''
        self.stopPlayback()
        self.threadpool.clear()
        self.threadpool.waitForDone(5000)
        super().closeEvent(event)

    def resetShotBuffer(self):
        '''
        Resetting the buffer on the current shot of the timeline
        '''
        self.stopBuffer()

        currentPos = (self.frameNumber.slider.value())
        shot =  self.timeLineDict[currentPos]["shot"]

        bufferToReset = []

        current = 0
        for frame in self.timeLineDict:
            if (self.timeLineDict[frame]["shot"] == shot):
                bufferToReset.append(current)
            current += 1

        for i in bufferToReset:
            if self.imgDict["buffer"][i] is not None:
                self.bufferBytes -= self.frameByteSize(self.imgDict["buffer"][i])
            self.imgDict["buffer"][i] = None

        # TODO
        # Would need to reset the cache draw only on the shot, and not the whole timeline
        self.frameNumber._timeline.resetCacheDraw()

    def resetBuffer(self):
        '''
        Resetting the buffer
        '''
        #Stopping the queue if workers are not created yet
        self.threadpool.clear()
        # New generation : results of workers that are already running belong
        # to the buffer being thrown away and will be dropped on arrival.
        self.bufferEpoch += 1
        self.bufferBytes = 0

        if (len(self.imgDict["buffer"]) > 0):
            self.imgDict["buffer"] = []

        # Empty buffer slots
        for shot in self.seqDict:
            for frame in self.seqDict[shot]:
                self.imgDict["buffer"].append(None)

        self.frameNumber._timeline.resetCacheDraw()

    def bufferInit(self, seqDict):
        '''
        Init buffer size using the seqDict length
        '''
        self.resetBuffer()
        # Sending One frame to check the time
        frameList = []
        for shot in seqDict:
            for frame in seqDict[shot]:
                frameList.append(frame)
        current = self.frameNumber.slider.value()

        count = 0
        self.threadpool.setMaxThreadCount(self.maxThreads - 6)
        if (len(frameList) > 0):
            # First check to see how much time a thread takes to finish
            if (current+count > self.frameNumber.slider.maximum()):
                #print("NEED TO RESET THE CURRENT + COUNT")
                current = self.frameNumber.slider.minimum()
                count = 0
            self.t0 = time.time()
            self.startBufferWorker(frameList, current+count, self.queueStart)
            count += 1

    def snapshotBufferState(self):
        '''
        Snapshot of everything the cached images depend on.
        The shot list is copied with list() : storing self.seqDict.keys() kept
        a live view of the dictionary, so the stored state and the current one
        always compared equal on that key and adding or removing a shot never
        invalidated the buffer.
        '''
        return {
            "frame": list(self.seqDict.keys()),
            "ocioIn": self.imgDict["ocio"]["ocioIn"],
            "ocioOut": self.imgDict["ocio"]["ocioOut"],
            "ocioLook": self.imgDict["ocio"]["ocioLook"],
            "ocioDisplay": self.imgDict["ocio"]["ocioDisplay"],
            "ocioToggle": self.imgDict["ocioToggle"],
            "channel": self.imgDict["channel"],
            "exposure": self.imgDict["exposure"],
            "saturation": self.imgDict["saturation"],
            "RGBA": self.imgDict["RGBA"],
            "ContactSheet": self.imgDict["ContactSheet"],
            "ContactSheetChannels": list(self.imgDict["ContactSheetChannels"]),
        }

    def createBufferState(self):
        '''
        Creating a buffer state that will be used to compare
        Buffer settings and know if it needs to be reset
        '''
        # Check if there are frames in the seqDict
        if (len(self.seqDict) > 0):
            self.bufferState = self.snapshotBufferState()

    def checkIfBufferStateChanged(self):
        '''
        Compares the self.bufferState with the current buffer settings
        in order to see if buffer needs to be reset or not
        '''
        # Compare bufferState
        if (len(self.seqDict) > 0):
            currentState = self.snapshotBufferState()

            if (currentState == self.bufferState):
                #print("No change in buffer state")
                pass
            else:
                #print("Change in buffer !")
                self.bufferState = currentState
                # Stop threadpool in case a buffer is in progress
                self.threadpool.clear()
                self.bufferInit(self.seqDict)

                #print(self.bufferState)
                #print(currentState)

    def cacheCurrentFrame(self):
        '''
        Recalculating / Calculating the image for the current buffer
        '''
        #print("Recaching current Frame")
        # Stopping the queue if workers are not created yet
        self.threadpool.clear()

        frameList = []
        for shot in self.seqDict:
            for frame in self.seqDict[shot]:
                frameList.append(frame)

        current = self.frameNumber.slider.value()

        # Starting a thread
        self.startBufferWorker(frameList, current)

        self.refreshImg()

    def cacheAllFrames(self):
        '''
        Caching all frames in the timeline from the current cursor position
        '''
        # First clear the cache
        self.resetBuffer()

        currentPosition = self.frameNumber.slider.value()
        
        frameList = []
        for shot in self.seqDict:
            for frame in self.seqDict[shot]:
                frameList.append(frame)

        minimum = self.frameNumber.slider.minimum()
        maximum = self.frameNumber.slider.maximum()
        for i in frameList:
            self.startBufferWorker(frameList, currentPosition)
            if currentPosition < maximum:
                currentPosition += 1
            else:
                currentPosition = minimum


    def bufferLoad(self, seqDict):
        # Clear the queue if any workers have not been created yet
        self.threadpool.clear()
        # Frame path list from seqDict
        frameList = []
        for shot in seqDict:
            for frame in seqDict[shot]:
                frameList.append(frame)
        current = self.frameNumber.slider.value()
        
        #print(self.diagnostic)

        count = 0
        if (len(frameList) > 0):
            # First check to see how much time a thread takes to finish
            if (self.diagnostic == False):
                #print("buffer launch limited")
                for i in range(self.bufferRange):
                    # Reset the curent + count to not get out of list range
                    if (current+count > self.frameNumber.slider.maximum()):
                        #print("NEED TO RESET THE CURRENT + COUNT")
                        current = self.frameNumber.slider.minimum()
                        count = 0
                    self.startBufferWorker(frameList, current+count)
                    count += 1
            else:
                #print("buffer launch full")
                for i in range(len(frameList)):
                    # Reset the curent + count to not get out of list range
                    if (current+count > self.frameNumber.slider.maximum()):
                        #print("NEED TO RESET THE CURRENT + COUNT")
                        current = self.frameNumber.slider.minimum()
                        count = 0
                    self.startBufferWorker(frameList, current+count)
                    count += 1

    def bufferThreadCount(self, reserved):
        '''
        Threads left for buffering after keeping some cores for the interface.
        Never below one : on a four core machine "maxThreads - 4" gave a pool
        of zero, where Qt queues every worker forever and nothing is ever
        cached, with no message.
        '''
        return(max(1, self.maxThreads - reserved))

    def bufferSettings(self):
        '''
        Immutable snapshot of everything a worker needs.
        Workers used to receive **self.imgDict, a shallow copy : "buffer",
        "ocio" and "path" were the very same objects the GUI thread keeps
        mutating while the workers read them.
        '''
        settings = dict(self.imgDict)
        settings["ocio"] = dict(self.imgDict["ocio"])
        settings["ContactSheetChannels"] = list(self.imgDict["ContactSheetChannels"])
        settings["path"] = list(self.imgDict["path"])
        # The buffer belongs to the GUI thread only.
        settings.pop("buffer", None)
        settings.pop("version", None)
        return(settings)

    def startBufferWorker(self, frameList, index, slot=None):
        '''
        Starts one worker for the frame at index, unless it is already cached.
        Returns True when a worker was actually started.
        '''
        if (index < 0) or (index >= len(frameList)):
            return(False)
        if (index < len(self.imgDict["buffer"])) and (self.imgDict["buffer"][index] is not None):
            return(False)

        worker = Worker(frameList, index, self.bufferSettings(), self.bufferEpoch)
        worker.signals.result.connect(slot if slot is not None else self.queueResult)
        self.threadpool.start(worker)
        return(True)

    def storeBufferResult(self, image, position, epoch):
        '''
        Stores a worker result in the buffer.
        Workers still running when the buffer was reset come back with a
        position, and pixels, that belong to the previous sequence : both the
        generation and the bounds are checked here rather than trusting the
        sender. threadpool.clear() only drops what has not started yet.
        '''
        if epoch != self.bufferEpoch:
            return(False)
        if (position < 0) or (position >= len(self.imgDict["buffer"])):
            return(False)

        if self.imgDict["buffer"][position] is None:
            self.bufferBytes += self.frameByteSize(image)
        self.imgDict["buffer"][position] = image
        self.frameNumber._timeline.paintBuffer(position, len(self.imgDict["buffer"]))
        self.enforceBufferBudget()
        return(True)

    def frameByteSize(self, image):
        '''
        Memory held by one cached frame : (pixels, width, height, bytesPerLine)
        '''
        try:
            return(int(image[2]) * int(image[3]))
        except (TypeError, IndexError, ValueError):
            return(0)

    def enforceBufferBudget(self):
        '''
        Drops the frames furthest from the playhead until the cache fits in
        the memory budget. Without this a 200 frame 4K timeline holds several
        gigabytes and nothing ever frees them but the Reset Buffer menu.
        '''
        if self.bufferBytes <= self.bufferBudgetBytes:
            return

        current = self.frameNumber.slider.value()
        cached = [index for index, image in enumerate(self.imgDict["buffer"])
                  if image is not None]
        # Furthest from the playhead first.
        cached.sort(key=lambda index: abs(index - current), reverse=True)

        for index in cached:
            if self.bufferBytes <= self.bufferBudgetBytes:
                break
            if index == current:
                continue
            self.bufferBytes -= self.frameByteSize(self.imgDict["buffer"][index])
            self.imgDict["buffer"][index] = None
            self.frameNumber._timeline.unpaintBuffer(index)

    def queueResult(self, resultA, resultB, epoch):
        self.storeBufferResult(resultA, resultB, epoch)
        #print(("Multithreading with maximum {} threads").format(self.threadpool.maxThreadCount()))
        #print("Finished loading buffer at pos {}".format(resultB))

    def queueStart(self, resultA, resultB, epoch):
        self.storeBufferResult(resultA, resultB, epoch)
        t1 = time.time()
        #print(t1 - self.t0)
        if (t1 - self.t0) < 0.2:
            self.threadpool.setMaxThreadCount(self.bufferThreadCount(2))
            self.diagnostic = True
        else:
            self.threadpool.setMaxThreadCount(self.bufferThreadCount(6))
            self.diagnostic = False
            self.threadpool.clear()
        #print("diagnostic has been set to : ".format(self.diagnostic))

    def bufferPopup(self):
        self.bufPopup = BufferPopup()
        self.bufPopup.show()

    def infosPopup(self):
        self.infPopup = InfosPopup()
        self.infPopup.show()
        self.infPopup.resize(500,400)

    def addShot(self):
        '''
        Adding shot to current PyVexr Viewing Session
        '''
        #print("Adding shot")
        openDialog = QtWidgets.QFileDialog.getOpenFileName(self, "Open new shot")

        shotToAdd = (openDialog[0])
        if not shotToAdd:
            return

        newShotList = []

        for shot in self.seqDict:
            for frame in self.seqDict[shot]:
                newShotList.append(frame)
                
        newShotList.append(shotToAdd)

        self.updateImgDict(newShotList)

    def initOnDrop(self):
        '''
        Resetting the slider back to its first frame after an image is dropped
        '''
        #print("Setting the slider to {}".format(self.frameNumber.slider.minimum()))
        self.frameNumber.slider.setValue(self.frameNumber.slider.minimum() + 1)
        self.frameNumber.slider.setValue(self.frameNumber.slider.minimum())

    def exportPlaylist(self):
        '''
        Exporting the current list of shot as a playlist, in order to re-open it
        '''
        # Getting a destination for the playlist
        lt = time.localtime()
        
        jsonData = {}
        # getpass and not os.getlogin() : the latter raises when there is no
        # controlling terminal, which is the case when started from a desktop
        # launcher or a container.
        jsonData["user"] = getpass.getuser()
        jsonData["date"] = ("{}/{}/{} - {}:{}".format(lt[0], str(lt[1]).zfill(2), str(lt[2]).zfill(2), str(lt[3]).zfill(2), str(lt[4]).zfill(2)))
        jsonData["shots"] = self.seqDict


        exportDialog = QtWidgets.QFileDialog.getSaveFileName(self, "Export PyVexrPlaylist")
        destination = (exportDialog[0])
        # Cancelling the dialog returns an empty path : without this it used to
        # write a file literally named ".pyVexr" in the current directory.
        if not destination:
            return

        # Ensuring there is an extension
        if destination.endswith(".pyVexr") == False:
            destination = "{}.pyVexr".format(destination)


        with open(destination, "w") as file:
            json.dump(jsonData, file)
        file.close()

    def getOpenPlaylist(self):
        '''
        Opening a playlist file
        '''
        openDialog = QtWidgets.QFileDialog.getOpenFileName(self, "Open a playlist")

        jsonPath = (openDialog[0])
        if not jsonPath:
            return

        print("Opening {}".format(openDialog[0]))

        with open(jsonPath, "r") as file:
            config = json.load(file)
        file.close()

        print("Playlist created by {} on the {}".format(config["user"], config["date"]))

        self.seqDict = config["shots"]
        frames = []
        for shot in self.seqDict:
            for frame in self.seqDict[shot]:
                frames.append(frame)

        self.updateImgDict(frames)


    def movieExport(self):
        '''
        Exporting a movie from the written cache
        '''
        # First clear threadpool in order to focus writing power to the mp4 generation
        self.stopPlaybackButtons()
        self.threadpool.clear()

        # Creating window for export destination
        exportDialog = QtWidgets.QFileDialog.getSaveFileName(self, 'Export MP4 file')
        destination = (exportDialog[0])
        if not destination:
            return
        # Adding the mp4 extension if it was forgotten
        if destination.endswith(".mp4") == False:
            destination ="{}.mp4".format(destination)
            
        current = self.frameNumber.slider.value()
        frameList = []
        for shot in self.seqDict:
            for frame in self.seqDict[shot]:
                frameList.append(frame)

        createVideoWriter(self.imgDict, frameList, current, destination)

    def imgExport(self):
        '''
        Exporting a single frame from the written cache
        '''
        # Clear threadpool in order to focus writing the image to disk
        self.stopPlaybackButtons()
        self.threadpool.clear()

        current = self.frameNumber.slider.value()
        frameList = []
        for shot in self.seqDict:
            for frame in self.seqDict[shot]:
                frameList.append(frame)

        # Creating a window for export destination
        exportDiag = QtWidgets.QFileDialog.getSaveFileName(self, "Export Jpeg Image")
        destination = exportDiag[0]
        if not destination:
            return
        # Adding jpeg extension if forgotten
        if destination.endswith(".jpg") == False:
            destination = "{}.jpg".format(destination)

        createImgWriter(self.imgDict, frameList, current, destination)


    def loadFile(self):
        #Loading frames from same nomenclature
        seqDict = seqFromPath(self.imgDict["path"], self.autoLoadMenu.isChecked())
        self.seqDict = seqDict

        self.bufferInit(seqDict)
        self.createBufferState()

        #Init the slider
        self.initSlider(seqDict)
        self.buildVersioningDict()
        # Calculating the actual image from the backend
        tempImg = loadImg(self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"],self.imgDict["path"], self.imgDict["exposure"], self.imgDict["saturation"], self.imgDict["channel"], self.imgDict["RGBA"], self.imgDict["ocioVar"], self.imgDict["ocio"]["ocioDisplay"], self.imgDict["ocioToggle"], self.imgDict)

        if len(self.imgDict["buffer"]) > 0:
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
        # Checking if the position is not out of range from the list
        if (currentPos < len(self.imgDict["buffer"])):
            if (self.imgDict["buffer"][currentPos] != None):
                tempImg = self.imgDict["buffer"][currentPos]
            else:
                self.imgDict["path"][0] = frame
                self.bufferLoad(self.seqDict)
                #tempImg = self.imgDict["buffer"][currentPos]
                tempImg = loadImg(self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"],self.imgDict["path"], self.imgDict["exposure"], self.imgDict["saturation"], self.imgDict["channel"], self.imgDict["RGBA"], self.imgDict["ocioVar"], self.imgDict["ocio"]["ocioDisplay"], self.imgDict["ocioToggle"], self.imgDict)
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
                self.listVersions()
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
        
    def startPlayback(self, slot):
        '''
        Drives playback with a single timer on the GUI thread.
        It used to queue one sleeping QRunnable per frame of the timeline in a
        one thread pool : the sleep was serialised in front of the decode so
        the real rate always drifted below the nominal one, the connect
        happened after start() so the first tick could be lost, and clear()
        could not stop the runnable already sleeping, which gave one extra
        frame after pause.
        '''
        self.stopPlayback()
        self.playTimer.setInterval(int(1000 / self.playbackFps))
        self.playTimer.timeout.connect(slot)
        self.playTimer.start()

    def stopPlaybackButtons(self):
        '''
        Stops playback and releases both buttons. The export dialogs are modal
        and run the event loop, so a running playback would keep advancing the
        timeline while the file is being written.
        '''
        for button in (self.playBtn, self.playBackBtn):
            if button.isChecked():
                button.setChecked(False)
        self.playBtn.setText(">")
        self.playBackBtn.setText("<")
        self.stopPlayback()

    def stopPlayback(self):
        self.playTimer.stop()
        try:
            self.playTimer.timeout.disconnect()
        except TypeError:
            # Nothing was connected yet.
            pass

    def playForward(self):
        if (self.playBtn.isChecked() == True):
            if (self.playBackBtn.isChecked() == True):
                self.playBackBtn.click()
            self.playBtn.setText("||")
            self.startPlayback(self.jumpFrameForward)
        else:
            self.playBtn.setText(">")
            self.stopPlayback()

    def playBack(self):
        if (self.playBackBtn.isChecked() == True):
            if (self.playBtn.isChecked() == True):
                self.playBtn.click()
            self.playBackBtn.setText("||")
            self.startPlayback(self.jumpFrameBack)
        else:
            self.playBackBtn.setText("<")
            self.stopPlayback()


    def nextPlaybackFrame(self, step):
        '''
        Frame the playhead would move to, wrapping around the timeline.
        Bounds come from the buffer itself : clamping against len(timeLineDict)
        and then indexing the buffer used to raise IndexError, since the two
        lists are built separately and the buffer is momentarily empty during a
        reset.
        '''
        bufferLength = len(self.imgDict["buffer"])
        if bufferLength == 0:
            return(None)

        position = self.frameNumber.slider.value() + step
        if position > self.frameNumber.slider.maximum():
            position = self.frameNumber.slider.minimum()
        elif position < self.frameNumber.slider.minimum():
            position = self.frameNumber.slider.maximum()

        return(max(0, min(position, bufferLength - 1)))

    def advancePlayback(self, step):
        position = self.nextPlaybackFrame(step)
        if position is None:
            return

        if self.imgDict["buffer"][position] is not None:
            self.frameNumber.slider.setValue(position)
        else:
            # Frame not cached yet : wait for the buffer rather than showing
            # nothing, and ask for it.
            self.bufferLoad(self.seqDict)

    def jumpFrameForward(self):
        self.advancePlayback(1)

    def jumpFrameBack(self):
        self.advancePlayback(-1)


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
        try:
            self.listVersions()
        except:
            self.listVersions()
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
            self.listVersions()
        self.initOnDrop()

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

    def addNewVersion(self):
        openDialog = QtWidgets.QFileDialog.getOpenFileName(self, "New Version")
        if not openDialog[0]:
            return
        newVersion = [(openDialog[0])]

        imagesFromNewVersion = list((seqFromPath(newVersion, self.autoLoadMenu.isChecked())).values())[0]

        currentPos = self.frameNumber.slider.value()
        shot = self.timeLineDict[currentPos]["shot"]

        # Getting number of version to know what tag to give the newest one
        numberOfVersions = len(list(self.imgDict["version"][shot].keys())) - 1
        self.imgDict["version"][shot]["v_{}".format(str(numberOfVersions+1).zfill(4))] = imagesFromNewVersion

        self.listVersions()

    def buildVersioningDict(self):
        # Building the versioning dictionnary.
        # Only for shots that are not known yet : this runs again every time a
        # shot is added, and resetting the whole dict silently threw away every
        # version the user had registered.
        for i in self.seqDict:
            if i not in self.imgDict["version"]:
                self.imgDict["version"][i] = {}
            self.imgDict["version"][i]["v_0000"] = self.seqDict[i]

    def listVersions(self):
        currentPos = (self.frameNumber.slider.value())
        frame = self.frameNumber.returnFrame(currentPos)
        shot = (self.timeLineDict[currentPos]["shot"])

        #print(self.imgDict["version"][shot].keys())
        versionsButtonList = []
        current = 0
        for i in self.imgDict["version"][shot].keys():
            #print("Creating versions buttons")
            versionBtn = QtWidgets.QPushButton("v_{}".format(str(current).zfill(4)))
            versionBtn.clicked.connect(self.switchVersion)
            versionsButtonList.append(versionBtn)
            current += 1

        # Removing older versions
        layout = self.versionsLayout
        if (layout.count()) > 3:
            for i in range(layout.count()-1,-1,-1):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, QtWidgets.QPushButton):
                    if widget.text().startswith("v_"):
                        layout.removeWidget(widget)
                        widget.deleteLater()

        # Adding versions button
        for btn in versionsButtonList:
             self.versionsLayout.addWidget(btn)

    def switchVersion(self):
        currentPos = (self.frameNumber.slider.value())
        shot =  self.timeLineDict[currentPos]["shot"]

        # Getting the new version path to assign
        versionToAssign = self.imgDict["version"][shot][self.sender().text()]

        # Assign on same frame range as the previous shot
        resizedVersionList = self.matchListLen(versionToAssign, self.seqDict[shot])
        self.seqDict[shot] = resizedVersionList

        # Need to implement a re cache of the shot before the image update, for now need to do it manually
        self.resetShotBuffer()
        self.cacheCurrentFrame()
        self.imageUpdate()

    def matchListLen(self, listA, listB):
        '''
        Return a copy of listA resized to the len of listB, containing only
        items from listA.

        The copy matters : switchVersion passes the list stored in
        self.imgDict["version"], and inserting or deleting in place destroyed
        that version's frame list for good after a couple of switches.
        '''
        listA = list(listA)
        lenA = len(listA)
        lenB = len(listB)

        # In case listA is not as long as list B
        if (lenA < lenB):
            current = 0
            while (len(listA) < len(listB)):
                listA.insert(current+1, listA[current])
                if (current + 2) < len(listA):
                    current += 2
                else:
                    current = 0
                #print("length list A is : {}".format(len(listA)))
                #print("current is : {}".format(current))

        # In case listA is longer than list B
        if (lenA > lenB):
            current = len(listA) // 2
            while (len(listA) > len(listB)):
                del listA[current]
                previousCurrent = current
                current = current // 2
                if current == 1:
                    current = 2
                currentIter = current + previousCurrent
                while currentIter < len(listA) and len(listA) > len(listB):
                    del listA[currentIter]
                    currentIter += previousCurrent

        return(listA)


    def listChannels(self):
        currentPos = (self.frameNumber.slider.value())
        frame = self.frameNumber.returnFrame(currentPos)

        self.imgDict["path"] = [frame]

        channels = exrListChannels(self.imgDict["path"])

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

    def getRelativeFrameIndex(self):
        '''
        Returns the index of the frame on the specific shot it is on
        '''
        currentPos = (self.frameNumber.slider.value())

        if currentPos > (len(self.timeLineDict) - 1):
            currentPos = (len(self.timeLineDict) - 1)

        # Walk the shots keeping a running offset : comparing a shot length
        # against a global position used to leave the very first frame of a
        # following shot pointing past the end of its own list.
        offset = 0
        for anyshot in self.seqDict:
            shotLength = len(self.seqDict[anyshot])
            if currentPos < (offset + shotLength):
                return(currentPos - offset)
            offset += shotLength
        return(currentPos - offset)

    def refreshImg(self):
        self.checkIfBufferStateChanged()

        currentPos = (self.frameNumber.slider.value())

        if currentPos > (len(self.timeLineDict) - 1):
            currentPos = (len(self.timeLineDict) - 1)
        shot =  self.timeLineDict[currentPos]["shot"]
        # Finding the index of the frame relative to current shot
        posRelativeToShot = self.getRelativeFrameIndex()
        self.imgDict["path"] = [self.seqDict[shot][posRelativeToShot]]

        #print("check buffer at position {} and frame {}".format(currentPos, frame))
        tempImg = loadImg(self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"],self.imgDict["path"], self.imgDict["exposure"], self.imgDict["saturation"],self.imgDict["channel"], self.imgDict["RGBA"], self.imgDict["ocioVar"], self.imgDict["ocio"]["ocioDisplay"], self.imgDict["ocioToggle"], self.imgDict)

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

    def contactSheetWindow(self):
        self.contactSheetPop = ContactSheetPopup()
        self.contactSheetPop.resize(600,300)
        self.contactSheetPop.show()

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
        '''
        Loads the saved OCIO preferences, falling back to the defaults of the
        shipped config when the file is missing, unreadable, incomplete, or
        points at an OCIO config that no longer exists. This runs from
        __init__, so anything raising here used to make the application
        impossible to start.
        '''
        config = self.readSavedConfig()

        if config is not None:
            print("Loaded ocio config and preferences")
            self.imgDict["ocioVar"] = config["ocioVar"]
            self.imgDict["ocio"]["ocioIn"] = config["ocioIn"]
            self.imgDict["ocio"]["ocioOut"] = config["ocioOut"]
            self.imgDict["ocio"]["ocioDisplay"] = config["ocioDisplay"]
            self.imgDict["ocio"]["ocioLook"] = config["ocioLook"]
            return

        cc, cc, dispView = initOcio2(self.imgDict["ocioVar"])
        self.imgDict["ocio"]["ocioIn"] = cc[0]
        self.imgDict["ocio"]["ocioOut"] = cc[0]
        self.imgDict["ocio"]["ocioDisplay"] = dispView[0]

    def readSavedConfig(self):
        '''
        Returns the saved preferences when they are complete and usable,
        None otherwise.
        '''
        jsonPath = readableConfigPath()
        if os.path.exists(jsonPath) == False:
            return(None)

        try:
            with open(jsonPath, "r") as file:
                config = json.load(file)
        except (OSError, ValueError) as error:
            print("Ignoring unreadable config.json : {}".format(error))
            return(None)

        expected = ["ocioVar", "ocioIn", "ocioOut", "ocioDisplay", "ocioLook"]
        missing = [key for key in expected if key not in config]
        if missing:
            print("Ignoring incomplete config.json, missing {}".format(
                ", ".join(missing)))
            return(None)

        if os.path.exists(config["ocioVar"]) == False:
            print("Ignoring config.json, the ocio config {} is gone".format(
                config["ocioVar"]))
            return(None)

        return(config)


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
        tuple, int, int (img, its buffer index, and the buffer generation it
        was computed for)
    '''
    finished = QtCore.pyqtSignal()
    result = QtCore.pyqtSignal(tuple, object, object)

class Worker(QtCore.QRunnable):
    '''
    Worker thread computing one frame of the buffer.

    settings is a snapshot : the worker never sees the live imgDict, so the
    GUI thread can mutate the buffer, the OCIO settings or the shot list while
    workers are running.
    '''

    def __init__(self, frameList, index, settings, epoch):
        super(Worker, self).__init__()
        self.frameList = frameList
        self.index = index
        self.settings = settings
        self.epoch = epoch
        self.signals = WorkerSignals()

    def run(self):
        img = bufferBackEnd(self.settings, self.frameList, self.index)

        self.signals.finished.emit()
        if isinstance(img, tuple):
            self.signals.result.emit(img[0], img[1], self.epoch)



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

class ContactSheetPopup(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
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
        currentPos = (widget.frameNumber.slider.value())
        frame = widget.frameNumber.returnFrame(currentPos)
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
        self.toggleBtn.setChecked(widget.imgDict["ContactSheet"])
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
        if (sender.isChecked() == True):
            sender.setStyleSheet("background-color: rgb(1,1,221)")
        else:
            sender.setStyleSheet("background-color: rgb(11,11,11)")


        if (chanClicked in self.channelSelection):
            self.channelSelection.remove(chanClicked)
        else:
            self.channelSelection.append(chanClicked)

        widget.imgDict["ContactSheetChannels"] = self.channelSelection

    def contactSheetMode(self):
        '''
        Responsible for switching the image buffer generation to layercontactsheet mode
        '''
        if self.toggleBtn.isChecked() == True:
            #print("LayerContactSheet mode is on")
            self.toggleBtn.setStyleSheet("background-color: rgb(1,1,221)")
            widget.imgDict["ContactSheet"] = True
        else:
            #print("LayerContactSheet mode is off")
            self.toggleBtn.setStyleSheet("background-color: rgb(11,11,11)")
            widget.imgDict["ContactSheet"] = False
            
        # Reset buffer for change
        widget.checkIfBufferStateChanged()

    def okBtnClicked(self):
        '''
        Responsible for sending the list to backend and returning the image to put in the viewer
        '''
        currentPos = (widget.frameNumber.slider.value())
        frame = widget.frameNumber.returnFrame(currentPos)

        # Passing the chan list again to the widget imgList dict
        widget.imgDict["ContactSheetChannels"] = self.channelSelection

        widget.imgDict["path"] = [frame]

        #print(self.channelSelection)
        tempImg = layerContactSheetBackend(self.channelSelection, widget.imgDict)
        
        convertToQt = QtGui.QImage(tempImg[0], tempImg[1], tempImg[2], tempImg[3], QtGui.QImage.Format_RGB888)
        widget.image.setPixmap(QtGui.QPixmap.fromImage(convertToQt))

        widget.checkIfBufferStateChanged()

        widget.imgDict["buffer"][currentPos] = tempImg 


class InfosPopup(QtWidgets.QWidget):
    def __init__(self, *args,**kwargs):
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
    def __init__(self, *args, **kwargs):
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
        self.threadNumber.setMaximum(max(1, widget.maxThreads))
        self.threadNumber.setValue(widget.threadpool.maxThreadCount())
        self.threadNumber.valueChanged.connect(self.updateThreads)

        # Size of buffer batch
        self.threadBatchLabel = QtWidgets.QLabel("Buffer Batch Size for heavy EXRs :")
        self.threadBatch = QtWidgets.QSpinBox()
        self.threadBatch.setMinimum(1)
        self.threadBatch.setMaximum(9999)
        self.threadBatch.setValue(widget.bufferRange)
        self.threadBatch.valueChanged.connect(self.updateBatchSize)

        # Memory the cache is allowed to hold
        self.memoryLabel = QtWidgets.QLabel("Cache memory budget (MB) :")
        self.memoryBudget = QtWidgets.QSpinBox()
        self.memoryBudget.setMinimum(64)
        self.memoryBudget.setMaximum(1024 * 1024)
        self.memoryBudget.setSingleStep(256)
        self.memoryBudget.setValue(int(widget.bufferBudgetBytes / (1024 * 1024)))
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
        widget.threadpool.setMaxThreadCount(self.threadNumber.value())

    def updateBatchSize(self):
        #print(self.threadBatch.value())
        widget.bufferRange = self.threadBatch.value()

    def updateMemoryBudget(self):
        widget.bufferBudgetBytes = self.memoryBudget.value() * 1024 * 1024
        widget.enforceBufferBudget()
 
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
        self.ocioPath = QtWidgets.QLineEdit(widget.imgDict["ocioVar"])
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
        self.previousOcio = dict(widget.imgDict["ocio"])

        # Clearing the previous contents of menus
        for combo in (self.comboCS, self.comboInput, self.comboDisplay,
                      self.comboView):
            combo.blockSignals(True)
            combo.clear()

        colorSpaces,inputInterp,displays = initOcio2(widget.imgDict["ocioVar"])
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
        for look in getLooks(widget.imgDict["ocioVar"],
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
        previousOCIOvar = widget.imgDict["ocioVar"]
        widget.imgDict["ocioVar"] = self.ocioPath.text()

        try :
            colorSpaces,inputInterp,displays = initOcio2(widget.imgDict["ocioVar"])
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
        except :
            self.errorOcio(widget.imgDict["ocioVar"])
            widget.imgDict["ocioVar"] = previousOCIOvar
            # Turn off OCIO button
            #if widget.ocioToggle.isChecked():
            #    widget.ocioToggle.click()

    def errorOcio(self, path):
        err = QtWidgets.QMessageBox()
        err.setIcon(QtWidgets.QMessageBox.Critical)
        err.setText("ERROR : {} is not a valid ocio file".format(path))
        err.setWindowTitle("OCIO path error !")
        err.exec()

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
        jsonPath = writableConfigPath()
        absoluteOcioPath = (os.path.realpath(self.ocioPath.text()))

        # The ocio config has to exist, otherwise the saved preferences make
        # the next start fall back to the defaults anyway.
        if (os.path.exists(absoluteOcioPath) == False):
            print("Not saving : {} does not exist".format(absoluteOcioPath))
            return

        if (os.path.exists(jsonPath) == True):
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
        config = MyWidget.readSavedConfig(self)
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
        widget.imgDict["ocio"].update(self.previousOcio)
        widget.refreshImg()
        self.close()



if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")

    widget = MyWidget()
    widget.resize(800,600)
    widget.show()

    # Init the gui with the default pyVexr splashcreen in order to enable drag and drop from the start
    filenames = [resource("imgs", "pyVexrSplashScreen_v001.exr")]
    widget.updateImgDict(filenames)

    sys.exit(app.exec())
