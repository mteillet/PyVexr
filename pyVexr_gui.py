# Main GUI for pyVexr

# PyVexr_gui.py

import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from pyVexr_main import loadImg, interpretRectangle
from math import sqrt

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyVexr -- OpenExr Viewer") 

        # StyleSheet settings
        self.setStyleSheet("color: white; background-color: rgb(11,11,11)")
        self.setMouseTracking(True)
        self._zoom = 0
        

        ####################################
        # Code for the PyVexr Main windows #
        ####################################

        # Menu bar area
        self.file = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.menuBar = QtWidgets.QMenuBar()
        self.fileMenu = self.menuBar.addMenu('&File')
        self.editMenu = self.menuBar.addMenu('&Edit')
        self.colorspaceMenu = self.menuBar.addMenu('&Colorspace')
        self.infoMenu = self.menuBar.addMenu('&Info')

        # Channel area - to make it appear using something containing the widgets and toggle its visibility on or off
        self.channels = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.channels.setText("Exr Channels")
        self.popupChannels = QtWidgets.QLabel()
        self.popupChannels.setText("- This is a channel")
        #self.channelsFrame.hide()

        # Image area - using a QGraphicsScene, a QGraphicsPixmap for image display and a QGraphicsRect for tracking the user view and zoom
        self.imgZone = QtWidgets.QGraphicsScene()
       
        # RectWidget for tracking the view relative to the image
        self.viewArea = QtWidgets.QGraphicsRectItem(0,0,10,10)
        # Giving a color to the default rect -- only for debugging purposes
        self.viewArea.setBrush(QtGui.QColor(255, 0, 0, 30))

        self.image = QtWidgets.QGraphicsPixmapItem()
        self.imgZone.addItem(self.image)
        self.imgZone.addItem(self.viewArea)
        
        self.imgViewer = QtWidgets.QGraphicsView(self.imgZone)
        self.imgViewer.viewport().setMouseTracking(True)
        self.imgViewer.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.imgViewer.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        # Temp img load button
        self.img = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.img.setText("IMG")
        self.load = QtWidgets.QPushButton("Load")
        self.load.clicked.connect(self.function)

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

        # Main Center layout #

        self.centerLayout = QtWidgets.QHBoxLayout()
        self.channelsLayout = QtWidgets.QVBoxLayout()
        self.channelsLayout.addWidget(self.channels)
        self.channelsLayout.addWidget(self.popupChannels)
        #self.channelsLayout.addWidget(self.channelsFrame)
        
        self.imgLayout = QtWidgets.QVBoxLayout()
        self.imgLayout.addWidget(self.imgViewer)
        self.imgLayout.addWidget(self.load)
        
        self.versionsLayout = QtWidgets.QVBoxLayout()
        self.versionsLayout.addWidget(self.version)
        self.centerLayout.addLayout(self.channelsLayout)
        self.centerLayout.addLayout(self.imgLayout, stretch = 1)
        self.centerLayout.addLayout(self.versionsLayout)

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
    def function(self):
        tempImg = loadImg()
        
        convertToQt = QtGui.QImage(tempImg[0], tempImg[1], tempImg[2], tempImg[3], QtGui.QImage.Format_RGB888)
        convertedImg = convertToQt.scaled(800, 600, QtCore.Qt.KeepAspectRatio)

        
        # Set pixmap in self.image
        self.image.setPixmap(QtGui.QPixmap.fromImage(convertedImg))

        # Give the rectangle view area the coordinates of the pixmap image after the image has been loaded
        imgCoordinates = interpretRectangle(str(self.image.boundingRect()))
        self.viewArea.setRect(imgCoordinates[0],imgCoordinates[1],imgCoordinates[2],imgCoordinates[3])

        # Fit in view after first load
        self.imgViewer.fitInView(self.viewArea, QtCore.Qt.KeepAspectRatio)
        # Toggle visibility on widget
        #self.channelsFrame.setHidden(not self.channelsFrame.isHidden())

    def resizeEvent(self, event):
        #print("Resize")
        # Fit image in view based on resize of the window
        self.imgViewer.fitInView(self.viewArea, QtCore.Qt.KeepAspectRatio)


    def mousePressEvent(self, event):
        print("Mouse Press")
        
    def mouseMoveEvent(self, event):
        print("Mouse Move")

        
    # Zooming using mouse wheel
    def wheelEvent(self, event):
        # Gettubg the zoom direction
        wheelDirection = (event.angleDelta().y())
        # Get the rectangle size
        rectCoordinates = interpretRectangle(str(self.viewArea.rect()))
        # Check coordinates and sets the rectangle size in ordre to avoid unatural scrolling limitation because of the X or Y difference in size
        if (sqrt((rectCoordinates[3] - rectCoordinates[1])**2) > sqrt((rectCoordinates[2] - rectCoordinates[0])**2)):
            self.viewArea.setRect(rectCoordinates[0]+(wheelDirection/2),rectCoordinates[1],rectCoordinates[2]-wheelDirection,rectCoordinates[3])
        else:
            self.viewArea.setRect(rectCoordinates[0]+(wheelDirection/2),rectCoordinates[1]+(wheelDirection/2),rectCoordinates[2]-wheelDirection,rectCoordinates[3]-wheelDirection)
        # Also sets the scene rectangle to avoid strangle scrolling behaviour !!!
        sceneCoordinates = interpretRectangle(str(self.viewArea.rect()))
        self.imgViewer.setSceneRect(sceneCoordinates[0],sceneCoordinates[1],sceneCoordinates[2],sceneCoordinates[3])
        # Fit in view to follow the rectangle
        self.imgViewer.fitInView(self.viewArea, QtCore.Qt.KeepAspectRatio)

    # All keypresses    
    def keyPressEvent(self, event):
        # Frame the image -- KEYPRESS F 
        # Set the viewArea back to the default coordinates of the self.image pixmap and fits it in view
        if (event.key() == QtCore.Qt.Key_F):
            imgCoordinates = interpretRectangle(str(self.image.boundingRect()))
            self.viewArea.setRect(imgCoordinates[0],imgCoordinates[1],imgCoordinates[2],imgCoordinates[3])
            self.imgViewer.fitInView(self.image, QtCore.Qt.KeepAspectRatio)
            self.imgViewer.fitInView(self.viewArea, QtCore.Qt.KeepAspectRatio)
            

        # Panning image -- KEYPRESS H,J,K,L , VIM like
        if (event.key() == QtCore.Qt.Key_H):
            #print("Left")
            imgCoordinates = interpretRectangle(str(self.viewArea.rect()))
            self.viewArea.setRect(imgCoordinates[0]-1,imgCoordinates[1],imgCoordinates[2]-1,imgCoordinates[3])
            sceneCoordinates = interpretRectangle(str(self.viewArea.rect()))
            self.imgViewer.setSceneRect(sceneCoordinates[0],sceneCoordinates[1],sceneCoordinates[2],sceneCoordinates[3])
        if (event.key() == QtCore.Qt.Key_J):
            #print("Up")
            imgCoordinates = interpretRectangle(str(self.viewArea.rect()))
            self.viewArea.setRect(imgCoordinates[0],imgCoordinates[1]-1,imgCoordinates[2],imgCoordinates[3]-1)
            sceneCoordinates = interpretRectangle(str(self.viewArea.rect()))
            self.imgViewer.setSceneRect(sceneCoordinates[0],sceneCoordinates[1],sceneCoordinates[2],sceneCoordinates[3])
        if (event.key() == QtCore.Qt.Key_K):
            #print("Down")
            imgCoordinates = interpretRectangle(str(self.viewArea.rect()))
            self.viewArea.setRect(imgCoordinates[0],imgCoordinates[1]+1,imgCoordinates[2],imgCoordinates[3]+1)
            sceneCoordinates = interpretRectangle(str(self.viewArea.rect()))
            self.imgViewer.setSceneRect(sceneCoordinates[0],sceneCoordinates[1],sceneCoordinates[2],sceneCoordinates[3])
        if (event.key() == QtCore.Qt.Key_L):
            #print("Right")
            imgCoordinates = interpretRectangle(str(self.viewArea.rect()))
            self.viewArea.setRect(imgCoordinates[0]+1,imgCoordinates[1],imgCoordinates[2]+1,imgCoordinates[3])
            sceneCoordinates = interpretRectangle(str(self.viewArea.rect()))
            self.imgViewer.setSceneRect(sceneCoordinates[0],sceneCoordinates[1],sceneCoordinates[2],sceneCoordinates[3])
        

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800,600)
    widget.show()

    sys.exit(app.exec())
