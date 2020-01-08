from PySide2.QtCore import *
import numpy as np

class ObjectSignals(QObject):
    '''
    Defines the signals available from an object.

    Supported signals are:

    finished
        No data
    
    error
        `tuple` (exctype, value, traceback.format_exc() )
    
    result
        `image` data returned from processing, np.ndarray

    progress
        `int` indicating % progress 

    '''
    finished = Signal()
    error = Signal(tuple)
    message = Signal(str)
    result = Signal(np.ndarray)
    progress = Signal(int)
    resultBlobs = Signal(np.ndarray, list)
