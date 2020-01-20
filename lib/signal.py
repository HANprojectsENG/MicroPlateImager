from PySide2.QtCore import Signal, QObject
import numpy as np

## @brief signalClass(QObject) contains signals. 
# @param QObject is inherited from, because Signal() may be used only when the class is inherited from QObject, this way the signal can be used by each class.
class signalClass(QObject):
    ## @param mes is the signal used in all classes to emit messages which are then displayed in the log window by the MainWindow class
    mes = Signal(str) 
    
    ## ImageProcessor
    error = Signal(tuple)
    result = Signal(np.ndarray)
    finished = Signal()
    resultBlobs = Signal(np.ndarray, list)

    ## Scanner
    #imageUpdate = Signal()
    prvReady = Signal()
    capReady = Signal()
    previewUpdated = Signal()
    captureUpdated = Signal()
    previewRawUpdated = Signal()
    captureRawUpdated = Signal()
    signal_rdy_calibrator = Signal() # snapshot taken signal
    signal_rdy_positioner = Signal(np.ndarray) # snapshot taken signal
    signal_rdy_batchrun = Signal()    

    ## Well positioner
    snapshot_requested = Signal(str)
    process_active = Signal()
    process_inactive = Signal()
    target_located = Signal(tuple)
    well_located = Signal(tuple)
    well_unknown = Signal()
    
    ## STM data available
    stm_read_request = Signal()
    confirmation = Signal() ## emitted if stm message contains confirmation of Gcode execution
    first_move = Signal()

    ## Main Window
    windowClosing = Signal()
    
    
