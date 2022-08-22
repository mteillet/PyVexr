# Main GUI for pyVexr

# PyVexr_gui.py

import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui
from pyVexr_main import loadImg, interpretRectangle, initOCIO, ocioLooksFromView, exrListChannels, updateImg, updateExposure
from math import sqrt

# Subclassing graphicsView in order to be able to track mouse movements in the scene
class graphicsView(QtWidgets.QGraphicsView):
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
        # + and - keys
        self.activeKeys[43] = False
        self.activeKeys[45] = False


        # Active mouse dictionnary
        self.activeMouse = {}
        self.activeMouse[QtCore.Qt.LeftButton] = False
        self.activeMouse[QtCore.Qt.RightButton] = False

        # Mouse Move list [x, y]
        self.mouseMove = [[],[]]

    ###############################
    # Code for the Slot functions #
    ###############################
    @QtCore.pyqtSlot()
    def mousePressEvent(self, event):
        if event.button() in self.activeMouse:
            self.activeMouse[event.button()] = True
        self.update()


    def mouseReleaseEvent(self, event):
        if event.button() in self.activeMouse:
            self.activeMouse[event.button()] = False
            
        self.update()

    def keyPressEvent(self, event):
        #print("GraphicsView " + str(event.key()))
        if event.key() in self.activeKeys:
                self.activeKeys[event.key()] = True
        if event.key() == QtCore.Qt.Key_E:
            widget.showExposureText()
        # Expo change if key hit is + of -
        if (event.key() == 43) | (event.key() == 45):
            # Boost expo
            widget.exposureChange(event.key())



    def keyReleaseEvent(self, event):
        if event.key() in self.activeKeys:
            self.activeKeys[event.key()] = False   

        # F for recenter
        if str(event.key()) == str(70):
            # Issue need to reset the zoom index too, otherwise won't work
            print("Key is F")
            # Reset zoom
            self.resetTransform()
            # Reset position
            self.setSceneRect(0, 0, self.defaultSceneRect[2], self.defaultSceneRect[3])
            #print(interpretRectangle(str(self.sceneRect())))
    
    def mouseMoveEvent(self, event):
        # Storing the initial scene rect
        if len(self.defaultSceneRect) == 0:
            temp = interpretRectangle(str(self.sceneRect()))
            for val in temp:
                self.defaultSceneRect.append(val)
            print(self.defaultSceneRect)

        # Translate view
        sceneCoordinates = interpretRectangle(str(self.sceneRect()))
        if (self.activeKeys[16777251] == True) & (self.activeMouse[QtCore.Qt.LeftButton] == True):
            sceneCoordinates = interpretRectangle(str(self.sceneRect()))
            position = QtCore.QPointF(event.pos())
            self.mouseMove[0].append(position.x())
            self.mouseMove[1].append(position.y())
            #print(self.mouseMove)
            if ((len(self.mouseMove[0]) >= 2) & (len(self.mouseMove[1]) >= 2) ):
                mouseMoveX =  (self.mouseMove[0][1] - self.mouseMove[0][0])
                mouseMoveY =  (self.mouseMove[1][1] - self.mouseMove[1][0]) 
                # If exceptions for mouse move
                if (mouseMoveX > 10) | (mouseMoveX < -10):
                    mouseMoveX = 0
                if (mouseMoveY > 10) | (mouseMoveY < -10):
                    mouseMoveY = 0
                # Moving the Graphics view adding the mousemov vars to the current coordinates of the scene rect
                sceneCoordinates = interpretRectangle(str(self.sceneRect()))
                self.setSceneRect(sceneCoordinates[0]-mouseMoveX,sceneCoordinates[1]-mouseMoveY,sceneCoordinates[2]-mouseMoveX,sceneCoordinates[3]-mouseMoveY)
                self.mouseMove[0] = []
                self.mouseMove[1] = []

        # Zoom view
        if (self.activeKeys[16777249] == True) & (self.activeMouse[QtCore.Qt.LeftButton] == True):
            # Storing the mouse moves in a declared list
            position = QtCore.QPointF(event.pos())
            
            self.mouseMove[0].append(position.x())
            self.mouseMove[1].append(position.y())

            if(len(self.mouseMove[1]) >= 2):
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyVexr -- OpenExr Viewer") 
        self.setWindowIcon(QtGui.QIcon("/home/martin/Documents/PYTHON/PyVexr/imgs/pyVexr_Icon_512.jpeg"))
        self.setAcceptDrops(True)

        # StyleSheet settings
        self.setStyleSheet("color: white; background-color: rgb(11,11,11)")
        self.setMouseTracking(True)
        self._zoom = 0
        
        # Global dict image related:
        self.imgDict = {}
        self.imgDict["path"] = []
        self.imgDict["ocio"] = {}
        self.imgDict["ocio"]["ocioIn"] = None
        self.imgDict["ocio"]["ocioOut"] = None
        self.imgDict["ocio"]["ocioLook"] = None
        self.imgDict["channel"] = None
        self.imgDict["exposure"] = 0

        ####################################
        # Code for the PyVexr Main windows #
        ####################################

        # Menu bar area
        self.file = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.menuBar = QtWidgets.QMenuBar()
        self.fileMenu = self.menuBar.addMenu('&File')
        self.openAction = self.fileMenu.addAction("Open        &-&C&t&r&l&+&O")
        self.openAction.triggered.connect(self.openFiles)
        self.editMenu = self.menuBar.addMenu('&Edit')
        # NEED TO HOOK CHANNEL MENU BAR TO A FUNCTION FOR SHOWING / HIDING THE CHANNELS
        #self.channelsMenu = self.menuBar.addMenu('&Channels')
        self.channelsAction = self.editMenu.addAction("Channels Pannel    &-&C")
        self.versionsAction = self.editMenu.addAction("Versions Pannel    &-&V")
        self.infosAction = self.editMenu.addAction("Help")
        self.channelsAction.triggered.connect(self.channelsClicked)
        self.versionsAction.triggered.connect(self.versionsClicked)
        #self.colorspaceMenu = self.menuBar.addMenu('&Colorspace')

        # OCIO dropdown
        ocioViews, looksDict, viewsList= initOCIO()
        # Setup dict in order to retrieve selected items
        self.ocioInLabel = QtWidgets.QLabel("Source Input:")
        self.ocioOutLabel = QtWidgets.QLabel("Output sRGB:")
        self.ocioLooksLabel = QtWidgets.QLabel("Look :")
        self.ocioIn = QtWidgets.QComboBox()
        self.ocioIn.activated.connect(self.ocioInChange)
        self.ocioOut = QtWidgets.QComboBox()
        self.ocioOut.activated.connect(self.ocioOutChange)
        self.ocioLooks = QtWidgets.QComboBox()
        self.ocioLooks.activated.connect(self.ocioLookChange)

        if "sRGB" in ocioViews and "Linear" in ocioViews:
            self.ocioIn.addItem("Linear")
        for i in ocioViews:
            if i != "Linear":
                self.ocioIn.addItem(i)
        for view in viewsList:
            self.ocioOut.addItem(view)
        self.ocioLooks.addItem("None")


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
        # Exposure text, hidden by default
        self.exposureText = QtWidgets.QGraphicsTextItem("Exposure : ")
        self.exposureText.setScale(2)
        self.exposureText.setDefaultTextColor(QtGui.QColor("white"))
        self.exposureText.hide()

        # Putting the objects in the scene
        self.image = QtWidgets.QGraphicsPixmapItem()
        self.imgZone.addItem(self.image)
        self.imgZone.addItem(self.viewArea)
        self.imgZone.addItem(self.exposureText)
        
        self.imgViewer = graphicsView(self)
        #self.imgViewer.setMouseTracking(True)
        self.imgViewer.setScene(self.imgZone)
        self.imgViewer.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.imgViewer.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.imgViewer.setAcceptDrops(True)

        # Temp img load button -- Will be replaced with a load images dropdown in the menu
        self.img = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.img.setText("IMG")

        # Version area - Need to replace with a floating window
        self.version = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.version.setText("Versions")

        # Slider for the frame sequence
        self.frameNumber = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.frameNumber.setValue(101)
        self.frameNumber.setMinimum(101)
        self.frameNumber.setMaximum(111)
        self.frameNumber.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.frameNumber.setStyleSheet("color: white")
        self.frameNumberLabel = QtWidgets.QLabel()
        self.frameNumberLabel.setText("Frame Number")
        
        # Player buttons area
        self.player = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.player.setText("Player")

        #############################
        # Layout for the PyVexr GUI #
        #############################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        
        # Top Bar
        self.topBarLayout = QtWidgets.QHBoxLayout()
        self.topBarLayout.addWidget(self.menuBar)
        self.topBarLayout.addStretch()
        self.topBarLayout.addWidget(self.ocioInLabel)
        self.topBarLayout.addWidget(self.ocioIn)
        self.topBarLayout.addWidget(self.ocioOutLabel)
        self.topBarLayout.addWidget(self.ocioOut)
        self.topBarLayout.addWidget(self.ocioLooksLabel)
        self.topBarLayout.addWidget(self.ocioLooks)

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
        self.frameNumLayout.addWidget(self.frameNumberLabel)
        self.frameNumLayout.addWidget(self.frameNumber, stretch = 1)
        
        self.playerLayout = QtWidgets.QHBoxLayout()
        self.playerLayout.addWidget(self.player)

        self.mainLayout.addLayout(self.topBarLayout)
        self.mainLayout.addLayout(self.centerLayout, stretch = 1)
        self.mainLayout.addLayout(self.frameNumLayout)
        self.mainLayout.addLayout(self.playerLayout)

    ###############################
    # Code for the Slot functions #
    ###############################
    @QtCore.pyqtSlot()
    def loadFile(self):
        #print(self.imgDict["path"])
        # OCIO DATA
        self.imgDict["ocio"]["ocioIn"] = self.ocioIn.currentText()
        self.imgDict["ocio"]["ocioOut"] = self.ocioOut.currentText()
        self.imgDict["ocio"]["ocioLook"] = self.ocioLooks.currentText()
        #print("Input : {0}\nOutput : {1} (sRGB)\nLook : {2}".format(self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"]))

        tempImg = loadImg(self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"],self.imgDict["path"])
        convertToQt = QtGui.QImage(tempImg[0], tempImg[1], tempImg[2], tempImg[3], QtGui.QImage.Format_RGB888)
        # If need to rescale the image
        #convertedImg = convertToQt.scaled(800, 600, QtCore.Qt.KeepAspectRatio)

        # Set pixmap in self.image
        self.image.setPixmap(QtGui.QPixmap.fromImage(convertToQt))

        # Give the rectangle view area the coordinates of the pixmap image after the image has been loaded
        imgCoordinates = interpretRectangle(str(self.image.boundingRect()))
        self.viewArea.setRect(imgCoordinates[0],imgCoordinates[1],imgCoordinates[2],imgCoordinates[3])

        # Fit in view after first load
        self.imgViewer.fitInView(self.viewArea, QtCore.Qt.KeepAspectRatio)
        # Toggle visibility on widget
        #self.channelsFrame.setHidden(not self.channelsFrame.isHidden())

    def updateImgDict(self, path):
        self.imgDict["path"] = path
        self.loadFile()
        self.listChannels()

    def dragEnterEvent(self, event):
        print("drag")
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

    def imageUpdate(self):
        #print("Updating image using the dictionnary")
        tempImg = updateImg(self.imgDict["path"],self.imgDict["channel"],self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"])
        convertToQt = QtGui.QImage(tempImg[0], tempImg[1], tempImg[2], tempImg[3], QtGui.QImage.Format_RGB888)
        self.image.setPixmap(QtGui.QPixmap.fromImage(convertToQt))

    def resizeEvent(self, event):
        #print("Resize")
        # Fit image in view based on resize of the window
        self.imgViewer.fitInView(self.viewArea, QtCore.Qt.KeepAspectRatio)

    def ocioInChange(self):
        sender = self.sender()
        self.imgDict["ocio"]["ocioIn"] = self.ocioIn.currentText()
        self.imageUpdate()

    def ocioOutChange(self):
        sender = self.sender()
        #print("Changed The View to : {}".format(sender.currentText()))
        looks = ocioLooksFromView(sender.currentText())
        self.ocioLooks.clear()
        self.ocioLooks.addItems(looks)
        # Updating the imgDict
        self.imgDict["ocio"]["ocioIn"] = self.ocioIn.currentText()
        self.imgDict["ocio"]["ocioOut"] = self.ocioOut.currentText()
        self.imgDict["ocio"]["ocioLook"] = self.ocioLooks.currentText()
        self.imageUpdate()

    def ocioLookChange(self):
        sender = self.sender()
        self.imgDict["ocio"]["ocioLook"] = self.ocioLooks.currentText()
        self.imageUpdate()

    def exposureChange(self, key):
        # Tweak expo only if E has been pressed before, and therefore the text is toggled on
        # Need to integrate the exposure in every call to backend image update, otherwise exposure will be reset on any other backend image call (such as ocio change or channel change)
        if (self.exposureText.isVisible() == True):
            #print(key)
            if key == 43:
                #print("Boost expo")
                self.imgDict["exposure"] += 0.1
                self.updateExposure()
                tempImg = updateExposure(self.imgDict["path"],self.imgDict["channel"],self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"],self.imgDict["exposure"])
                convertToQt = QtGui.QImage(tempImg[0], tempImg[1], tempImg[2], tempImg[3], QtGui.QImage.Format_RGB888)
                self.image.setPixmap(QtGui.QPixmap.fromImage(convertToQt))

            if key == 45:
                #print("Lower expo")
                self.imgDict["exposure"] -= 0.1
                self.updateExposure()
                tempImg = updateExposure(self.imgDict["path"],self.imgDict["channel"],self.imgDict["ocio"]["ocioIn"],self.imgDict["ocio"]["ocioOut"],self.imgDict["ocio"]["ocioLook"],self.imgDict["exposure"])
                convertToQt = QtGui.QImage(tempImg[0], tempImg[1], tempImg[2], tempImg[3], QtGui.QImage.Format_RGB888)
                self.image.setPixmap(QtGui.QPixmap.fromImage(convertToQt))


    def updateExposure(self):
        self.exposureText.setPlainText("Exposure : {}".format(round(self.imgDict["exposure"], 2)))

    def showExposureText(self):
        if (self.exposureText.isVisible() == False):
            self.exposureText.show()
            self.updateExposure()
        else:
            self.exposureText.hide()




if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800,600)
    widget.show()

    # Init the gui with the default pyVexr splashcreen in order to enable drag and drop from the start
    filenames = ["/home/martin/Documents/PYTHON/PyVexr/imgs/pyVexrSplashScreen_v001.exr"]
    widget.updateImgDict(filenames)

    sys.exit(app.exec())
