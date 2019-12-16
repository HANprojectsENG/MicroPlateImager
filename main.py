## @package main.py
# @brief main.py instantiates a main window. It handles message signals for logging. It connects to the PrintHAT pseudo serial port (/tmp/printer). It connects (window widget) signals to their slots and finally it disconnects from the port at exit.

import os
import sys
import time
import serial_printhat
import stepper

from PySide2.QtWidgets import QPlainTextEdit, QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QDialog, QLineEdit, QFileDialog
from PySide2.QtGui import QFont
from PySide2.QtCore import QSettings, Signal, Slot

## @brief MainWindow(QDialog) instantiates a main window. It consists of a manual control groupbox in which the user can control the steppers of the plate reader manually. Furthermore a groupbox with batch control widgets is created. A groupbox with log window provides runtime debug information. A groupbox with a camerastream widget shows the snapshots created by the well.
# @param QDialog is used as the window is a user interactive GUI.
# @todo Creation of signal messages for the log window.
# @todo Creation of the snapshot stream.
class MainWindow(QDialog):
    message = Signal(str) # message signal

    ## @param Create serial instance used for writing G-code.
    # @todo Check if PrintHAT_serial can be declared in the main application.
    #PrintHAT_serial = serial_printhat.GcodeSerial()

    settings = None
    settings_batch = None

    ## @brief MainWindow::__init__ initializes the window with widgets, layouts and groupboxes.
    def __init__(self):
        super().__init__()
        
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

    ## @brief MainWindow::createBatchGroupBox(self) creates the groupbox and the widgets in it which are used for the batch control.
    # @return self.batchGroupBox. This is the groupbox containing the Batch process widgets.
    def createBatchGroupBox(self):
        self.processControlGridLayout = QGridLayout()        

        self.batchGroupBox = QGroupBox("Batch control")
        self.batchGroupBox.setStyleSheet("color: #000000;")

        ## Button FIRMWARE_RESTART
        self.b_firmware_restart = QPushButton("FIRMWARE_RESTART")
        self.processControlGridLayout.addWidget(self.b_firmware_restart,0,0)

        ## Button START BATCH
        self.b_start_batch = QPushButton("START BATCH")
        self.processControlGridLayout.addWidget(self.b_start_batch,1,0)

        ## Button STOP BATCH
        self.b_stop_batch = QPushButton("STOP BATCH")
        self.processControlGridLayout.addWidget(self.b_stop_batch,2,0)
    
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
        self.log.appendPlainText("Opened settingsfile: " + os.path.dirname(os.path.realpath(__file__)) + "/settings.ini\n")
        return 

    ## @brief MainWindow::openBatchIniFile(self) opens the initialisation file with the batch process settings of the device and wells.
    def openBatchIniFile(self):
        print("\nDEBUG: in function MainWindow::openBatchIniFile()")
        self.settings_batch = QSettings(os.path.dirname(os.path.realpath(__file__)) + "/batch.ini",  QSettings.IniFormat)
        self.log.appendPlainText("Opened batch file: " + os.path.dirname(os.path.realpath(__file__)) + "/batch.ini\n")
        return 
    
################################ MAIN APPLICATION ################################
## @brief main application of the well plate reader system. Instantiates the MainWindow().
# It connects to the /tmp/printer pseudo serial link. Instantiates the X and Y StepperControl classes and the StepperWellp[ositioning class.
# After that it connects the (window and message) signals to their slots.
# At exit, it takes care of correct shutdown of the motors and disconnection of the /tmp/printer port.
if __name__ == '__main__':
    ## Instantiate MainWindow and app
    app = QApplication([])
    ## @param mwi is the MainWindow application.
    mwi = MainWindow()
    mwi.show()

    ## @param stepper_X is the X-axis stepper motor.
    steppers = stepper.StepperControl()
    
    ## Connect steppers to printhat virtual port (this links the klipper software also).
    steppers.PrintHAT_serial.connect("/tmp/printer")

    ## @param stepper_Y is the Y-axis stepper motor.
    #stepper_Y = stepper.StepperControl()
    
    ## @param stepper_well_positioning is the positioning instance of the wells.
    stepper_well_positioning = stepper.StepperWellpositioning(steppers)
    
    ## Signal slot connections
    mwi.b_firmware_restart.clicked.connect(steppers.firmwareRestart)

    #mwi.b_start_batch.clicked.connect(mwi.startBatch)
    #mwi.b_stop_batch.clicked.connect(mwi.stopBatch)
    
    mwi.b_home_x.clicked.connect(steppers.homeXY)
    mwi.b_turn_up.clicked.connect(steppers.turnUp)
    mwi.b_turn_left.clicked.connect(steppers.turnLeft)
    mwi.b_turn_right.clicked.connect(steppers.turnRight)
    mwi.b_turn_down.clicked.connect(steppers.turnDown)
    mwi.b_gotoXY.clicked.connect(lambda: steppers.gotoXY(mwi.x_pos.text(), mwi.y_pos.text()))
    mwi.b_emergency_break.clicked.connect(steppers.emergencyBreak)
    mwi.message.connect(mwi.LogWindowInsert)
    mwi.message.emit("creating batchgroupbox")
    #steppers.message.connect(mwi.LogWindowInsert)
    stepper_well_positioning.message.sig.connect(mwi.LogWindowInsert)

    ret = app.exec_()
    # stops the motors and disconnects from pseudo serial link /tmp/printer at exit
    steppers.PrintHAT_serial.disconnect()
    sys.exit(ret)
