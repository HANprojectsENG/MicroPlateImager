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
import math
import sys
import os
import cv2
import traceback
import lib.signal as signal
from lib.imageEnhancer import ImageEnhancer
from lib.imageSegmenter import ImageSegmenter
from lib.BlobDetector import BlobDetector
from PySide2.QtCore import QThread, Slot, QEventLoop, QTimer


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
       
        
    #def __del__(self):
    #    None
    #    self.wait()

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
                self.image = image     
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

    ## @brief ImageProcessor::wait_ms(self, milliseconds) is a delay function.
    ## @param milliseconds is the number of milliseconds to wait.
    def wait_ms(self, milliseconds):
        GeneralEventLoop = QEventLoop()
        QTimer.singleShot(milliseconds, GeneralEventLoop.exit)
        GeneralEventLoop.exec_()
        return

    @Slot()
    def close(self):
        print("ImageProcessor closing thread check: " + str(QThread.currentThread()))
        self.stop()
        self.exit(0)
        return      

## @brief class WellPositionEvaluator evaluates the position of circles in the passed image relative to the target position.
## @author Robin Meekers
class WellPositionEvaluator(QThread):
    img_width = None
    img_height = None 
    circle_minRadius = None
    circle_maxRadius = None
    circle_minDistance = None

    def __init__(self, resolution):
        super().__init__()
        self.img_width, self.img_height = resolution
        # The radius' are just initial values and will be reset once the first circle was found at the home position.
        self.circle_maxRadius = int((self.img_height/2)) # maximum circle radius is one that covers the entire height
        self.circle_minRadius = int((self.img_height/2) * 0.7) # minimum circle size covers 70% of img height
        self.circle_minDistance = int(self.img_height/480) # find as many circles as reasonably possible

    ## @brief WellPositionEvaluator::evaluate(self, source, target=(0,0)) finds the position error by finding the well bottom centroid. 
    ## Find circle(s) using hough transform, and return the circle that is closest to the centre.
    ## If no circle could be found decrease param2 and increase contrast, though this might cause false negatives if it is too low.
    ## When this still fails, use blob detection and attempt to find a circle like object.
    ## @param source 2d grayscale image list
    ## @param target contains the target coordinates (topleft pixel is 0,0)
    ## @return offset tuple (x, y) position error
    def evaluate(self, source, target=(0, 0)):
        error = None
        best_match = None
        best_area = None
        best_radius = None
        img = source.copy()
        ## First attempt to find the well using the hough circles method.
        ## Hough circle is most accurate when the well is closest to the desired target.
        ## Normalize and adjust contrast 'curve' using clahe
        cv2.normalize(img, img, 0, 255, cv2.NORM_MINMAX)
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        img = clahe.apply(img)
        circles = cv2.HoughCircles(image=img, method=cv2.HOUGH_GRADIENT, dp=1, param1=40, param2=80, minDist=self.circle_minDistance, minRadius=self.circle_minRadius, maxRadius=self.circle_maxRadius)
        if not circles is None:
            circles = np.round(circles[0, :]).astype("int")
            ## loop over the (x, y) coordinates and radius of the circles
            ## store the circle that has the largest radius
            best_radius = 0
            for (x, y, r) in circles:
                target_error = np.subtract((x,y), target)
                if best_radius < r:
                    best_match = target_error
                    best_area = int(math.pi * r * r)
                    best_radius = r 
            error = (best_match, best_area, best_radius)
            #print("Found (hough): " + str(error))
            return error
        ## Couldnt find a circle using the hough circle method, the well is probably too far off target.
        ## Try detecting a well by using blobs and controur detection, and calculating their eccentricity.
        ## Threashold the image to create solid objects.
        cv2.threshold(img, 200, 255, cv2.THRESH_OTSU, img)

        # Morph-close with a small kernel to close holes caused by objects within the well.
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(self.img_width / 128), int(self.img_height / 128)))
        cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, img, (-1, -1), 2)

        ## Find contours and select best matching blob by looking at the mean score for rondness and eccentricity,
        ## where lower is better. Apply a threshold on found objects,
        ## Must have a minimum to prevent false negatives and maximum area to prevent false positives.
        best_score = sys.maxsize
        #_,contours,_ = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours,_ = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for i, c in enumerate(contours):
            area = cv2.contourArea(c)
            if area > int((self.img_width/3) * (self.img_height/3)):
                perimeter = cv2.arcLength(c, True)
                roundness = 4 * np.pi * area / perimeter ** 2
                m = cv2.moments(c)
                eccentricity = ((m['nu20'] - m['nu02']) ** 2 + 4 * m['nu11'] ** 2) / (m['nu20'] + m['nu02']) ** 2
                score = (1 - roundness + eccentricity) / 2
                if score < best_score:
                    best_score = score
                    best_match = c
                    best_area = int(area)
                    best_radius = int(math.sqrt(area/np.pi))

        if best_match is not None:
            M = cv2.moments(best_match)
            cX = int(M["m10"] / M["m00"] + 0.5)
            cY = int(M["m01"] / M["m00"] + 0.5)
            centroid = (cX, cY)
            best_match = np.subtract(centroid, target)
            error = (best_match, best_area, best_radius)
            return (error)
        else:
            return 0, 0, -1, -1

    ## @brief WellPositionEvaluator::wait_ms(self, milliseconds) is a delay function.
    ## @param milliseconds is the number of milliseconds to wait.
    def wait_ms(self, milliseconds):
        GeneralEventLoop = QEventLoop()
        QTimer.singleShot(milliseconds, GeneralEventLoop.exit)
        GeneralEventLoop.exec_()
        return

    @Slot()
    def stop(self):
        if self.isRunning():
            self.msg('I: Stopping worker "{}"\n'.format(self.name))
            self.quit()

    @Slot()
    def close(self):
        print("WellPositionEvaluator::close thread check: " + str(QThread.currentThread()))
        self.stop()
        self.exit(0)
        return
