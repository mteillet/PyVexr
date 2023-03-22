# Main GUI for pyVexr

# PyVexr_gui.py

import sys
import os
import json
import time
from math import sqrt
from PyQt5 import QtWidgets, QtCore, QtGui
from pyVexr_main import loadImg, interpretRectangle, exrListChannels, seqFromPath, initOcio2, getLooks, bufferBackEnd, layerContactSheetBackend, createVideoWriter, createImgWriter
from pyVexr_timelineGui import Timeline

# Setting absPath in order to avoid broken file links when using a compiled version on windows
absPath = os.path.dirname(sys.argv[0])
if absPath:
    absPath = "{}/".format(absPath)
realPath = "{}/".format(os.path.realpath("/".join((sys.argv[0]).split("/")[:-1])))

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
                filenames.append("{}imgs/pyVexrSplashScreen_v002.exr".format(absPath))
        #print(filenames)
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
        self.setWindowIcon(QtGui.QIcon("{}imgs/pyVexr_Icon_512.jpeg".format(absPath)))
        self.setAcceptDrops(True)

        # ThreadPool
        self.threadpool = QtCore.QThreadPool()
        self.maxThreads = self.threadpool.maxThreadCount()
        self.threadpool.setMaxThreadCount(self.maxThreads - 4)
        self.playThreadpool = QtCore.QThreadPool()
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
        self.imgDict["ocioVar"] = "{}ocio/config.ocio".format(realPath)
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
        self.p = None
        self.diagnostic = False
        self.playCount = []
        self.bufferRange = 2

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
        self.stopBufferAction = self.bufferMenu.addAction("Stop Buffer")
        self.stopBufferAction.triggered.connect(self.stopBuffer)
        self.reloadFrameAction = self.bufferMenu.addAction("Reload Current Frame")
        self.reloadFrameAction.triggered.connect(self.cacheCurrentFrame)
        self.resetBufferAction = self.bufferMenu.addAction("Reset Buffer")
        self.resetBufferAction.triggered.connect(self.resetBuffer)
        self.bufferAllAction = self.bufferMenu.addAction("Cache all frames")
        self.bufferAllAction.triggered.connect(self.cacheAllFrames)
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

        if (len(self.imgDict["buffer"]) >> 0):
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
        if (len(frameList) >> 0):
            # First check to see how much time a thread takes to finish
            if (current+count >> self.frameNumber.slider.maximum()):
                #print("NEED TO RESET THE CURRENT + COUNT")
                current = self.frameNumber.slider.minimum()
                count = 0
            self.t0 = time.time()
            worker = Worker(frameList, current+count, **self.imgDict)
            worker.signals.result.connect(self.queueStart)
            self.threadpool.start(worker)
            count += 1

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
            self.bufferState["ContactSheet"] = self.imgDict["ContactSheet"]
            self.bufferState["ContactSheetChannels"] = self.imgDict["ContactSheetChannels"]

            #print(self.bufferState)

    def checkIfBufferStateChanged(self):
        '''
        Compares the self.bufferState with the current buffer settings
        in order to see if buffer needs to be reset or not
        '''
        # Compare bufferState
        if (len(self.seqDict) >> 0):
            currentState = {}
            currentState["frame"] = (self.seqDict.keys())
            currentState["ocioIn"] = self.imgDict["ocio"]["ocioIn"]
            currentState["ocioOut"] = self.imgDict["ocio"]["ocioOut"]
            currentState["ocioLook"] = self.imgDict["ocio"]["ocioLook"] 
            currentState["ocioDisplay"] = self.imgDict["ocio"]["ocioDisplay"]
            currentState["ocioToggle"] = self.imgDict["ocioToggle"]
            currentState["channel"] = self.imgDict["channel"]
            currentState["exposure"] = self.imgDict["exposure"]
            currentState["saturation"] = self.imgDict["saturation"]
            currentState["RGBA"] = self.imgDict["RGBA"]
            currentState["ContactSheet"] = self.imgDict["ContactSheet"]
            currentState["ContactSheetChannels"] = self.imgDict["ContactSheetChannels"]

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
        worker = Worker(frameList, current, **self.imgDict)
        worker.signals.result.connect(self.queueResult)
        self.threadpool.start(worker)

        self.refreshImg()

    def cacheAllFrames(self):
        '''
        Caching all frames in the timeline
        '''
        print("cache all frames")
        # First clear the cache
        self.resetBuffer()
        
        frameList = []
        for shot in self.seqDict:
            for frame in self.seqDict[shot]:
                frameList.append(frame)

        current = self.frameNumber.slider.minimum()
        for i in frameList:
            worker = Worker(frameList, current, **self.imgDict)
            worker.signals.result.connect(self.queueResult)
            self.threadpool.start(worker)
            current += 1


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
        
        #print(self.diagnostic)

        count = 0
        if (len(frameList) >> 0):
            # First check to see how much time a thread takes to finish
            if (self.diagnostic == False):
                #print("buffer launch limited")
                for i in range(self.bufferRange):
                    # Reset the curent + count to not get out of list range
                    if (current+count >> self.frameNumber.slider.maximum()):
                        #print("NEED TO RESET THE CURRENT + COUNT")
                        current = self.frameNumber.slider.minimum()
                        count = 0
                    worker = Worker(frameList, current+count, **self.imgDict)
                    worker.signals.result.connect(self.queueResult)
                    self.threadpool.start(worker)
                    count += 1
            else:
                #print("buffer launch full")
                for i in range(len(frameList)):
                    # Reset the curent + count to not get out of list range
                    if (current+count >> self.frameNumber.slider.maximum()):
                        #print("NEED TO RESET THE CURRENT + COUNT")
                        current = self.frameNumber.slider.minimum()
                        count = 0
                    worker = Worker(frameList, current+count, **self.imgDict)
                    worker.signals.result.connect(self.queueResult)
                    self.threadpool.start(worker)
                    count += 1

    def queueResult(self, resultA, resultB):
        self.imgDict["buffer"][resultB] = resultA
        self.frameNumber._timeline.paintBuffer(resultB, len(self.imgDict["buffer"]))
        #print(("Multithreading with maximum {} threads").format(self.threadpool.maxThreadCount()))
        #print("Finished loading buffer at pos {}".format(resultB))

    def queueStart(self, resultA, resultB):
        self.imgDict["buffer"][resultB] = resultA
        self.frameNumber._timeline.paintBuffer(resultB, len(self.imgDict["buffer"]))
        t1 = time.time()
        #print(t1 - self.t0)
        if (t1 - self.t0) < 0.2:
            self.threadpool.setMaxThreadCount(self.maxThreads - 2)
            self.diagnostic = True
        else:
            self.threadpool.setMaxThreadCount(self.maxThreads - 6)
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
        jsonData["user"] = os.getlogin()
        jsonData["date"] = ("{}/{}/{} - {}:{}".format(lt[0], str(lt[1]).zfill(2), str(lt[2]).zfill(2), str(lt[3]).zfill(2), str(lt[4]).zfill(2)))
        jsonData["shots"] = self.seqDict


        exportDialog = QtWidgets.QFileDialog.getSaveFileName(self, "Export PyVexrPlaylist")
        destination = (exportDialog[0])

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
        self.threadpool.clear()

        # Creating window for export destination
        exportDialog = QtWidgets.QFileDialog.getSaveFileName(self, 'Export MP4 file')
        destination = (exportDialog[0])
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
        self.threadpool.clear()

        current = self.frameNumber.slider.value()
        frameList = []
        for shot in self.seqDict:
            for frame in self.seqDict[shot]:
                frameList.append(frame)

        # Creating a window for export destination
        exportDiag = QtWidgets.QFileDialog.getSaveFileName(self, "Export Jpeg Image")
        destination = exportDiag[0]
        # Adding jpeg extension if forgotten
        if destination.endswith(".jpg") == False:
            destination = "{}.jpg".format(destination)

        createImgWriter(self.imgDict, frameList, current, destination)


    def loadFile(self):
        #Loading frames from same nomenclature
        seqDict = seqFromPath(self.imgDict["path"])
        self.seqDict = seqDict

        self.bufferInit(seqDict)
        self.createBufferState()

        #Init the slider
        self.initSlider(seqDict)
        self.buildVersioningDict()
        # Calculating the actual image from the backend
        tempImg = loadImg(self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"],self.imgDict["path"], self.imgDict["exposure"], self.imgDict["saturation"], self.imgDict["channel"], self.imgDict["RGBA"], self.imgDict["ocioVar"], self.imgDict["ocio"]["ocioDisplay"], self.imgDict["ocioToggle"], self.imgDict)

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
        
    def playForward(self):
        if (self.playBtn.isChecked() == True):
            if (self.playBackBtn.isChecked() == True):
                self.playBackBtn.click()
            self.playCount = []
            self.playBtn.setText("||")
            self.playThreadpool.clear()
            self.playThreadpool.setMaxThreadCount(1)
            for i in range(self.frameNumber.slider.maximum() - self.frameNumber.slider.minimum()):
                nextWorker = NextWorker()
                nextWorker.signals.result.connect(self.jumpFrameForward)
                self.playThreadpool.start(nextWorker)
        else:
            self.playBtn.setText(">")
            self.playThreadpool.clear()

    def playBack(self):
        if (self.playBackBtn.isChecked() == True):
            if (self.playBtn.isChecked() == True):
                self.playBtn.click()
            self.playCount = []
            self.playBackBtn.setText("||")
            self.playThreadpool.clear()
            self.playThreadpool.setMaxThreadCount(1)
            for i in range(self.frameNumber.slider.maximum() - self.frameNumber.slider.minimum()):
                nextWorker = NextWorker()
                nextWorker.signals.result.connect(self.jumpFrameBack)
                self.playThreadpool.start(nextWorker)
        else:
            self.playBackBtn.setText("<")
            self.playThreadpool.clear()


    def jumpFrameForward(self):
        self.playCount.append(True)
        # Add this in case buffer needs to go back to first frame
        toCheckBuffer = self.frameNumber.slider.value()+1
        if toCheckBuffer > self.frameNumber.slider.maximum():
            toCheckBuffer = self.frameNumber.slider.minimum()
        if toCheckBuffer > (len(self.timeLineDict) - 1):
            toCheckBuffer = (len(self.timeLineDict) - 1)

        if self.imgDict["buffer"][toCheckBuffer] != None:
            #print("buffer ok")
            if ((self.frameNumber.slider.value() + 1) > self.frameNumber.slider.maximum()):
                self.frameNumber.slider.setValue(self.frameNumber.slider.minimum())
            else:
                self.frameNumber.slider.setValue(self.frameNumber.slider.value()+1)
        else:
            #print("Nothing in buffer !")
            self.bufferLoad(self.seqDict)

        if len(self.playCount) == (self.frameNumber.slider.maximum() - self.frameNumber.slider.minimum()):
            self.playForward()
        
    def jumpFrameBack(self):
        self.playCount.append(True)
        # Add this in case going back on first frame with no buffer on last frame
        toCheckBuffer = self.frameNumber.slider.value()-1
        if toCheckBuffer < self.frameNumber.slider.minimum():
            toCheckBuffer = self.frameNumber.slider.maximum()
        if toCheckBuffer > (len(self.timeLineDict) - 1):
            toCheckBuffer = (len(self.timeLineDict) - 1)

        if self.imgDict["buffer"][toCheckBuffer] != None:
            if ((self.frameNumber.slider.value() - 1) < self.frameNumber.slider.minimum()):
                self.frameNumber.slider.setValue(self.frameNumber.slider.maximum())
            else:
                self.frameNumber.slider.setValue(self.frameNumber.slider.value()-1)
        else:
            self.bufferLoad(self.seqDict)

        if len(self.playCount) == (self.frameNumber.slider.maximum() - self.frameNumber.slider.minimum()):
            self.playBack()


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
        newVersion = [(openDialog[0])]

        imagesFromNewVersion = list((seqFromPath(newVersion)).values())[0]

        currentPos = self.frameNumber.slider.value()
        shot = self.timeLineDict[currentPos]["shot"]

        # Getting number of version to know what tag to give the newest one
        numberOfVersions = len(list(self.imgDict["version"][shot].keys())) - 1
        self.imgDict["version"][shot]["v_{}".format(str(numberOfVersions+1).zfill(4))] = imagesFromNewVersion

        self.listVersions()

    def buildVersioningDict(self):
        # Building the versioning dictionnary
        for i in self.seqDict:
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
        Modify listA so it matches the len of listB and only contains items from listA
        '''
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
        currentPos = (self.frameNumber.slider.value())

        if currentPos > (len(self.timeLineDict) - 1):
            currentPos = (len(self.timeLineDict) - 1)

        shot =  self.timeLineDict[currentPos]["shot"]
        posRelativeToShot = 0
        for anyshot in self.seqDict:
            if len(self.seqDict[anyshot]) < currentPos:
                 #print("Not in shot {}, continuing".format(anyshot))
                posRelativeToShot += - len(self.seqDict[anyshot])
        posRelativeToShot += currentPos
        return(posRelativeToShot)

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
        self.expopop.show()
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
        jsonPath = "{}config.json".format(absPath)
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
            cc, cc, dispView = initOcio2(self.imgDict["ocioVar"])
            self.imgDict["ocio"]["ocioIn"] = cc[0]
            self.imgDict["ocio"]["ocioOut"] = cc[0]
            self.imgDict["ocio"]["ocioDisplay"] = dispView[0]


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
        img= bufferBackEnd(self.kwargs, self.args[0], self.args[1])
        #print(self.kwargs)
        #print("img obtained in {}".format(t1-t0))

        self.signals.finished.emit()
        if (type(img) == tuple):
            self.signals.result.emit(img[0], img[1])

class NextWorkerSignals(QtCore.QObject):
    '''
    Defines signals available from running NextWorker Thread
    
    result
        string
    '''
    finished = QtCore.pyqtSignal()
    result = QtCore.pyqtSignal(str)

class NextWorker(QtCore.QRunnable):
    '''
    Worker Thread emitting signal every 1/24th of a second
    '''
    def __init__(self):
        super(NextWorker, self).__init__()
        self.signals = NextWorkerSignals()

    def run(self):
        time.sleep(1/24)

        self.signals.result.emit("Ok")


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
        for i in range(widget.bufferRange):
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
        self.toggleBtn.clicked.connect(self.contactSheetMode)
        if self.toggleBtn.isChecked() == False:
            self.toggleBtn.click()
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

        # Number of frames
        self.threadNumberLabel = QtWidgets.QLabel("Number of threads :")
        self.threadNumber = QtWidgets.QSpinBox()
        self.threadNumber.valueChanged.connect(self.updateThreads)
        # Getting default value of max threads
        self.threadNumber.setValue(widget.maxThreads - 4)
        # Size of buffer batch
        self.threadBatchLabel = QtWidgets.QLabel("Buffer Batch Size for heavy EXRs :")
        self.threadBatch = QtWidgets.QSpinBox()
        self.threadBatch.setValue(4)
        self.threadBatch.valueChanged.connect(self.updateBatchSize)
        
        self.threadLayout.addWidget(self.threadNumberLabel)
        self.threadLayout.addStretch()
        self.threadLayout.addWidget(self.threadNumber)
        self.batchLayout.addWidget(self.threadBatchLabel)
        self.batchLayout.addStretch()
        self.batchLayout.addWidget(self.threadBatch)
        layout.addLayout(self.threadLayout)
        layout.addLayout(self.batchLayout)
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
        self.ocioPath = QtWidgets.QLineEdit("{}ocio/config.ocio".format(realPath))
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

        

        # Clearing the previous contents of menus
        self.comboCS.clear()
        self.comboInput.clear()
        self.comboDisplay.clear()

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
        # Check if a config.json exists 
        jsonPath = "config.json"
        absoluteOcioPath = (os.path.realpath(self.ocioPath.text()))
        if (os.path.exists(absoluteOcioPath) == True):
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
        with open("{}{}".format(realPath, jsonPath), "w") as file:
            json.dump(jsonData, file)
        file.close()

    def checkIfJsonExists(self):
        jsonPath = "config.json"
        if (os.path.exists("{}{}".format(realPath,jsonPath)) == True):
            with open("{}{}".format(realPath,jsonPath), "r") as file:
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
    app.setStyle("Fusion")

    widget = MyWidget()
    widget.resize(800,600)
    widget.show()

    # Init the gui with the default pyVexr splashcreen in order to enable drag and drop from the start
    filenames = ["{}imgs/pyVexrSplashScreen_v001.exr".format(absPath)]
    widget.updateImgDict(filenames)

    sys.exit(app.exec())
