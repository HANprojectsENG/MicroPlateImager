import os
import sys
import time
import serial_printhat
import stepper

from PySide2.QtWidgets import QPlainTextEdit, QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QDialog, QLineEdit, QFileDialog
from PySide2.QtGui import QFont
from PySide2.QtCore import QSettings, Signal, Slot

class MainWindow(QDialog):

    message = Signal(str) # message signal

    # create serial instance used for writing G-code
    PrintHAT_serial = serial_printhat.GcodeSerial()

    settings = None
    settings_batch = None

    def __init__(self):
        super().__init__()
        
        self.mainWindowLayout = QGridLayout()    
           
        # groupbox with manual control widgets
        mgb = self.createManualGroupBox()

        # groupbox with batch process control widgets
        bgb = self.createBatchGroupBox()
        
        # groupbox with log window
        lgb = self.createLogWindow()

        # groupbox with video stream window
        vgb = self.createVideoWindow()

        # fill mainWindowLayout
        self.mainWindowLayout.addWidget(bgb,0,0)
        self.mainWindowLayout.addWidget(mgb,1,0)
        self.mainWindowLayout.addWidget(vgb,0,1)
        self.mainWindowLayout.addWidget(lgb,1,1)

        self.setWindowTitle("PrintHAT")
        self.setLayout(self.mainWindowLayout)
        self.resize(self.width(), self.height())

    def createBatchGroupBox(self):
        self.processControlGridLayout = QGridLayout()        

        self.batchGroupBox = QGroupBox("Batch control")
        self.batchGroupBox.setStyleSheet("color: #000000;")

        # button FIRMWARE_RESTART
        self.b_firmware_restart = QPushButton("FIRMWARE_RESTART")
        self.processControlGridLayout.addWidget(self.b_firmware_restart,0,0)

        # button START BATCH
        self.b_start_batch = QPushButton("START BATCH")
        self.processControlGridLayout.addWidget(self.b_start_batch,1,0)

        # button STOP BATCH
        self.b_stop_batch = QPushButton("STOP BATCH")
        self.processControlGridLayout.addWidget(self.b_stop_batch,2,0)
    
        self.batchGroupBox.setLayout(self.processControlGridLayout)

        return self.batchGroupBox

    def createManualGroupBox(self):
        self.manualControlGridLayout = QGridLayout()   
        self.manualGroupBox = QGroupBox("Manual XY-control")
        self.manualGroupBox.setStyleSheet("color: #000000;")

        # button HOME X
        self.b_home_x = QPushButton("HOME X0 Y0")
        self.manualControlGridLayout.addWidget(self.b_home_x,0,0,1,2)

        # button GET_POSITION
        self.b_get_pos = QPushButton("GET_POSITION")
        self.manualControlGridLayout.addWidget(self.b_get_pos,1,0,1,2)
        
        # button TURN UP
        self.b_turn_up = QPushButton("^")
        self.manualControlGridLayout.addWidget(self.b_turn_up,2,0,1,2)

        # button TURN LEFT
        self.b_turn_left = QPushButton("<")
        self.manualControlGridLayout.addWidget(self.b_turn_left,3,0,1,1)

        # button TURN RIGHT
        self.b_turn_right = QPushButton(">")
        self.manualControlGridLayout.addWidget(self.b_turn_right,3,1,1,1)

        # button TURN DOWN
        self.b_turn_down = QPushButton("v")
        self.manualControlGridLayout.addWidget(self.b_turn_down,4,0,1,2)

        # X position input field
        self.x_pos = QLineEdit()
        self.x_pos.setText('0.00')
        self.x_pos.setFont(QFont("Arial",20))
        self.manualControlGridLayout.addWidget(self.x_pos,5,0)

        # Y position input field
        self.y_pos = QLineEdit()
        self.y_pos.setText('0.00')
        self.y_pos.setFont(QFont("Arial",20))
        self.manualControlGridLayout.addWidget(self.y_pos,5,1)

        # button goto X
        self.b_gotoXY = QPushButton("Goto XY")
        self.manualControlGridLayout.addWidget(self.b_gotoXY,6,0,1,2)

        # button Emergency break
        self.b_emergency_break = QPushButton("Emergency break")
        self.manualControlGridLayout.addWidget(self.b_emergency_break,7,0,1,2)
        
        self.manualGroupBox.setLayout(self.manualControlGridLayout)
        
        return self.manualGroupBox

    def createLogWindow(self):
        self.logGridLayout = QGridLayout()
        self.logGroupBox = QGroupBox("Logger")
        self.logGroupBox.setStyleSheet("color: #000000;")

        # logger screen
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background-color: #AAAAAA;")
        self.logGridLayout.addWidget(self.log,0,0)

        self.logGroupBox.setLayout(self.logGridLayout)

        return self.logGroupBox

    def createVideoWindow(self):
        self.videoGridLayout = QGridLayout()
        self.videoGroupBox = QGroupBox("Video stream")
        self.videoGroupBox.setStyleSheet("color: #000000;")

        # logger screen
        self.videoStream = QPlainTextEdit()
        self.videoStream.setReadOnly(True)
        self.videoStream.setStyleSheet("background-color: #AAAAAA;")
        self.videoGridLayout.addWidget(self.videoStream,0,0)

        self.videoStream.appendPlainText("This will become a video stream widget.")

        self.videoGroupBox.setLayout(self.videoGridLayout)

        return self.videoGroupBox

    @Slot(str)
    def LogWindowInsert(self, message):
        self.log.appendPlainText("it works: " +str(message) + "\n")
        return

    def openSettingsIniFile(self):
        print("\nDEBUG: in function MainWindow::openSettingsIniFile()")
        self.settings = QSettings(os.path.dirname(os.path.realpath(__file__)) + "/settings.ini",  QSettings.IniFormat)
        self.log.appendPlainText("Opened settingsfile: " + os.path.dirname(os.path.realpath(__file__)) + "/settings.ini\n")
        return 

    def openBatchIniFile(self):
        print("\nDEBUG: in function MainWindow::openBatchIniFile()")
        self.settings_batch = QSettings(os.path.dirname(os.path.realpath(__file__)) + "/batch.ini",  QSettings.IniFormat)
        self.log.appendPlainText("Opened batch file: " + os.path.dirname(os.path.realpath(__file__)) + "/batch.ini\n")
        return 

class depricatedFunctions:    
    # button readData from port
    def readData(self):
        data = ""
        if self.b_connect.isChecked():
            data = self.PrintHAT_serial.readPort()
        else:
            self.log.appendPlainText("You try to read data while port is not connected")
        return data
    
################ MAIN APPLICATION ################
if __name__ == '__main__':
    # Instantiate MainWindow and app
    app = QApplication([])
    mwi = MainWindow()
    mwi.show()

    # Connect to printhat virtual port (this links the klipper software also)
    mwi.PrintHAT_serial.connect("/tmp/printer")

    # create stepper instances
    stepper_X = stepper.StepperControl()
    stepper_Y = stepper.StepperControl()
    stepper_well_positioning = stepper.StepperWellpositioning(stepper_X, stepper_Y, mwi.PrintHAT_serial)
    
    # Signal slot connections
    mwi.b_firmware_restart.clicked.connect(stepper_well_positioning.firmwareRestart)

    #mwi.b_start_batch.clicked.connect(mwi.startBatch)
    #mwi.b_stop_batch.clicked.connect(mwi.stopBatch)
    
    mwi.b_home_x.clicked.connect(stepper_well_positioning.homeX)
    mwi.b_get_pos.clicked.connect(stepper_well_positioning.getPosition)
    mwi.b_turn_up.clicked.connect(stepper_well_positioning.turnUp)
    mwi.b_turn_left.clicked.connect(stepper_well_positioning.turnLeft)
    mwi.b_turn_right.clicked.connect(stepper_well_positioning.turnRight)
    mwi.b_turn_down.clicked.connect(stepper_well_positioning.turnDown)
    mwi.b_gotoXY.clicked.connect(lambda: stepper_well_positioning.gotoXY(mwi.x_pos.text(), mwi.y_pos.text()))
    mwi.b_emergency_break.clicked.connect(stepper_well_positioning.emergencyBreak)
    mwi.message.connect(mwi.LogWindowInsert)
    mwi.message.emit("creating batchgroupbox")
    #stepper_X.message.connect(mwi.LogWindowInsert)
    #stepper_Y.message.connect(mwi.LogWindowInsert)
    stepper_well_positioning.message.sig.connect(mwi.LogWindowInsert)

    ret = app.exec_()
    mwi.PrintHAT_serial.disconnect() # stops the motors and disconnects from pseudo serial link /tmp/printer
    sys.exit(ret)
