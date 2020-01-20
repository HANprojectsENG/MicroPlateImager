#!/usr/bin/python3
# -*- coding: utf-8 -*-
import numpy as np
import lib.signal as signal
#from PyQt5.QtCore import QObject, QThread, QTimer, QEventLoop, pyqtSignal, pyqtSlot
from PySide2.QtCore import QObject, QThread, QTimer, QEventLoop, Signal, Slot
from picamera import PiCamera
from picamera.array import PiRGBArray, PiYUVArray, PiArrayOutput
import time, datetime

class PiYArray(PiArrayOutput):
    """
    Produces a 2-dimensional Y only array from a YUV capture.
    Does not seem faster than PiYUV array...
    """
    def __init__(self, camera, size=None):
        super(PiYArray, self).__init__(camera, size)
##        width, height = resolution
        self.fwidth, self.fheight = raw_resolution(self.size or self.camera.resolution)
        self.y_len = self.fwidth * self.fheight
##        uv_len = (fwidth // 2) * (fheight // 2)
##        if len(data) != (y_len + 2 * uv_len):
##            raise PiCameraValueError(
##            'Incorrect buffer length for resolution %dx%d' % (width, height))

    def flush(self):
        super(PiYArray, self).flush()
        a = np.frombuffer(self.getvalue()[:self.y_len], dtype=np.uint8)
        self.array = a[:self.y_len].reshape((self.fheight, self.fwidth))

## PiVideoStream class streams camera images to a numpy array
class PiVideoStream(QThread):
    name = "PiVideoStream"
    signals = signal.signalClass()
    pause = False
    CaptureStream = None
    PreviewStream = None
    CaptureArray = None
    PreviewArray = None
    CaptureFrame = None
    PreviewFrame = None
    
    ## The constructor.
    def __init__(self, resolution=(640,480), monochrome=False, framerate=24, effect='none', use_video_port=False):
        super().__init__()
        resolution = raw_resolution(resolution)
        self.frame = np.empty(resolution + (1 if monochrome else 3,), dtype=np.uint8)
        self.camera = PiCamera()
        self.initCamera(resolution, monochrome, framerate, effect, use_video_port)
        self.startMillis = None
        print(self.name + ": camera opened.")

    def __del__(self):
        self.wait()

    ## @brief PiVideoStream::msg(self, message) emits the message signal. This emit will be catched by the logging slot function in main.py.
    ## @param message is the string message to be emitted.
    def msg(self, message):
        if message is not None:
            self.signals.mes.emit(self.__class__.__name__ + ": " + str(message))
        return

    def run(self):
        try:
            self.fps = FPS().start()
            for f1 in self.previewStream:
                if (self.pause == True):
                    self.msg(self.name + ": paused.")
                    break # return from thread is needed
                else:
                    self.rawCapture.truncate(0) # clear the stream in preparation for the next frame
                    self.PreviewArray.truncate(0) # clear the stream in preparation for the next frame
                    for f2 in self.stream:
                        self.rawCapture.seek(0)
                        self.CaptureFrame = f2.array
                        self.signals.capReady.emit()
                        break
                    self.PreviewArray.seek(0)
                    self.PreviewFrame = f1.array
                    self.fps.update()
                    if self.startMillis is not None:
                        None
                    self.startMillis = int(round(time.time() * 1000))
                    self.signals.prvReady.emit()    
                           
        except Exception as err:
            print(err)
            self.msg(self.name + ": error running thread.")
            pass

        finally:
            self.camera.stop_preview()
            self.msg(self.name + ": quit.")

    def initCamera(self, resolution=(640,480), monochrome=False, framerate=24, effect='none', use_video_port=False):
        self.msg(self.name + "Init: resolution = " + str(resolution))
        self.camera.resolution = resolution        
        self.camera.image_effect = effect
        self.camera.image_effect_params = (2,)
        self.camera.iso = 100 # should force unity analog gain
        self.monochrome = monochrome # spoils edges
        self.camera.framerate = framerate
        if self.monochrome:
            self.rawCapture = PiYArray(self.camera, size=self.camera.resolution)
            self.PreviewArray = PiYArray(self.camera, size=(640,480))
            self.stream = self.camera.capture_continuous(self.rawCapture, 'yuv', use_video_port)
            self.previewStream = self.camera.capture_continuous(output=self.PreviewArray, format='yuv', use_video_port=use_video_port, splitter_port=1, resize=(640,480))
        else:
            self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
            self.PreviewArray = PiRGBArray(self.camera, size=(640,480))
            self.stream = self.camera.capture_continuous(self.rawCapture, 'bgr', use_video_port)
            self.previewStream = self.camera.capture_continuous(output=self.PreviewArray, format='bgr', use_video_port=use_video_port, splitter_port=1, resize=(640,480))

        GeneralEventLoop = QEventLoop(self)
        QTimer.singleShot(2, GeneralEventLoop.exit)
        GeneralEventLoop.exec_()            
        
    @Slot()
    def stop(self):
        self.pause = True
        self.fps.stop()
        print(self.name + ": approx. acquisition speed: {:.2f} fps".format(self.fps.fps()))        
        self.quit()
        self.msg(self.name + ": closed.")
        
    @Slot()
    def changeCameraSettings(self, resolution=(640,480), framerate=24, format="bgr", effect='none', use_video_port=False):
        print("in function PiVideoStream::changeCameraSettings()")
        self.pause = True
        self.wait()
        self.initCamera(resolution, framerate, format, effect, use_video_port)
        self.pause = False
        self.start()  # restart thread

class FPS:
	def __init__(self):
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
