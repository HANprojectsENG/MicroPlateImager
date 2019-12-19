#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time, datetime
import numpy as np
import matplotlib.pyplot as plt
from PySide2.QtCore import QObject, QThread, QTimer, QEventLoop, Signal, Slot
from picamera import PiCamera
from picamera.array import PiRGBArray, PiArrayOutput

class PiYArray(PiArrayOutput):
    """
    Produces a 2-dimensional Y only array from a YUV capture.
    Does not seem faster than PiYUV array...
    """
    def __init__(self, camera, size=None):
        super(PiYArray, self).__init__(camera, size)
        self.fwidth, self.fheight = raw_resolution(self.size or self.camera.resolution)
        self.y_len = self.fwidth * self.fheight

    def flush(self):
        super(PiYArray, self).flush()
        a = np.frombuffer(self.getvalue()[:self.y_len], dtype=np.uint8)
        self.array = a[:self.y_len].reshape((self.fheight, self.fwidth))

## PiVideoStream class streams camera images to a numpy array
# noinspection PyAttributeOutsideInit,PyAttributeOutsideInit
class PiVideoStream(QThread):
    message = Signal(str)  # Message signal
    framedelay = Signal(float)  # Message signal
    CapReady = Signal() # Ready signal
    PrvReady = Signal() # Ready signal
    stopped = Signal() # Stopping signal
    pause = False
    CaptureStream = None
    PreviewStream = None
    CaptureArray = None
    PreviewArray = None
    CaptureFrame = None
    PreviewFrame = None
    camera = None
    
    ## The constructor.
    def __init__(self, resolution=(640,480), monochrome=False, framerate=24, effect='none', use_video_port=False):
        super().__init__()        
        if(resolution == (1640,1232)): #frame will be rounded up. use below frame instead to prevent segmentation faults.
            self.CaptureFrame = np.empty((1664,1232) + (1 if monochrome else 3,), dtype=np.uint8)
        else:
            self.CaptureFrame = np.empty(resolution + (1 if monochrome else 3,), dtype=np.uint8)
        self.PreviewFrame = np.empty((640,480) + (1 if monochrome else 3,), dtype=np.uint8)  
        self.camera = PiCamera()
        self.initCamera(resolution, monochrome, framerate, effect, use_video_port)
        self.startMillis = None

    def initCamera(self, resolution=(640,480), monochrome=False, framerate=24, effect='none', use_video_port=False):
            self.camera.resolution = resolution        
            self.camera.image_effect = effect
            self.camera.image_effect_params = (2,)
            self.camera.rotation = 180
            self.camera.iso = 100 # should force unity analog gain
            self.monochrome = monochrome # spoils edges
            self.camera.framerate = framerate
            if self.monochrome:
                self.CaptureArray = PiYArray(self.camera, size=self.camera.resolution)
                self.PreviewArray = PiYArray(self.camera, size=(640,480))
                self.CaptureStream = self.camera.capture_continuous(output=self.CaptureArray, format='yuv', use_video_port=use_video_port)
                self.PreviewStream = self.camera.capture_continuous(output=self.PreviewArray, format='yuv', use_video_port=use_video_port, splitter_port=1, resize=(640,480))
            else:
                self.CaptureArray = PiRGBArray(self.camera, size=self.camera.resolution)
                self.PreviewArray = PiRGBArray(self.camera, size=(640,480))
                self.CaptureStream = self.camera.capture_continuous(output=self.CaptureArray, format='bgr', use_video_port=use_video_port)
                self.PreviewStream = self.camera.capture_continuous(output=self.PreviewArray, format='bgr', use_video_port=use_video_port, splitter_port=1, resize=(640,480))
            
            GeneralEventLoop = QEventLoop(self)
            QTimer.singleShot(2, GeneralEventLoop.exit)
            GeneralEventLoop.exec_()

    def run(self):
        try:
            self.fps = FPS().start()   
            for f1 in self.PreviewStream:
                self.CaptureArray.truncate(0)  # clear the stream in preparation for the next frame
                self.PreviewArray.truncate(0)  # clear the stream in preparation for the next frame
                for f2 in self.CaptureStream:
                    self.CaptureArray.seek(0)
                    self.CaptureFrame = f2.array
                    self.CapReady.emit()  
                    break
                self.PreviewArray.seek(0)
                self.PreviewFrame = f1.array
                self.fps.update()
                if self.startMillis is not None:
                    self.framedelay.emit(float(round(time.time() * 1000)))
                self.startMillis = float(round(time.time() * 1000))
                self.PrvReady.emit()                    
        finally:
            self.camera.stop_preview()
            self.stopped.emit()

    @Slot()
    def close(self):
        self.pause = True
        self.fps.stop()
        self.exit(0)

    def msg(self, message):
        self.message.emit(self.__class__.__name__ + ": " + str(message) )
        return

class FPS(QObject):
    ## The constructor.
    def __init__(self):
        super().__init__()
        # store the start time, end time, and total number of frames
        # that were examined between the start and end intervals
        self._start = None
        self._end = None
        self._numFrames = 0

    def start(self):
        # start the timer
        self._start = datetime.datetime.now()
        return self

    def stop(self):
        # stop the timer
        self._end = datetime.datetime.now()

    def update(self):
        # increment the total number of frames examined during the
        # start and end intervals
        self._numFrames += 1

    def elapsed(self):
        # return the total number of seconds between the start and
        # end interval
        return (self._end - self._start).total_seconds()

    def fps(self):
        # compute the (approximate) frames per second
        return self._numFrames / self.elapsed()

##    Gridsearch of a hyperparameter H (image quality) over a process variable P (focus).
##    Start signal initiates a search around a given point P_centre, with gridsize N_p and gridspacing dP.
##    The search is repeated N_n times, where the gridspacing is halved with each step.
# noinspection PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit,PyAttributeOutsideInit
class AutoFocus(QObject):
    message = Signal(str)  # Message signal
    VCValue = Signal(float)  # Focus signal
    ready = Signal()  # Autofocus done signal

    ## The constructor.
    def __init__(self, doPlot=False):
        super().__init__()
        self.doPlot = doPlot
        self.k = 0 # plot position counter
        self.running = False
        
    @Slot(float)
    def start(self, P_centre=0, N_p=11, dP=1, N_n=10):
        if self.running:
            self.msg( "Error: already running.")
        else:
            self.N_n = N_n  # Maximum number of iterations
            if (N_p & 1) != 1:  # Enforce N_p to be odd
                N_p += 1
                self.msg( "constructor warning : Grid size must be odd, so changed to " + str(N_p))
            self.N_p = N_p  # Grid size
            self.dP = dP  # Grid spacing, percentage change in VC current per step        
            self.H = np.zeros(shape=(self.N_p,1), dtype=float)
            self.P = np.zeros(shape=(self.N_p,1), dtype=float)
            self.P_centre = P_centre  # Set grid centre point
            self.n = 0  # First iteration
            self.p = 0  #
            self.p_sign = 1  # Process variable is rising
            if self.doPlot and (self.k == 0): # we have not plotted before
                self.k = 0 # plot position counter
                self.fig, (self.ax1, self.ax2) = plt.subplots(2,1)
                self.graph1 = None
                self.ax1.grid(True)
                self.ax1.set_ylabel("Image quality")
                self.graph2 = None
                self.ax2.grid(True)
                self.ax2.set_ylabel("Voice coil value")
                plt.show(block=False)        
            self.P[self.p] = self.P_centre-self.dP*int((self.N_p-1)/2)  # current process parameter
            self.VCValue.emit(self.P[self.p])  # Move to starting point of grid search
            self.mmsg( ": started.")
            self.running = True

    @Slot(float)
    def imgQualUpdate(self, imgQual=0):
        try:
            if self.running:  # autofocus is active
                self.msg("image quality updated.")
                self.H[self.p] = imgQual
                if self.doPlot:
               # draw grid lines
                    self.graph1 = self.ax1.plot(self.k, self.H[self.p], 'bo')[0]
                    self.graph2 = self.ax2.plot(self.k, self.P[self.p], 'bo')[0]
                # We need to draw *and* flush
                    self.fig.canvas.draw()
                    self.fig.canvas.flush_events()
                    self.k += 1
                self.p += self.p_sign  # Move to next grid point
                if 0 <= self.p < self.N_p: # We're on the grid, so set parameter value
                    self.P[self.p] = self.P_centre + (self.dP/(self.n+1))*(self.p-int((self.N_p-1)/2))  # compute next grid point
                    value = self.P[self.p]
                else:
                    self.n += 1  # New iteration
                    self.P_centre = self.P[np.argmax(self.H),0] # set new grid centre point
                    if self.n < self.N_n:  # still iterating
                        #self.P.fill(0) # clear parameter array 
                        self.H.fill(0) # clear hyperparameter array 
                        self.p_sign *= -1 # Reverse direction
                        self.p += self.p_sign  # Reset current grid point
                        self.P[self.p] = self.P_centre + (self.dP/(self.n+1))*(self.p-int((self.N_p-1)/2))  # compute next grid point
                        value = self.P[self.p]
                    else:
                        self.running = False
                        value = self.P_centre
                self.msg( "focus adapted to " + str(value))
                self.VCValue.emit(value)  # set next focus
        finally:
            self.msg("error " )
            return
        
    @Slot()
    def stop(self):
        try:
            self.running = False
        finally:
            self.msg("error ")
            return

    def msg(self, message):
        self.message.emit(self.__class__.__name__ + ": " + str(message) )
        return
        
def raw_resolution(resolution, splitter=False):
    """
    Round a (width, height) tuple up to the nearest multiple of 32 horizontally
    and 16 vertically (as this is what the Pi's camera module does for
    unencoded output).
    """
    width, height = resolution
    if splitter:
        fwidth = (width + 15) & ~15
    else:
        fwidth = (width + 31) & ~31
    fheight = (height + 15) & ~15
    return fwidth, fheight

