from abc import ABC, abstractmethod
from PySide2.QtCore import *
import time
import lib.signal as signal

## @author Jeroen Veen
class Manipulator(ABC):
    """Documentation for a class.
 
    More details.
    """      

    def __init__(self, Name):
        """The constructor."""        
        super(Manipulator,self).__init__()
        self.name = Name
        self.image = None
        self.show = False # Show intermediate results
        self.processsingTime = 0 # processing time [ms]
        self.startTime = 0
        self.signals = signal.signalClass()
    
    ## @brief Manipulator::msg(self, message) emits the message signal. This emit will be catched by the logging slot function in main.py.
    # @param message is the string message to be emitted.
    def msg(self, message):
        if message is not None:
            self.signals.mes.emit(self.__class__.__name__ + ": " + str(message))
        return

    @abstractmethod
    def start(self):
        """Process image."""        
        pass

    def startTimer(self):
        """Start millisecond timer."""        
        self.startTime = int(round(time.time() * 1000))
        self.msg('I: {} started'.format(self.name))            
        

    def stopTimer(self):
        """Stop millisecond timer."""        
        self.processsingTime = int(round(time.time() * 1000)) - self.startTime
        self.msg('I: {} finished in {} ms'.format(self.name, self.processsingTime))
        
         
