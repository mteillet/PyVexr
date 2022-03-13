# Main GUI for pyVexr

# PyVexr_gui.py

import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from pyVexr_main import loadImg

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyVexr -- OpenExr Viewer") 

        # StyleSheet settings
        self.setStyleSheet("color: white; background-color: rgb(11,11,11)")
        

        ####################################
        # Code for the PyVexr Main windows #
        ####################################

        self.file = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.file.setText("File Space")
        
        self.channels = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.channels.setText("Exr Channels")

        self.img = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.img.setText("IMG")
        self.load = QtWidgets.QPushButton("Load")
        self.load.clicked.connect(self.function)

        self.version = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.version.setText("Versions")

        self.frameNumber = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.frameNumber.setText("Frame Number")

        self.player = QtWidgets.QLabel(alignment = QtCore.Qt.AlignCenter)
        self.player.setText("Player")

        #############################
        # Layout for the PyVexr GUI #
        #############################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        
        self.topBarLayout = QtWidgets.QHBoxLayout()
        self.topBarLayout.addWidget(self.file)

        self.centerLayout = QtWidgets.QHBoxLayout()
        self.channelsLayout = QtWidgets.QVBoxLayout()
        self.channelsLayout.addWidget(self.channels)
        self.imgLayout = QtWidgets.QVBoxLayout()
        self.imgLayout.addWidget(self.img)
        self.imgLayout.addWidget(self.load)
        self.versionsLayout = QtWidgets.QVBoxLayout()
        self.versionsLayout.addWidget(self.version)
        self.centerLayout.addLayout(self.channelsLayout)
        self.centerLayout.addLayout(self.imgLayout)
        self.centerLayout.addLayout(self.versionsLayout)

        self.frameNumLayout = QtWidgets.QHBoxLayout()
        self.frameNumLayout.addWidget(self.frameNumber)
        
        self.playerLayout = QtWidgets.QHBoxLayout()
        self.playerLayout.addWidget(self.player)

        self.mainLayout.addLayout(self.topBarLayout)
        self.mainLayout.addLayout(self.centerLayout)
        self.mainLayout.addLayout(self.frameNumLayout)
        self.mainLayout.addLayout(self.playerLayout)

    ###############################
    # Code for the Slot functions #
    ###############################
    @QtCore.pyqtSlot()
    def function(self):
        loadImg()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800,600)
    widget.show()

    sys.exit(app.exec())
