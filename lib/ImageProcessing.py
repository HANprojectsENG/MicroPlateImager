#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time, math, sys
import numpy as np
import matplotlib.pyplot as plt
from PySide2.QtCore import QObject, QThread, Signal, Slot
import cv2
## Digital image processing threads
class ImgEnhancer(QThread):
	## Logging message signal
	message = Signal(str)  # Message signal
	ready = Signal()
	name = "ImageEnhancer"
	image = None
	procMillis = 0	

	def __init__(self):
		super().__init__()
		self.cropRect = [0,0,0,0] # p1_y, p1_x, p2_y, p2_x
		self.rotAngle = 0.0
		self.gamma = 1.0				
		self.clahe = None

	@Slot(np.ndarray)
	# Note that we need this wrapper around the Thread run function, since the latter will not accept any parameters
	def imgUpdate(self, image=None): 
		try:
			self.startMillis = int(round(time.time() * 1000)) 
			if self.image is None:  # first image to receive
				self.cropRect[2:] = image.shape[0:2]  # set cropping rectangle
			if self.isRunning():  # thread is already running
				self.message.emit(self.name + ": busy, frame dropped.")  # drop frame
			elif image is not None:  # we have a new image
				self.image = image #.copy()
				self.start()
		except exception as err:
			self.message.emit(self.name + ": exception " + str(err))
			pass		
		
	def run(self):
		try:
			if self.image is not None:
				self.message.emit(self.name + ": started.")
				if len(self.image.shape) > 2:  # if color image
					self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)  # convert to gray scale image
				self.image = self.image[self.cropRect[0]:self.cropRect[2], self.cropRect[1]:self.cropRect[3]] # crop the image
				if abs(self.rotAngle) > 0.0:
					self.image = rotateImage(self.image, self.rotAngle)  # rotate
					deltaw = int(.5*np.round(np.arcsin(np.pi*np.abs(self.rotAngle)/180)*self.image.shape[0]))
					deltah = int(.5*np.round(np.arcsin(np.pi*np.abs(self.rotAngle)/180)*self.image.shape[1]))
					self.image = self.image[+deltah:-deltah, +deltaw:-deltaw]  # autocrop when rotated
				if self.clahe is not None:
					self.image = self.clahe.apply(self.image)  # Contrast Limited Adaptive Histogram Equalization.
				if self.gamma > 1.0:
					self.image = adjust_gamma(self.image, self.gamma)  # change gamma
##				self.image = cv2.equalizeHist(self.image)  # histogram equalization
				self.procMillis = int(round(time.time() * 1000)) - self.startMillis
				self.message.emit(self.name + ": processing delay = " + str(self.procMillis) + " ms")
				self.ready.emit()
		finally:
			return
	
	def close(self):
		self.exit(0)
		
	@Slot(float)
	def setRotateAngle(self, angle):
		if -5.0 <= angle <= 5.0:
			self.rotAngle = round(angle, 1)  # strange behaviour, and rounding seems required
		else:
			self.message.emit("Error in " + self.name)
			
	@Slot(float)
	def setGamma(self, val):
		if 0.0 <= val <= 10.0:
			self.gamma = val
		else:
			self.message.emit("Error in " + self.name)

	@Slot(float)
	def setClaheClipLimit(self, val):
		if val <= 0.0:
			self.clahe = None
		elif val <= 10.0:
			self.clahe = cv2.createCLAHE(clipLimit=val, tileGridSize=(8,8))  # Sets threshold for contrast limiting
		else:
			self.message.emit("Error in " + self.name)

	@Slot(int)
	def setCropXp1(self, val):
		if 0 < val < self.cropRect[3]:		
			self.cropRect[1] = val
		else:
			self.message.emit("Error in " + self.name)

	@Slot(int)
	def setCropXp2(self, val):
		if self.cropRect[1] < val < self.image.shape[1]:			
			self.cropRect[3] = val
		else:
			self.message.emit("Error in " + self.name)

	@Slot(int)
	def setCropYp1(self, val):
		if 0 < val < self.cropRect[2]:		
			self.cropRect[0] = val			
		else:
			self.message.emit("Error in " + self.name)

	@Slot(int)
	def setCropYp2(self, val):
		if self.cropRect[0] < val < self.image.shape[0]:
			self.cropRect[2] = val			
		else:
			self.message.emit("Error in " + self.name)
class ImgSegmenter(QObject):
	## Logging message signal
	message = Signal(str)  # Message signal
	ready = Signal()
	name = "ImageSegmenter"	
	ksize = 0 ## ksize - Median Blur aperture linear size; it must be odd and greater than 1, for example: 3, 5, 7 ...
	sizeFrac = 0.005 # Findgrid parameter as a fraction of the image size
	image = None
	ROIs = None
	
	def __init__(self, doPlot=False):
		super().__init__()
		self.doPlot = doPlot
		self.imgQuality = None
		self.procMillis = 0
		self.running = False
		if self.doPlot:
			self.fig, (self.ax1, self.ax2) = plt.subplots(2,1)
			self.graph1 = None
			self.graph2 = None
			self.ax1.grid(True)
			self.ax2.grid(True)
			plt.show(block=False)
		
	@Slot(np.ndarray)
	def start(self, image=None):
		try:
			if self.running:
				self.message.emit(self.name + ": Error, already running.")
			elif image is not None:
				self.message.emit(self.name + ": started.")
				self.startMillis = int(round(time.time() * 1000))
				self.image = image if self.ksize < 1 else cv2.medianBlur(image, self.ksize)  # blur the image, very slow
				# Find grid pattern along row and column averages
				row_av = cv2.reduce(self.image, 0, cv2.REDUCE_AVG, dtype=cv2.CV_32S).flatten('F')
				row_seg_list, row_mask, smooth_row_av = find1DGrid(row_av, int(self.sizeFrac*row_av.size))
				col_av = cv2.reduce(self.image, 1, cv2.REDUCE_AVG, dtype=cv2.CV_32S).flatten('F')
				col_seg_list, col_mask, smooth_col_av = find1DGrid(col_av, int(self.sizeFrac*col_av.size))
				# Compute metrics
				col_stuff = np.diff(smooth_col_av[~col_mask]) # slice masked areas
				col_stuff = col_stuff[25:-25]  # slice edge effects
				row_stuff = np.diff(smooth_row_av[~row_mask]) # slice masked areas
				row_stuff = row_stuff[25:-25]  # slice edge effects
				self.imgQuality = np.sqrt( np.var(col_stuff) # / col_stuff[np.abs(col_stuff) < .5].size
										   + np.var(row_stuff) ) # / row_stuff[np.abs(row_stuff) < .5].size )
				# Rationale behind quality metrics: parameterize edge histogram by variance to amplitude (0-bin) ratio 
				# Plot curves
				if self.doPlot:
					col_hist, bin_edges = np.histogram(col_stuff, bins=np.arange(-5,5,.1), density=True)
					# Draw grid lines
					self.ax1.clear()
					self.graph1 = self.ax1.plot(row_stuff)[0]  # (col_hist)[0]
					self.ax2.clear()
					self.graph2 = self.ax2.plot(col_stuff)[0]  # smooth_col_av)[0]
### This way of plotting is probably faster, but right now can't get it to work with clearing as well					
##					if (self.graph1 is None):
##						self.graph1 = self.ax1.plot(smooth_row_av)[0]
##						self.graph2 = self.ax2.plot(smooth_col_av)[0]
##					else: 
##						self.graph1.set_image(np.arange(smooth_row_av.shape[1]), smooth_row_av)
##						self.graph2.set_image(np.arange(smooth_col_av.shape[1]), smooth_col_av)
##					# Need both of these in order to rescale
##					self.ax1.relim()
##					self.ax1.autoscale_view()
##					self.ax2.relim()
##					self.ax2.autoscale_view()
					# We need to draw *and* flush
					self.fig.canvas.draw()
					self.fig.canvas.flush_events()
				# Create ROI list
				list_width = len(row_seg_list)
				list_length = len(col_seg_list)
				self.ROIs = np.zeros([list_width*list_length,4], dtype=np.uint16)
				ROI_area = 0
				for i, x in enumerate(row_seg_list):
					for j, y in enumerate(col_seg_list):
						self.ROIs[i+j*list_width] = [x[0],y[0],x[1],y[1]]
						cv2.rectangle(self.image, (x[0],y[0]), (x[0]+x[1],y[0]+y[1]), (0, 255, 0), 2)
						ROI_area += x[1]*y[1]
				self.imgQuality *= (ROI_area/np.prod(image.shape[0:2])) # Rationale: sharp edges result in ROI increase
### These deep copies are very inefficient, so omitted
##			# Mask the RoI and nonRoI areas
##				self.nonRoI = np.zeros(shape=self.RoI.shape, dtype=self.RoI.dtype)
##				self.nonRoI[:, ~row_mask] = self.RoI[:, ~row_mask] 
##				self.nonRoI[~col_mask, :] = self.RoI[~col_mask, :]
##			# Mask the grid, note that masking also acts as a trick to combine all border blobs
##				self.RoI[:, ~row_mask] = 0
##				self.RoI[~col_mask, :] = 0
##				self.RoIArea = cv2.countNonZero(self.RoI)
				self.procMillis = int(round(time.time() * 1000)) - self.startMillis
				self.message.emit(self.name + ": processing delay = " + str(self.procMillis) + " ms")
				self.running = False
				self.ready.emit()
		except exception as err:
			self.message.emit("Error in " + self.name)
class BlobDetector(QObject):
	## Logging message signal
	message = Signal(str)  # Message signal
	## Image signal as numpy array
	ready = Signal()
	name = "BlobDetector"
	minBlobArea = 30
	maxBlobArea = 5000
	invertBinary = True # adaptiveThresholdInvertBinary
	showProcStep = 0
	image = None
	blobData = None

	def __init__(self, doPlot=False):
		super().__init__()
		self.doPlot = doPlot
		self.image = None
		self.procMillis = 0
		self.running = False
		self.offset = 0  # adaptiveThresholdOffset
		self.blocksize = 3  # adaptiveThresholdBlocksize
		if self.doPlot:
			cv2.namedWindow(self.name)
			plt.show(block=False)
			
	@Slot(np.ndarray)
	def start(self, image=None, ROIs=None):
		try:
			if self.running:
				self.message.emit(self.name + ": Error. already running.")
			elif (image is not None) and (ROIs is not None):
				self.message.emit(self.name + ": started.")
				self.startMillis = int(round(time.time() * 1000))
				self.image = image
				for ind, ROI in enumerate(ROIs):  # np.nditer(ROIs, flags=['multi_index']):
##					print(str(ROI[0]) + ":"  + str(ROI[2]) + "," + str(ROI[1]) + ":"  + str(ROI[3]))
					ROI_image = self.image[ROI[1]:ROI[1]+ROI[3],ROI[0]:ROI[0]+ROI[2]]  # slice image, assuming ROI:(left,top,width,height)
					# Binarize and find blobs
					BWImage = cv2.adaptiveThreshold(
						ROI_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, self.invertBinary, self.blocksize, self.offset)
					# ConnectedComponentsWithStats output: number of labels, label matrix, stats(left,top,width,height), area
					blobFeatures = cv2.connectedComponentsWithStats(BWImage, 8, cv2.CV_32S)				
					# Get blob RoI and area, and filter blobFeatures
					blobFeatures = blobFeatures[2][1:]  # skipping background (label 0)
					# Filter by blob area
					blobFeatures = blobFeatures[np.where( (blobFeatures[:, 4] > self.minBlobArea) & (blobFeatures[:, 4] < self.maxBlobArea) )]
					# Mark blobs in image
					for blob in blobFeatures:
						tl = (blob[0], blob[1])
						br = (blob[0] + blob[2], blob[1] + blob[3])
						cv2.rectangle(ROI_image, tl, br, (0, 0, 0), 1)

# todo dit testen en afmaken


					
##					self.data = np.copy(tmpData[np.where(tmpData[:, 4] > self.minBlobArea)])
##					self.data = self.data[np.where(self.data[:, 4] < self.maxBlobArea)]
##				# # filter ratio of Area vs ROI, to remove border blobs
##				# for index, row in enumerate(self.data):
##				#	 if (row[2] * row[3]) / row[4] > 8:
##				#		 print(row)
##				#		 blobData = np.delete(blobData, (index), axis=0)
##				self.data = np.append(self.data, np.zeros(
##					(self.data.shape[0], 3), dtype=int), axis=1)  # add empty columns

				# Plot ROI
				if self.doPlot:
					cv2.imshow(self.name, BWImage)	
					

##
##				# Compute some metrics of individual blobs
##				for row in self.data:
##					tempImage = image[row[1]:row[1] + row[3], row[0]:row[0] + row[2]]
##					tempBW = BWImage[row[1]:row[1] + row[3], row[0]:row[0] + row[2]]
##					tempMask = tempBW > 0
##					im2, contours, hierarchy = cv2.findContours(
##						tempBW, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # assuming that there is one blob in an RoI, if not we need to fiddle with the label output matrix output[1]
##					row[5] = int(cv2.Laplacian(tempImage, cv2.CV_64F).var())  # local image quality
##					row[6] = len(contours[0])  # perimeter
##					row[7] = int(np.mean(tempImage[tempMask]))  # foreground mean intensity

				self.procMillis = int(round(time.time() * 1000)) - self.startMillis
				self.message.emit(self.name + ": processing delay = " + str(self.procMillis) + " ms")
				self.running = False				
				self.ready.emit()				
			
		except exception as err:
			self.message.emit("Error in " + self.name)

	@Slot(float)
	def setOffset(self, val):
		if -10.0 <= val <= 10.0:
			self.offset = val
		else:
			self.message.emit("Error in " + self.name)

	@Slot(int)
	def setBlockSize(self, val):
		if (3 <= val <= 21) and (val & 1) == 1:
			self.blocksize = val
		else:
			self.message.emit("Error in " + self.name)
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
		self.circle_maxRadius = int((self.img_height/2)) # maximum circle radius is one that covers the entire height.
		self.circle_minRadius = int((self.img_height/2) * 0.7) # minimum circle size covers 70% of img height
		self.circle_minDistance = int(self.img_height/480) # find as many circles as reasonably possible

	def evaluate(self, source, target=(0, 0)):
		""" Finds the position error by finding the well bottom centroid.
		Args:
			img: 2d grayscale image list
			target: target coordinates (topleft pixel is 0,0)
		Returns: offset tuple (x, y) position error
		# Find circle(s) using hough transform, and return the circle that is closest to the centre.
		# If no circle could be found decrease param2 and increase contrast,
		# though this might cause false negatives if it is too low.
		# When this still fails, use blob detection and attempt to find a circle like object.
		:param source:
		"""
		error = None
		best_match = None
		best_area = None
		best_radius = None
		img = source.copy()
		## First attempt to find the well using the hough circles method.
		## Hough circle is most accurate when the well is closest to the desired target.
		# Normalize and adjust contrast 'curve' using clahe.
		cv2.normalize(img, img, 0, 255, cv2.NORM_MINMAX)
		clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
		img = clahe.apply(img)
		circles = cv2.HoughCircles(image=img,
								   method=cv2.HOUGH_GRADIENT,
								   dp=1,
								   param1=40,
								   param2=80,
								   minDist=self.circle_minDistance,
								   minRadius=self.circle_minRadius,
								   maxRadius=self.circle_maxRadius
								   )
		if not circles is None:
			circles = np.round(circles[0, :]).astype("int")
			# loop over the (x, y) coordinates and radius of the circles
			# store the circle that has the largest radius
			best_radius = 0
			for (x, y, r) in circles:	
				target_error = np.subtract((x,y), target)
				if best_radius < r:
					best_match = target_error
					best_area = int(math.pi * r * r)
					best_radius = r
			error = (best_match, best_area, best_radius)
			#print("Found (hough): " + str(error) )
			return (error)
		## Couldnt find a circle using the hough circle method, the well is probably too far off target.
		## Try detecting a well by using blobs and contour detection, and calculating their
		## eccentricity.
		# Threshold the image to create solid objects.
		cv2.threshold(img, 200, 255, cv2.THRESH_OTSU, img)
		
		# Morph-close with a small kernel to close holes caused by objects within the well.
		kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(self.img_width / 128), int(self.img_height / 128)) )
		cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, img, (-1, -1), 2)

		# Morph-open with a larger kernel to remove 'random' blobs caused by light reflection/refraction.
		kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(self.img_width / 48), int(self.img_height / 48)) )
		cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel, img, (-1,-1), 2)

		## Find contours and select best matching blob by looking at the mean score for
		## roundness and eccentricity, where lower is better. Apply a threshold on found objects,
		## Must have a minimum to prevent false negatives and maximum area to prevent false positives.
		best_score = sys.maxsize
		_,contours,_ = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
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

		# Calculate centroid for best match blob
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

def adjust_gamma(image, gamma=1.0):
   invGamma = 1.0 / gamma
   table = np.array([((i / 255.0) ** invGamma) * 255
##   table = np.array([(  np.log(1.0 + i/255.0)*gamma) * 255  # log transform
	  for i in np.arange(0, 256)]).astype("uint8")

   return cv2.LUT(image, table)
def rotateImage(image, angle):
	if angle != 0:
		image_center = tuple(np.array(image.shape[1::-1]) / 2)
		rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0) ## no scaling
		result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
		return result
	else:
		return image
def moving_average(x, N=5):
	if N > 1 and (N & 1) == 1:
		x = np.pad(x, pad_width=(N // 2, N // 2),
				   mode='constant')  # Assuming N is odd
		cumsum = np.cumsum(np.insert(x, 0, 0))
		return (cumsum[N:] - cumsum[:-N]) / float(N)
	else:
		raise ValueError("Moving average size must be odd and greater than 1.")
def find1DGrid(data, N):	
	if N <= 1:
		raise ValueError('findGrid parameter <= 1')
	if (N & 1) != 1:  # enforce N to be odd
		N += 1
	gridSmoothKsize = N
	gridMinSegmentLength = 10*N	
	# high-pass filter, to suppress uneven illumination
	data = np.abs(data - moving_average(data, int(3*N)))
	data[:N] = 0 # cut off MA artifacts
	data[-N:] = 0 # cut off MA artifacts, why not -(N-1)/2?? ??
	smooth_data = moving_average(data, gridSmoothKsize)
	smooth_data = smooth_data - np.mean(smooth_data)
	mask_data = np.zeros(data.shape, dtype='bool')  # mask grid lines
	mask_data[np.where(smooth_data < 0)[0]] = True
	# Now filter mask_data based on segment length and suppress too short segments
	prev_x = False
	segmentLength = 0
	segmentList = []
	for index, x in enumerate(mask_data):
		if x:  # segment
			segmentLength += 1
		elif x != prev_x:  # falling edge
			if segmentLength < gridMinSegmentLength:  # suppress short segments
				mask_data[index - segmentLength: index] = False
				# print(diff(data[index - segmentLength:index]))
			else:
				segmentList.append((index - segmentLength, segmentLength))  # Save segment start and length
			segmentLength = 0  # reset counter
		prev_x = x
####	segmentList = np.array(segmentList)
####	# Rudimentary grid pattern recognition
####	# expected pattern: 2 groups of 2 segments (+/- 5%), where the largest is sqrt(2) larger than smallest
######	print(segmentList)
####	gridFound = False
####	if len(segmentList) >= 2 or len(segmentList) <= 10:  # Nr of segments should be reasonable
####		# try to separate short and long segments, knn wouldbe better
####		meanSegmentLength = np.mean(segmentList)
####		shortSegments = segmentList[np.where(segmentList < meanSegmentLength)]
####		longSegments = segmentList[np.where(segmentList > meanSegmentLength)]
####		nrOfSegmentsRatio = 0  # define a measure for nr of short vs nr long segments
####		if len(longSegments) > len(shortSegments):
####			nrOfSegmentsRatio = len(shortSegments) / len(longSegments)
####		elif len(shortSegments) > 0:
####			nrOfSegmentsRatio = len(longSegments) / len(shortSegments)
####
####		# nrOfSegmentsRatio = nrOfSegmentsRatio if nrOfSegmentsRatio <= 1.0 else 1 / nrOfSegmentsRatio
####		if nrOfSegmentsRatio > 0.5:  # nr of short and long segments should be approximaely equal
####			normSegmentLengthRatio = np.sqrt(2) * np.mean(shortSegments) / np.mean(longSegments)
####			if normSegmentLengthRatio >= .9 and normSegmentLengthRatio <= 1.1:
####				gridFound = True
####
	return segmentList, mask_data, smooth_data

   
