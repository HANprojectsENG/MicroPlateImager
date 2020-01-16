## @package main.py
## @brief main.py instantiates a main window. It handles message signals for logging. It connects to the PrintHAT pseudo serial port (/tmp/printer). It connects (window widget) signals to their slots and finally it disconnects from the port at exit.

import os
import sys
import time
import motor_control.serial_printhat as serial_printhat
import motor_control.stepper as stepper
import numpy as np
import array
import ctypes
import lib.signal as signal

from PySide2.QtWidgets import QPlainTextEdit, QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QDialog, QLineEdit, QFileDialog, QComboBox, QSizePolicy, QDoubleSpinBox, QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QWidget
from PySide2.QtGui import QFont, QColor, QPalette, QImage, QPixmap
from PySide2.QtCore import QSettings, Signal, Slot, Qt, QThread

from lib.checkOS import *
from lib.imageProcessor import *
from lib.PiCam import PiVideoStream

current_milli_time = lambda: int(round(time.time() * 1000))

## @brief MainWindow(QDialog) instantiates a main window. It consists of a manual control groupbox in which the user can control the steppers of the plate reader manually. Furthermore a groupbox with batch control widgets is created. A groupbox with log window provides runtime debug information. A groupbox with a camerastream widget shows the snapshots created by the well.
## @param QDialog is used as the window is a user interactive GUI.
## @author Gert van Lagen
class MainWindow(QDialog):
    signals = signal.signalClass() # message signal
    settings = None
    settings_batch = None
    Well_Map = None
    Well_Targets = None

    ## @brief MainWindow::__init__ initializes the window with widgets, layouts and groupboxes.
    def __init__(self):
        super().__init__()

        ## Create QSettings variables in order to be able to access the initialisation parameters
        self.openBatchIniFile()
        self.openSettingsIniFile()

        ## Load wells to process in batch from batch settings initialisation file and calculate the coordinates
        self.wellInitialisation()
        self.Well_Scanner = Scanner()

        ## Overall gridlayout
        self.mainWindowLayout = QGridLayout()    

        ## @param mgb is a groupbox with manual control widgets
        mgb = self.createManualGroupBox()

        ## @param is a groupbox with batch process control widgets
        bgb = self.createBatchGroupBox()

        ## @param is a groupbox with log window
        lgb = self.createLogWindow()

        ## @param is a groupbox with video stream window
        vgb = self.Well_Scanner.createVideoWindow()#self.createVideoWindow()

        ## Fill mainWindowLayout with the just created groupboxes in the mainWindowLayout gridlayout
        self.mainWindowLayout.addWidget(bgb,0,0)
        self.mainWindowLayout.addWidget(mgb,1,0)
        self.mainWindowLayout.addWidget(vgb,0,1)
        self.mainWindowLayout.addWidget(lgb,1,1)

        self.setWindowTitle("WELL READER")
        
        #self.mainWindowLayout.setStyleSheet('background-color: #a9a9a9')
        
        self.backgroundPalette = QPalette()
        self.backgroundColor = QColor(50, 50, 50)
        self.backgroundPalette.setColor(QPalette.Background, self.backgroundColor)
        self.setPalette(self.backgroundPalette)

        self.setLayout(self.mainWindowLayout)
        self.resize(self.width(), self.height())

    ## @brief Mainwindow(QDialog)::msg(self, message) emits the message signal. This emit will be catched by the logging slot function in main.py.
    ## @param message is the string message to be emitted.
    def msg(self, message):
        if message is not None:
            self.signals.mes.emit(self.__class__.__name__ + ": " + str(message))
        return
    
    ## @brief MainWindow::LogWindowInsert(self, message) appends the message to the log window. This is a slot function called when a mesnal message is emitted from any class which uses the message signal. This Slot is connected which each class which uses this signal.
    # @param message is the message to be displayed.
    @Slot(str)
    def LogWindowInsert(self, message):
        self.log.appendPlainText(str(message) + "\n")
        return

    ## @brief MainWindow::wait_ms(self, milliseconds) is a delay function.
    ## @param milliseconds is the number of milliseconds to wait.
    def wait_ms(self, milliseconds):
        GeneralEventLoop = QEventLoop()
        QTimer.singleShot(milliseconds, GeneralEventLoop.exit)
        GeneralEventLoop.exec_()
        return

    ## @brief MainWindow::createBatchGroupBox(self) creates the groupbox and the widgets in it which are used for the batch control.
    # @return self.batchGroupBox. This is the groupbox containing the Batch process widgets.
    def createBatchGroupBox(self):
        self.processControlGridLayout = QGridLayout()        

        self.batchGroupBox = QGroupBox()
        self.batchGroupBox.setStyleSheet("color: #000000;")

        ## label of QGroupbox content
        self.gb_label = QLabel("Batch control")
        self.gb_label.setStyleSheet('QLabel {color: #ffffff; font-weight: bold}')
        self.gb_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.processControlGridLayout.addWidget(self.gb_label,0,0,1,3, Qt.AlignHCenter)  

        ## Button FIRMWARE_RESTART
        self.b_firmware_restart = QPushButton("FIRMWARE_RESTART")
        self.b_firmware_restart.setStyleSheet('QPushButton {background-color: #AAAAAA; border: none}')
        self.b_firmware_restart.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.processControlGridLayout.addWidget(self.b_firmware_restart,1,0,1,1)

        ## Button Read STM buffer
        self.b_stm_read = QPushButton("STM READ")
        self.b_stm_read.setStyleSheet('QPushButton {background-color: #AAAAAA; border: none}')
        self.b_stm_read.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.processControlGridLayout.addWidget(self.b_stm_read,1,1,1,1)

        ## Button START BATCH
        self.b_start_batch = QPushButton("START BATCH")
        self.b_start_batch.setStyleSheet('QPushButton {background-color: #AAAAAA; border: none}')
        self.b_start_batch.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.processControlGridLayout.addWidget(self.b_start_batch,2,0,1,2)

        ## Button STOP BATCH
        self.b_stop_batch = QPushButton("STOP BATCH")
        self.b_stop_batch.setStyleSheet('QPushButton {background-color: #AAAAAA; border: none}')
        self.b_stop_batch.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.processControlGridLayout.addWidget(self.b_stop_batch,3,0,1,2)

        ## Button Snapshot. 
        self.b_snapshot = QPushButton("Snapshot")
        self.b_snapshot.setStyleSheet('QPushButton {background-color: #AAAAAA; border: none}')
        self.b_snapshot.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.processControlGridLayout.addWidget(self.b_snapshot,4,0,1,2)

        ## Button Doxygen. Creates and opens Doxygen documentation
        self.b_doxygen = QPushButton("Doxygen")
        self.b_doxygen.setStyleSheet('QPushButton {background-color: #ffa500; border: none}')
        self.b_doxygen.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.processControlGridLayout.addWidget(self.b_doxygen,5,0,1,2)

        self.batchGroupBox.setLayout(self.processControlGridLayout)

        return self.batchGroupBox

    ## @brief MainWindow::createManualGroupBox(self) creates the groupbox and the widgets in it which are used for the manual motor control.
    # @return self.manualGroupBox. This is the groupbox containing the manual control process widgets.
    def createManualGroupBox(self):
        self.manualControlGridLayout = QGridLayout()   
        self.manualGroupBox = QGroupBox()
        self.manualGroupBox.setStyleSheet("color: #000000;")

        ## label of QGroupbox content
        self.gb_label = QLabel("Manual XY-control")
        self.gb_label.setStyleSheet('QLabel {color: #ffffff; font-weight: bold}')
        self.gb_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.gb_label,0,0,1,4, Qt.AlignHCenter)  

        ## Button HOME X
        self.b_home_x = QPushButton("HOME X0 Y0")
        self.b_home_x.setStyleSheet('QPushButton {background-color: #55afff; border: none}')
        self.b_home_x.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.b_home_x,1,0,1,4)

        ## Button GET_POSITION
        self.b_get_pos = QPushButton("GET_POSITION")
        self.b_get_pos.setStyleSheet('QPushButton {background-color: #55afff; border: none}')
        self.b_get_pos.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.b_get_pos,2,0,1,4)
        
        ## Row selection label
        self.x_label = QLabel("X")
        self.x_label.setStyleSheet('QLabel {color: #ffffff}')
        self.x_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.x_label,3,0,1,1)  

        ## X position input field
        self.x_pos = QLineEdit()
        self.x_pos.setStyleSheet('QLineEdit {background-color: #AAAAAA; color: #000000; border: none}')
        self.x_pos.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.x_pos.setText('0.00')
        self.x_pos.setFont(QFont("Arial",20))
        self.manualControlGridLayout.addWidget(self.x_pos,4,0)

        ## Row selection label
        self.y_label = QLabel("Y")
        self.y_label.setStyleSheet('QLabel {color: #ffffff}')
        self.y_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.y_label,3,1,1,1)  

        ## Y position input field
        self.y_pos = QLineEdit()
        self.y_pos.setStyleSheet('QLineEdit {background-color: #AAAAAA; color: #000000; border: none}')
        self.y_pos.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.y_pos.setText('0.00')
        self.y_pos.setFont(QFont("Arial",20))
        self.manualControlGridLayout.addWidget(self.y_pos,4,1)

        ## Button goto XY
        self.b_gotoXY = QPushButton("Goto XY")
        self.b_gotoXY.setStyleSheet('QPushButton {background-color: #00cc33; border: none}')
        self.b_gotoXY.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.b_gotoXY,5,0,1,2)

        ## Row selection label
        self.row_label = QLabel("Row")
        self.row_label.setStyleSheet('QLabel {color: #ffffff}')
        self.row_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.row_label,3,2,1,1)
        
        ## Row well combobox
        self.row_well_combo_box = QComboBox(self)
        self.row_well_combo_box.setStyleSheet('QComboBox {background-color: #AAAAAA; border: none}')
        self.row_well_combo_box.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.row_well_combo_box,4,2,1,1)

        self.row_well_combo_box.addItem(str(0) + " position")
        for row in range(0, self.Well_Map.shape[0]-1, 1):
            self.row_well_combo_box.addItem(chr(ord('A') + row))

        ## Column selection label
        self.column_label = QLabel("Column")
        self.column_label.setStyleSheet('QLabel {color: #ffffff}')
        self.column_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.column_label,3,3,1,1)
        
        ## Column well combobox
        self.column_well_combo_box = QComboBox(self)
        self.column_well_combo_box.setStyleSheet('QComboBox {background-color: #AAAAAA; border: none}')
        self.column_well_combo_box.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.column_well_combo_box,4,3,1,1)
        
        self.column_well_combo_box.addItem(str(0) + " position")
        for column in range(1, self.Well_Map.shape[1], 1):
            self.column_well_combo_box.addItem(str(column))
    
        ## Button Goto well
        self.b_goto_well = QPushButton("Goto well")
        self.b_goto_well.setStyleSheet('QPushButton {background-color: #00cc33; border: none}')
        self.b_goto_well.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.b_goto_well,5,2,1,2)

        ## Button TURN UP
        self.b_turn_up = QPushButton("^")
        self.b_turn_up.setStyleSheet('QPushButton {background-color: #00cc33; border: none}')
        self.b_turn_up.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.b_turn_up,6,0,1,4)

        ## Button TURN LEFT
        self.b_turn_left = QPushButton("<")
        self.b_turn_left.setStyleSheet('QPushButton {background-color: #00cc33; border: none}')
        self.b_turn_left.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.b_turn_left,7,0,1,2)

        ## Button TURN RIGHT
        self.b_turn_right = QPushButton(">")
        self.b_turn_right.setStyleSheet('QPushButton {background-color: #00cc33; border: none}')
        self.b_turn_right.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.b_turn_right,7,2,1,2)

        ## Button TURN DOWN
        self.b_turn_down = QPushButton("v")
        self.b_turn_down.setStyleSheet('QPushButton {background-color: #00cc33; border: none}')
        self.b_turn_down.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.manualControlGridLayout.addWidget(self.b_turn_down,8,0,1,4)

        ## Button Emergency break
        self.b_emergency_break = QPushButton("Emergency break")
        self.b_emergency_break.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.b_emergency_break.setStyleSheet('QPushButton {background-color: #cc0000; border: none}')
        self.manualControlGridLayout.addWidget(self.b_emergency_break,9,0,1,4)
        self.manualGroupBox.setLayout(self.manualControlGridLayout)
        
        return self.manualGroupBox
    
    ## @brief MainWindow::createLogWindow(self) creates the groupbox and the log widget in it which is used for displaying debug messages.
    # @return self.logGroupBox. This is the groupbox containing the Log window widgets.
    def createLogWindow(self):
        self.logGridLayout = QGridLayout()
        self.logGroupBox = QGroupBox()
        self.logGroupBox.setStyleSheet("color: #000000;")

        ## label of QGroupbox content
        self.gb_label = QLabel("Debug information")
        self.gb_label.setStyleSheet('QLabel {color: #ffffff; font-weight: bold}')
        self.gb_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.logGridLayout.addWidget(self.gb_label,0,0,1,1, Qt.AlignHCenter)  

        ## Logger screen widget (QPlainTextEdit)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background-color: #AAAAAA;")
        self.logGridLayout.addWidget(self.log,1,0,1,1)

        self.logGroupBox.setLayout(self.logGridLayout)

        return self.logGroupBox

    ## @brief MainWindow::wellInitialisation(self) declares and defines the wellpositions in millimeters of the specified targets using the batch initialisation file.
    def wellInitialisation(self):
        ## Declare well map
        self.Well_Map = np.empty(
            (int(self.settings_batch.value("Plate/rows")) + 1,
            int(self.settings_batch.value("Plate/columns")) + 1, 2),
            dtype=object
        )
        
        ## Position 00 on the wellplate derived from the calibration data
        self.Well_Map[0:][0:] = (
            (float(self.settings_batch.value("Plate/posColumn00"))),
            (float(self.settings_batch.value("Plate/posRow00")))
        )

        self.msg("Initialising well plate with " + str(self.Well_Map.shape[0]) + " rows and " + str(self.Well_Map.shape[1]) + " columns.")

        ## Fill Well_Map with well positions in mm based on the distances of batch.ini
        for row in range(1, self.Well_Map.shape[0], 1):
            for column in range(1, self.Well_Map.shape[1], 1):
                self.Well_Map[row][column] = (
                    (float(self.settings_batch.value("Plate/posColumn00")) + float(self.settings_batch.value("Plate/p1")) + ((column-1) * float(self.settings_batch.value("Plate/p2")))),
                    (float(self.settings_batch.value("Plate/posRow00")) + float(self.settings_batch.value("Plate/p3")) + ((row-1) * float(self.settings_batch.value("Plate/p4"))))
                )
                
        ## load the wells to process
        self.settings_batch.beginReadArray("Wells")
        Well_KeyList = self.settings_batch.childKeys()
        print("Found (" + str(len(Well_KeyList)) + "): " + str(Well_KeyList))
        
        self.Well_Targets = np.empty((len(Well_KeyList), 1),
        dtype = [('X', 'i2'), ('Y', 'i2'), ('POS', 'U3'), ('Description', 'U100')])
        self.settings_batch.endArray()
        index = 0
        for Well_Key in Well_KeyList:
            Key_Characters = list(Well_Key)
            X_POS = (int(Key_Characters[1]) * 10) + (int(Key_Characters[2]))
            Y_POS = ord(Key_Characters[0].lower()) - 96
            self.Well_Targets[index] = (X_POS, Y_POS, str(Well_Key), str(self.settings_batch.value("Wells/"+Well_Key)))
            index = index+1
        print("Well targets: ")
        print(self.Well_Targets)
        return
    
    ## @brief MainWindow::openSettingsIniFile(self) opens the initialisation file with the technical settings of the device.
    def openSettingsIniFile(self):
        print("\nDEBUG: in function MainWindow::openSettingsIniFile()")
        self.settings = QSettings(os.path.dirname(os.path.realpath(__file__)) + "/system_config/settings.ini",  QSettings.IniFormat)
        self.msg("Opened settingsfile: " + os.path.dirname(os.path.realpath(__file__)) + "/system_config/settings.ini\n")
        return 

    ## @brief MainWindow::openBatchIniFile(self) opens the initialisation file with the batch process settings of the device and wells.
    def openBatchIniFile(self):
        print("\nDEBUG: in function MainWindow::openBatchIniFile()")
        self.settings_batch = QSettings(os.path.dirname(os.path.realpath(__file__)) + "/system_config/batch.ini",  QSettings.IniFormat)
        self.msg("Opened batch file: " + os.path.dirname(os.path.realpath(__file__)) + "/system_config/batch.ini\n")
        return 
    
    ## @brief mainWindow::doxygen(self) generates Doxygen documentation and opens a chromium-browser with the ./Documentation/html/index.html documentation website.
    def doxygen(self):
        os.system("cd Documentation && if [ -d ""html"" ]; then rm -r html; fi && cd ../ && doxygen Documentation/Doxyfile && chromium-browser ./Documentation/html/index.html")
        self.msg("Generated Doxygen documentation")
        return

    def closeEvent(self, event):
        self.signals.windowClosing.emit()
        event.accept()
        return

## @brief Scanner is the class which handles the image snapshot recording and processing and updates the video stream
## @author Robin Meekers
class Scanner():
    signals = signal.signalClass()
    preview = None ## @param preview contains the preview image
    capture = None ## @param capture contains the captured image
    captureRaw = None ## @param captureRaw contains the raw captured image
    previewRaw = None ## @param previewRaw contains the raw preview image
    DisplayTarget = None
    DisplayWell = None
    calibration_msg = str
    positioner_msg = str
    batchrun_msg = str

    ## @brief Scanner::__init__() initialises the variables and instances
    def __init__(self, parent=None):
        ## @param PixImage is the label on the MainWindow where the videostream is displayed
        self.PixImage = QLabel()
        return

    ## @brief MainWindow::createVideoGroupBox(self) creates the groupbox and the widgets in it which are used for displaying vido widgets.
    ## @return self.videoGroupBox. This the groupbox containing the snapshot visualisation widgets.
    ## @todo commenting
    def createVideoWindow(self):
        self.videoGridLayout = QGridLayout()
        self.videoGroupBox = QGroupBox()
        self.videoGroupBox.setStyleSheet("color: #000000;")

        ## label of QGroupbox content
        self.gb_label = QLabel("Video stream")
        self.gb_label.setStyleSheet('QLabel {color: #ffffff; font-weight: bold}')
        self.gb_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.videoGridLayout.addWidget(self.gb_label,0,0,1,1, Qt.AlignHCenter)

        ## PixImage is a QLabel widget used to display the snapshots
        self.videoGridLayout.addWidget(self.PixImage,1,0)

        self.videoGroupBox.setLayout(self.videoGridLayout)

        return self.videoGroupBox
    
    ## @brief Scanner()::msg(self, message) emits the message signal. This emit will be catched by the logging slot function in main.py.
    ## @param message is the string message to be emitted.
    def msg(self, message):
        if message is not None:
            self.signals.mes.emit(self.__class__.__name__ + ": " + str(message))
        return
    
    ## @brief Scanner::reader(self) takes snapshots
    @Slot()
    def reader(self):
        if not (self.capture is None):
            if not os.path.exists("snapshots"):
                self.msg("Generating snapshots directory")
                os.mkdir("snapshots")
            filename = 'snapshots/Reader_Snapshot' + str(current_milli_time()) + '.png'
            self.msg("Generated snapshot: " + str(filename))
            cv2.imwrite(filename, self.capture)
        return

    @Slot(str)
    def snapshotRequestedCalibrator(self, message):
        ## Set the info emitted by the calibrator.
        self.calibration_msg = str(message)
        ## Connect the capture ready signal to trigger the creation of a new frame.
        self.captureUpdated.connect(self.snapshotCalibrator)

    @Slot()
    def snapshotCalibrator(self):
        if not (self.capture is None):
            if not os.path.exists("snapshots_calibration"):
                os.mkdir("snapshots_calibration")
            filename = ' snapshots_calibration/HTSD_Snapshots_' + str(current_milli_time()) + "_" + str(self.callibration_msg) + '.png'
            print(filename)
            cv2.imwrite(filename, self.capture)
            # Disconnect the capture ready signal to only create snapshots when they are requested.
            self.signals.captureUpdated.disconnect(self.snapshot_calibrator)
            self.signals.signal_rdy_calibrator.emit()

    @Slot(str)
    def snapshotRequestedPositioner(self, message):
        ## Set the info emitted by the calibrator
        self.positioner_msg = str(message)
        ## Connect the capture ready signal to trigger the creation of a new frame.
        self.signals.previewUpdated.connect(self.snapshotPositioner)

    ## @todo check if self.preview or self.capture has to be emitted
    @Slot()
    def snapshotPositioner(self):
        if not (self.capture is None):
            ## Disconnect the capture ready signal to only create snapshots when they are requested.
            self.signals.previewUpdated.disconnect(self.snapshotPositioner)
            self.signals.signal_rdy_positioner.emit(self.preview)

    @Slot(str)
    def snapshotRequestedBatchRun(self, message):
        ## Set the info emitted by the calibrator.
        self.batchrun_msg = str(message)
        ## Connect the capture ready signal to trigger the creation of a new frame.
        self.captureUpdated.connect(self.snapshot_BatchRun)

    @Slot()
    def snapshotBatchRun(self):
        if not (self.capture is None):
            self.signals.captureUpdated.disconnect(self.snapshotBatchRun)
            if not os.path.exists("snapshot_run"):
                os.mkdir("snapshot_run")
            if not os.path.exists("snapshot_run/" + self.batchrun_msg):
                os.makedirs("snapshot_run/" + self.batchrun_msg)
            filename = ' snapshot_run/' + self.batchrun_msg + '/HTSD_Snapshot_' + str(current_milli_time()) + '.png'
            print(filename)
            cv2.imwrite(filename, self.capture)
            self.signals.signal_rdy_batchrun.emit()

    ## @brief Scanner::prvUpdate(self, image=None) updates the preview image on the QLabel widget of the MainWindow
    ## @param image is the new image to show
    ## @todo check necessity  of raw update functions
    @Slot(np.ndarray)
    def prvUpdate(self, image=None):
        if not (image is None):
            self.preview = image
            if len(image.shape) < 3:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB) ## convert to color image
            if self.DisplayTarget is not None:
                cv2.circle(image, (self.DisplayTarget[0], self.DisplayTarget[1]), self.DisplayTarget[2], (0,255,0), 1)
            if self.DisplayWell is not None:
                cv2.circle(image, (self.DisplayWell[0], self.DisplayWell[1]), self.DisplayWell[2], (255,0,0), 1)
            height, width = image.shape[:2] ## get dimensions
            
            ## @note Creating QImage without ctypes causes memory leaks. This is a PySide bug
            ch = ctypes.c_char.from_buffer(image.data, 0)
            rcount = ctypes.c_long.from_address(id(ch)).value
            qImage = QImage(ch, width, height, width * 3, QImage.Format_RGB888) ## Convert from OpenCV to PixMap
            ctypes.c_long.from_address(id(ch)).value = rcount

            ## Update the preview
            self.PixImage.setPixmap(QPixmap(qImage))
            self.PixImage.show()
            self.signals.previewUpdated.emit()

    ## @brief Scanner::capUpdate(self, image=None) updates the image when a new one is available and emits a captureUpdated signal.
    ## @param image is the new captured image.
    @Slot(np.ndarray)
    def capUpdate(self, image=None):
        if not (image is None):
            self.capture = image
            self.signals.captureUpdated.emit()

    ## @brief Scanner::capRawUpdate(self, image=None) updates the image when a new one is available and emits a captureRawUpdated signal.
    ## @param image is the new captured raw image.
    @Slot(np.ndarray)
    def capRawUpdate(self, image=None):
        if not (image is None):
            self.captureRaw = image
            self.signals.captureRawUpdated.emit()

    ## @brief Scanner::prvRawUpdate(self, image=None) updates the  raw preview image when a new one is availabe and emits the imageUpdate signal
    ## @param image is the new raw image
    @Slot(np.ndarray)
    def prvRawUpdate(self, image=None):
        print("in function Well_reader prvRawUpdate(self, image=None)")
        if not (image is None):
            self.previewRaw = image
            self.signals.previewRawUpdated.emit()

    @Slot(tuple)
    def set_displaytarget(self, target_information):
        self.DisplayTarget = target_information
        return

    @Slot(tuple)
    def set_displaywell(self, target_information):
        self.DisplayWell = target_information
        return

################################ MAIN APPLICATION ################################
## @brief main application of the well plate reader system. Instantiates the MainWindow().
# It connects to the /tmp/printer pseudo serial link. Instantiates StepperControl class for the XY movement control and the StepperWellPositioning class for positioning the wells under the camera.
# After that it connects the (window and message) signals to their slots.
# At exit, it takes care of correct shutdown of the motors and disconnection of the /tmp/printer port and stopping the klipper service.
##################################################################################
if __name__ == '__main__':
    
    ## Instantiate MainWindow and app
    app = QApplication([])

    ## @param mwi is the MainWindow application.
    mwi = MainWindow()
    mwi.showMaximized()

    ## @param steppers is the XY stepper motor control object.
    steppers = stepper.StepperControl()
    
    ## connect STM message signal to readPort function
    steppers.PrintHAT_serial.signals.stm_data.connect(steppers.PrintHAT_serial.readPort)
    steppers.PrintHAT_serial.signals.confirmation.connect(steppers.setConfirms)

    ## Connect steppers to printhat virtual port (this links the klipper software too).
    steppers.PrintHAT_serial.connect("/tmp/printer")
    
    ## @param stepper_well_positioning is the positioning instance of the wells making use of the steppers control class.
    stepper_well_positioning = stepper.StepperWellPositioning(steppers, mwi.Well_Map)
    stepper_well_positioning.signals.first_move.connect(steppers.PrintHAT_serial.setFirstMove)
    steppers.signals.well_unknown.connect(stepper_well_positioning.reset_current_well)

    ## @param Cam_Capturestream records images from the pi camera
    Cam_Capturestream = PiVideoStream(resolution=(int(mwi.settings.value("Camera/width")), int(mwi.settings.value("Camera/height"))), monochrome=True, framerate=int(mwi.settings.value("Camera/framerate")), effect='blur', use_video_port=bool(mwi.settings.value("Camera/use_video_port")))
    
    ## @param Image_Processor processes the images recorded by the PiVideoStream instance 
    Image_Processor = ImageProcessor()

    ## Start threads
    Cam_Capturestream.start(QThread.HighPriority)
    Image_Processor.start(QThread.HighPriority)

    ## Connect image signals to designated functions
    Cam_Capturestream.signals.prvReady.connect(lambda: Image_Processor.update(Cam_Capturestream.PreviewFrame), type=Qt.BlockingQueuedConnection)
    Image_Processor.signals.result.connect(lambda: mwi.Well_Scanner.capUpdate(Image_Processor.image))
    Image_Processor.signals.result.connect(lambda: mwi.Well_Scanner.prvUpdate(Image_Processor.image))

    stepper_well_positioning.signals.target_located.connect(mwi.Well_Scanner.set_displaytarget)
    stepper_well_positioning.signals.well_located.connect(mwi.Well_Scanner.set_displaywell)

    stepper_well_positioning.signals.snapshot_requested.connect(mwi.Well_Scanner.snapshotRequestedPositioner)
    mwi.Well_Scanner.signals.signal_rdy_positioner.connect(stepper_well_positioning.snapshot_confirmed)

    ## Signal slot connections
    ## Messages
    mwi.signals.mes.connect(mwi.LogWindowInsert)
    steppers.PrintHAT_serial.signals.mes.connect(mwi.LogWindowInsert)
    steppers.signals.mes.connect(mwi.LogWindowInsert)
    stepper_well_positioning.signals.mes.connect(mwi.LogWindowInsert)
    mwi.Well_Scanner.signals.mes.connect(mwi.LogWindowInsert)
    Cam_Capturestream.signals.mes.connect(mwi.LogWindowInsert)

    ## Buttons
    mwi.b_firmware_restart.clicked.connect(steppers.firmwareRestart)
    mwi.b_stm_read.clicked.connect(steppers.PrintHAT_serial.readPort)
    #mwi.b_start_batch.clicked.connect(mwi.startBatch)
    #mwi.b_stop_batch.clicked.connect(mwi.stopBatch)
    mwi.b_snapshot.clicked.connect(lambda: mwi.Well_Scanner.reader())
    mwi.b_doxygen.clicked.connect(mwi.doxygen)
    mwi.b_home_x.clicked.connect(steppers.homeXY)
    mwi.b_get_pos.clicked.connect(steppers.getPositionFromSTM)
    mwi.b_turn_up.clicked.connect(steppers.turnUp)
    mwi.b_turn_left.clicked.connect(steppers.turnLeft)
    mwi.b_turn_right.clicked.connect(steppers.turnRight)
    mwi.b_turn_down.clicked.connect(steppers.turnDown)
    mwi.b_gotoXY.clicked.connect(lambda: steppers.gotoXY(mwi.x_pos.text(), mwi.y_pos.text()))
    mwi.b_emergency_break.clicked.connect(steppers.emergencyBreak)
    mwi.b_goto_well.clicked.connect(lambda: stepper_well_positioning.goto_well(mwi.Well_Map[mwi.row_well_combo_box.currentIndex()][1][1], mwi.Well_Map[1][mwi.column_well_combo_box.currentIndex()][0]))

    
    ret = app.exec_()

    # stops the motors and disconnects from pseudo serial link /tmp/printer at exit
    steppers.PrintHAT_serial.disconnect()
    
    sys.exit(ret)
