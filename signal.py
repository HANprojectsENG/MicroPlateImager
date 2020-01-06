from PySide2.QtCore import Signal, QObject

## @brief signalClass(QObject) contains a signal. 
# @param QObject is passed because Signal() may be used only when the class is inherited from QObject. 
# this way the signal can be used by each class, even though it does not inherit from QObject.
class signalClass(QObject):
    sig = Signal(str)
    imageUpdate = Signal()
    windowClosing = Signal()