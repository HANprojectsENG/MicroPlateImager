from PySide2.QtCore import Signal, QObject
import numpy as np

## @brief signalClass(QObject) contains signals. 
# @param QObject is passed because Signal() may be used only when the class is inherited from QObject, this way the signal can be used by each class.
class signalClass(QObject):
    ## @param mes is the signal used in all classes to emit messages which are then displayed in the log window by the MainWindow class
    mes = Signal(str) 
    error = Signal(tuple)
    result = Signal(np.ndarray)
    finished = Signal()
    imageUpdate = Signal()
    resultBlobs = Signal(np.ndarray, list)

    ## Scanner
    prvReady = Signal()
    capReady = Signal()
    previewUpdated = Signal()
    captureUpdated = Signal()
    previewRawUpdated = Signal()
    captureRawUpdated = Signal()
    signal_rdy_calibrator = Signal() # snapshot taken signal
    signal_rdy_positioner = Signal(np.ndarray) # snapshot taken signal
    signal_rdy_batchrun = Signal()    

    ## Main Window
    windowClosing = Signal()
    
    ## Well position evaluator
    snapshot_requested = Signal(str)
    process_active = Signal()
    process_inactive = Signal()
    target_located = Signal(tuple)
    well_located = Signal(tuple)

    
