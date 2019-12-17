## @package main.py
## @brief main.py instantiates a main window. It handles message signals for logging. It connects to the PrintHAT pseudo serial port (/tmp/printer). It connects (window widget) signals to their slots and finally it disconnects from the port at exit.

import os
import sys
import time
import serial_printhat
import stepper
import signal
import numpy as np
import array
from PySide2.QtWidgets import QPlainTextEdit, QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QDialog, QLineEdit, QFileDialog, QComboBox
from PySide2.QtGui import QFont
from PySide2.QtCore import QSettings, Signal, Slot

## @brief MainWindow(QDialog) instantiates a main window. It consists of a manual control groupbox in which the user can control the steppers of the plate reader manually. Furthermore a groupbox with batch control widgets is created. A groupbox with log window provides runtime debug information. A groupbox with a camerastream widget shows the snapshots created by the well.
## @param QDialog is used as the window is a user interactive GUI.
## @todo Creation of signal messages for the log window.
## @todo Creation of the snapshot stream.
class MainWindow(QDialog):
    message = signal.signalClass() # message signal

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

        ## Overall gridlayout
        self.mainWindowLayout = QGridLayout()    

        ## @param mgb is a groupbox with manual control widgets
        mgb = self.createManualGroupBox()

        ## @param is a groupbox with batch process control widgets
        bgb = self.createBatchGroupBox()

        ## @param is a groupbox with log window
        lgb = self.createLogWindow()

        ## @param is a groupbox with video stream window
        vgb = self.createVideoWindow()

        ## Fill mainWindowLayout with the just created groupboxes in the mainWindowLayout gridlayout
        self.mainWindowLayout.addWidget(bgb,0,0)
        self.mainWindowLayout.addWidget(mgb,1,0)
        self.mainWindowLayout.addWidget(vgb,0,1)
        self.mainWindowLayout.addWidget(lgb,1,1)

        self.setWindowTitle("PrintHAT")
        self.setLayout(self.mainWindowLayout)
        self.resize(self.width(), self.height())

    ## @brief Mainwindow(QDialog)::msg(self, message) emits the message signal. This emit will be catched by the logging slot function in main.py.
    ## @param message is the string message to be emitted.
    def msg(self, message):
        if message is not None:
            self.message.sig.emit(self.__class__.__name__ + ": " + str(message))
        return
    
    ## @brief MainWindow::createBatchGroupBox(self) creates the groupbox and the widgets in it which are used for the batch control.
    # @return self.batchGroupBox. This is the groupbox containing the Batch process widgets.
    def createBatchGroupBox(self):
        self.processControlGridLayout = QGridLayout()        

        self.batchGroupBox = QGroupBox("Batch control")
        self.batchGroupBox.setStyleSheet("color: #000000;")

        ## Button FIRMWARE_RESTART
        self.b_firmware_restart = QPushButton("FIRMWARE_RESTART")
        self.processControlGridLayout.addWidget(self.b_firmware_restart,0,0,1,2)

        ## Button START BATCH
        self.b_start_batch = QPushButton("START BATCH")
        self.processControlGridLayout.addWidget(self.b_start_batch,1,0,1,2)

        ## Button STOP BATCH
        self.b_stop_batch = QPushButton("STOP BATCH")
        self.processControlGridLayout.addWidget(self.b_stop_batch,2,0,1,2)

        ## Row selection label
        self.row_label = QLabel("Row")
        self.processControlGridLayout.addWidget(self.row_label,3,0,1,1)
        
        ## Row well combobox
        self.row_well_combo_box = QComboBox(self)
        self.processControlGridLayout.addWidget(self.row_well_combo_box,4,0,1,1)

        self.row_well_combo_box.addItem(str(0) + " position")
        for row in range(0, self.Well_Map.shape[1]-1, 1):
            self.row_well_combo_box.addItem(chr(ord('A') + row))

        ## Column selection label
        self.column_label = QLabel("Column")
        self.processControlGridLayout.addWidget(self.column_label,3,1,1,1)
        
        ## Column well combobox
        self.column_well_combo_box = QComboBox(self)
        self.processControlGridLayout.addWidget(self.column_well_combo_box,4,1,1,1)
        
        self.column_well_combo_box.addItem(str(0) + " position")
        for column in range(1, self.Well_Map.shape[0]-1, 1):
            self.column_well_combo_box.addItem(str(column))
    
        self.b_goto_well = QPushButton("Goto well")
        self.processControlGridLayout.addWidget(self.b_goto_well,5,0,1,2)

        ## Button Doxygen. Creates and opens Doxygen documentation
        self.b_doxygen = QPushButton("Doxygen")
        self.processControlGridLayout.addWidget(self.b_doxygen,6,0,1,2)

        self.batchGroupBox.setLayout(self.processControlGridLayout)

        return self.batchGroupBox

    ## @brief MainWindow::createManualGroupBox(self) creates the groupbox and the widgets in it which are used for the manual motor control.
    # @return self.manualGroupBox. This is the groupbox containing the manual control process widgets.
    def createManualGroupBox(self):
        self.manualControlGridLayout = QGridLayout()   
        self.manualGroupBox = QGroupBox("Manual XY-control")
        self.manualGroupBox.setStyleSheet("color: #000000;")

        ## Button HOME X
        self.b_home_x = QPushButton("HOME X0 Y0")
        self.manualControlGridLayout.addWidget(self.b_home_x,0,0,1,2)

        ## Button GET_POSITION
        self.b_get_pos = QPushButton("GET_POSITION")
        self.manualControlGridLayout.addWidget(self.b_get_pos,1,0,1,2)
        
        ## Button TURN UP
        self.b_turn_up = QPushButton("^")
        self.manualControlGridLayout.addWidget(self.b_turn_up,2,0,1,2)

        ## Button TURN LEFT
        self.b_turn_left = QPushButton("<")
        self.manualControlGridLayout.addWidget(self.b_turn_left,3,0,1,1)

        ## Button TURN RIGHT
        self.b_turn_right = QPushButton(">")
        self.manualControlGridLayout.addWidget(self.b_turn_right,3,1,1,1)

        ## Button TURN DOWN
        self.b_turn_down = QPushButton("v")
        self.manualControlGridLayout.addWidget(self.b_turn_down,4,0,1,2)

        ## X position input field
        self.x_pos = QLineEdit()
        self.x_pos.setText('0.00')
        self.x_pos.setFont(QFont("Arial",20))
        self.manualControlGridLayout.addWidget(self.x_pos,5,0)

        ## Y position input field
        self.y_pos = QLineEdit()
        self.y_pos.setText('0.00')
        self.y_pos.setFont(QFont("Arial",20))
        self.manualControlGridLayout.addWidget(self.y_pos,5,1)

        ## Button goto X
        self.b_gotoXY = QPushButton("Goto XY")
        self.manualControlGridLayout.addWidget(self.b_gotoXY,6,0,1,2)

        ## Button Emergency break
        self.b_emergency_break = QPushButton("Emergency break")
        self.manualControlGridLayout.addWidget(self.b_emergency_break,7,0,1,2)
        
        self.manualGroupBox.setLayout(self.manualControlGridLayout)
        
        return self.manualGroupBox
    
    ## @brief MainWindow::createLogWindow(self) creates the groupbox and the log widget in it which is used for displaying debug messages.
    # @return self.logGroupBox. This is the groupbox containing the Log window widgets.
    def createLogWindow(self):
        self.logGridLayout = QGridLayout()
        self.logGroupBox = QGroupBox("Logger")
        self.logGroupBox.setStyleSheet("color: #000000;")

        ## Logger screen widget (QPlainTextEdit)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background-color: #AAAAAA;")
        self.logGridLayout.addWidget(self.log,0,0)

        self.logGroupBox.setLayout(self.logGridLayout)

        return self.logGroupBox

    ## @brief MainWindow::createVideoGroupBox(self) creates the groupbox and the widgets in it which are used for displaying vido widgets.
    # @return self.videoGroupBox. This the groupbox containing the snapshot visualisation widgets.
    def createVideoWindow(self):
        self.videoGridLayout = QGridLayout()
        self.videoGroupBox = QGroupBox("Video stream")
        self.videoGroupBox.setStyleSheet("color: #000000;")

        ## videoStream is a widget to display the snapshots
        self.videoStream = QPlainTextEdit()
        self.videoStream.setReadOnly(True)
        self.videoStream.setStyleSheet("background-color: #AAAAAA;")
        self.videoGridLayout.addWidget(self.videoStream,0,0)

        self.videoStream.appendPlainText("This will become a video stream widget.")

        self.videoGroupBox.setLayout(self.videoGridLayout)

        return self.videoGroupBox
    
    ## @brief MainWindow::wellInitialisation(self) declares and defines the wellpositions in millimeters of the specified targets using the batch initialisation file.
    def wellInitialisation(self):
        ## Declare and define wellpositions in millimeters
        self.Well_Map = np.empty(
            (int(self.settings_batch.value("Plate/columns")) + 1,
            int(self.settings_batch.value("Plate/rows")) + 1, 2),
            dtype=object
        )

        ## Position 00 on the wellplate derived from the calibration data
        self.Well_Map[0:][0:] = (
            (float(self.settings_batch.value("Plate/posxA1"))),
            (float(self.settings_batch.value("Plate/posyA1")))
        )

        self.msg("Initialising well plate with " + str(self.Well_Map.shape[1]) + " rows and " + str(self.Well_Map.shape[0]) + " columns.")

        for row in range(1, self.Well_Map.shape[1], 1):
            for column in range(1, self.Well_Map.shape[0], 1):
                self.Well_Map[column][row] = (
                    float(self.settings_batch.value("Plate/posxA1")) + ((column-1) * float(self.settings_batch.value("Plate/deltaxWell"))),
                    float(self.settings_batch.value("Plate/posyA1")) + ((row-1) * float(self.settings_batch.value("Plate/deltayWell")))
                )
                print(self.Well_Map[column][row])

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
    
    ## @brief MainWindow::LogWindowInsert(self, message) appends the message to the log window. This is a slot function called when a signal message is emitted from any class which uses the message signal. This Slot is connected which each class which uses this signal.
    # @param message is the message to be displayed.
    @Slot(str)
    def LogWindowInsert(self, message):
        self.log.appendPlainText("it works: " +str(message) + "\n")
        return

    
    ## @brief MainWindow::openSettingsIniFile(self) opens the initialisation file with the technical settings of the device.
    def openSettingsIniFile(self):
        print("\nDEBUG: in function MainWindow::openSettingsIniFile()")
        self.settings = QSettings(os.path.dirname(os.path.realpath(__file__)) + "/settings.ini",  QSettings.IniFormat)
        self.msg("Opened settingsfile: " + os.path.dirname(os.path.realpath(__file__)) + "/settings.ini\n")
        return 

    ## @brief MainWindow::openBatchIniFile(self) opens the initialisation file with the batch process settings of the device and wells.
    def openBatchIniFile(self):
        print("\nDEBUG: in function MainWindow::openBatchIniFile()")
        self.settings_batch = QSettings(os.path.dirname(os.path.realpath(__file__)) + "/batch.ini",  QSettings.IniFormat)
        self.msg("Opened batch file: " + os.path.dirname(os.path.realpath(__file__)) + "/batch.ini\n")
        return 
    
    def doxygen(self):
        os.system("cd Documentation && if [ -d ""html"" ]; then rm -r html; fi && cd ../ && doxygen Documentation/Doxyfile && chromium-browser ./Documentation/html/index.html")
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
    mwi.show()

    ## @param steppers is the XY stepper motor control object.
    steppers = stepper.StepperControl()
    
    ## Connect steppers to printhat virtual port (this links the klipper software too).
    steppers.PrintHAT_serial.connect("/tmp/printer")
    
    ## @param stepper_well_positioning is the positioning instance of the wells making use of the steppers control class.
    stepper_well_positioning = stepper.StepperWellPositioning(steppers)
    
    ## Signal slot connections
    mwi.b_firmware_restart.clicked.connect(steppers.firmwareRestart)
    #mwi.b_start_batch.clicked.connect(mwi.startBatch)
    #mwi.b_stop_batch.clicked.connect(mwi.stopBatch)
    mwi.b_doxygen.clicked.connect(mwi.doxygen)
    mwi.b_home_x.clicked.connect(steppers.homeXY)
    mwi.b_turn_up.clicked.connect(steppers.turnUp)
    mwi.b_turn_left.clicked.connect(steppers.turnLeft)
    mwi.b_turn_right.clicked.connect(steppers.turnRight)
    mwi.b_turn_down.clicked.connect(steppers.turnDown)
    mwi.b_gotoXY.clicked.connect(lambda: steppers.gotoXY(mwi.x_pos.text(), mwi.y_pos.text()))
    mwi.b_emergency_break.clicked.connect(steppers.emergencyBreak)
    
    mwi.message.sig.connect(mwi.LogWindowInsert)
    steppers.PrintHAT_serial.message.sig.connect(mwi.LogWindowInsert)
    steppers.message.sig.connect(mwi.LogWindowInsert)
    stepper_well_positioning.message.sig.connect(mwi.LogWindowInsert)

    ret = app.exec_()

    # stops the motors and disconnects from pseudo serial link /tmp/printer at exit
    steppers.PrintHAT_serial.disconnect()
    
    sys.exit(ret)
