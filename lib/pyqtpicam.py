#!/usr/bin/python3
# -*- coding: utf-8 -*-
import numpy as np
import signal
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
    message = signal.signalClass()#pyqtSignal(str)  # Message signal
    ready = signal.signalClass()#pyqtSignal() # Ready signal
    pause = False
    
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

    def run(self):
        try:
            self.fps = FPS().start()
            for f in self.stream:
                if (self.pause == True):
                    self.message.sig.emit(self.name + ": paused.")
                    break  # return from thread is needed
                else:
                    self.rawCapture.truncate(0)  # clear the stream in preparation for the next frame
##                    self.rawCapture.seek(0) 
                    self.frame = f.array # grab the frame from the stream
                    self.fps.update()
                    if self.startMillis is not None:
                        self.message.sig.emit(self.name + ": processing delay = " + str(int(round(time.time() * 1000)) - self.startMillis) + " ms")
                    self.startMillis = int(round(time.time() * 1000))
                    self.ready.imageUpdate.emit()                    
        except Exception as err:
            print(err)
            self.message.sig.emit(self.name + ": error running thread.")
            pass
        finally:
            self.camera.stop_preview()
            self.message.sig.emit(self.name + ": quit.")

    def initCamera(self, resolution=(640,480), monochrome=False, framerate=24, effect='none', use_video_port=False):
        self.message.sig.emit(self.name + "Init: resolution = " + str(resolution))
        self.camera.resolution = resolution        
        self.camera.image_effect = effect
        self.camera.image_effect_params = (2,)
        self.camera.iso = 100 # should force unity analog gain
##        self.camera.video_denoise = True
        self.monochrome = monochrome # spoils edges
        # dunno if setting awb mode manually is really useful
##        self.camera.awb_mode = 'off'
##        self.camera.awb_gains = 5.0
##        self.camera.meter_mode = 'average'
##        self.camera.exposure_mode = 'auto'  # 'sports' to reduce motion blur, 'off'after init to freeze settings
        self.camera.framerate = framerate
        if self.monochrome:
##            self.camera.color_effects = (128,128) # return monochrome image, not required if we take Y frame only.
            self.rawCapture = PiYArray(self.camera, size=self.camera.resolution)
            self.stream = self.camera.capture_continuous(self.rawCapture, 'yuv', use_video_port)
        else:
            self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
            self.stream = self.camera.capture_continuous(self.rawCapture, 'bgr', use_video_port)
##        time.sleep(2)
        GeneralEventLoop = QEventLoop(self)
        QTimer.singleShot(2, GeneralEventLoop.exit)
        GeneralEventLoop.exec_()            
        
    #@pyqtSlot()
    @Slot()
    def stop(self):
        self.pause = True
        self.fps.stop()
        print(self.name + ": approx. acquisition speed: {:.2f} fps".format(self.fps.fps()))        
##        self.wait()
##        self.rawCapture.close()
##        self.camera.close()
        self.quit()
        self.message.sig.emit(self.name + ": closed.")
##        self.exit(0)
        
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
