"""@package docstring
Image processor implements QThread
images are passed via wrapper
"""
 
#!/usr/bin/python3
# -*- coding: utf-8 -*-
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import numpy as np
import cv2
import traceback
import signal
from lib.imageEnhancer import ImageEnhancer
from lib.imageSegmenter import ImageSegmenter
from lib.BlobDetector import BlobDetector
from lib.objectSignals import ObjectSignals
from PySide2.QtCore import QThread, Slot


class ImageProcessor(QThread):
    '''
    Worker thread

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self):
        super().__init__()

        self.name = 'image processor'
        self.image = None
        self.signals = signal.signalClass()
        self.isStopped = False
        self.enhancer = ImageEnhancer()
        self.segmenter = ImageSegmenter(plot=True)
        self.detector = BlobDetector(plot=False)
        self.gridDetection = False
       
        
    def __del__(self):
        None
        self.wait()

    ## @brief ImageProcessor::msg(self, message) emits the message signal. This emit will be catched by the logging slot function in main.py.
    ## @param message is the string message to be emitted.
    def msg(self, message):
        if message is not None:
            self.signals.mes.emit(self.__class__.__name__ + ": " + str(message))
        return

    @Slot(np.ndarray)
    # Note that we need this wrapper around the Thread run function, since the latter will not accept any parameters
    def update(self, image=None):
        try:
            
            if self.isRunning():
                # thread is already running
                # drop frame
                self.msg('I: {} busy, frame dropped'.format(self.name))
            elif image is not None:
                # we have a new image
                self.image = image #.copy()        
                self.start()
                
        except Exception as err:
            traceback.print_exc()
            self.msg((type(err), err.args, traceback.format_exc()))
            self.signals.error.emit((type(err), err.args, traceback.format_exc()))

       
    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        if not self.isStopped and self.image is not None:
            self.msg('I: Running worker "{}"\n'.format(self.name))
           
            # Retrieve args/kwargs here; and fire processing using them
            try:
                # Enhance image
                self.image = self.enhancer.start(self.image)
                
                # Segment image according to grid 
                if self.gridDetection:
                    self.image = self.segmenter.start(self.image)
                    ROIs = self.segmenter.ROIs
                else:
                    ROIs = [[int(self.image.shape[1]/4), int(self.image.shape[0]/4),
                             int(self.image.shape[1]/2), int(self.image.shape[0]/2)]]

                # Blob detection
                result = self.detector.start(self.image, ROIs)

            except Exception as err:
                traceback.print_exc()
                self.signals.error.emit((type(err), err.args, traceback.format_exc()))
            else:
                self.signals.resultBlobs.emit(result,self.detector.blobs)
                self.signals.result.emit(result)  # Return the result of the processing
            finally:
                self.signals.finished.emit()  # Done
                
    @Slot()
    def stop(self):
        if self.isRunning():
            self.msg('I: Stopping worker "{}"\n'.format(self.name))
            self.isStopped = True
            self.quit()

    @Slot(bool)
    def setDetector(self, val):
        self.gridDetection = val        


            

