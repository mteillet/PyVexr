# Buffer workers for PyVexr

# pyVexr_buffer.py

from PyQt5 import QtCore

from pyVexr_main import bufferBackEnd


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
