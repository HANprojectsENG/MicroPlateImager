import os
import sys
import serial_printhat
import stepper

from PySide2.QtWidgets import QPlainTextEdit, QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QDialog, QLineEdit, QFileDialog
from PySide2.QtGui import QFont
from PySide2.QtCore import QSettings

class MainWindow(QDialog):

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

        # button START BATCH
        self.b_start_batch = QPushButton("START BATCH")
        #self.b_start_batch.clicked.connect(self.startBatch)
        self.processControlGridLayout.addWidget(self.b_start_batch,4,0)

        # button STOP BATCH
        self.b_stop_batch = QPushButton("STOP BATCH")
        #self.b_stop_batch.clicked.connect(self.stopBatch)
        self.processControlGridLayout.addWidget(self.b_stop_batch,5,0)
    
        self.batchGroupBox.setLayout(self.processControlGridLayout)

        return self.batchGroupBox

    def createManualGroupBox(self):
        self.manualControlGridLayout = QGridLayout()   
        self.manualGroupBox = QGroupBox("Manual XY-control")
        self.manualGroupBox.setStyleSheet("color: #000000;")

        # X position input field - deprecated
        self.x_pos = QLineEdit()
        self.x_pos.setFont(QFont("Arial",20))
        #self.manualControlGridLayout.addWidget(self.x_pos,0,1)

        # button HOME X
        self.b_home_x = QPushButton("HOME X")
        #self.b_home_x.clicked.connect(self.homeX)
        self.manualControlGridLayout.addWidget(self.b_home_x,0,0,1,2)

        # button GET_POSITION
        self.b_get_pos = QPushButton("GET_POSITION")
        #self.b_get_pos.clicked.connect(self.getPos)
        self.manualControlGridLayout.addWidget(self.b_get_pos,1,0,1,2)
        
        # button TURN UP
        self.b_turn_up = QPushButton("^")
        #self.b_turn_up.clicked.connect(self.turnUp)
        self.manualControlGridLayout.addWidget(self.b_turn_up,2,0,1,2)

        # button TURN LEFT
        self.b_turn_left = QPushButton("<")
        #self.b_turn_left.clicked.connect(self.turnLeft)
        self.manualControlGridLayout.addWidget(self.b_turn_left,3,0)

        # button TURN RIGHT
        self.b_turn_right = QPushButton(">")
        #self.b_turn_right.clicked.connect(self.turnRight)
        self.manualControlGridLayout.addWidget(self.b_turn_right,3,1)

        # button TURN DOWN
        self.b_turn_down = QPushButton("v")
        #self.b_turn_down.clicked.connect(self.turnDown)
        self.manualControlGridLayout.addWidget(self.b_turn_down,4,0,1,2)
        
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
    # button CONNECT / DISCONNECT
    def connectHandler(self):
        if self.b_connect.isChecked():
            self.b_connect.setText("CONNECTED")
            self.PrintHAT_serial.connect("/tmp/printer")
            self.b_connect.setStyleSheet('QPushButton {background-color: #00ff00; border: none}')
            self.log.appendPlainText("Connected to port /tmp/printer")
        else:
            self.b_connect.setText("DISCONNECTED")
            self.PrintHAT_serial.disconnect()
            self.b_connect.setStyleSheet('QPushButton {background-color: #ff0000; border: none}')
            self.log.appendPlainText("Disconnected from port /tmp/printer")
        return
        
    # button HOME X
    # @TODO: update function with homeXYZ functionality
    def homeX(self):
        if self.b_connect.isChecked():
            self.PrintHAT_serial.writeHomeX()
            self.stepper_X.setPosition(0)
        else:
            self.log.appendPlainText("Please connect first with your serial port")

        self.log.appendPlainText(str(self.readData()))
        return

    # button GET_POSITION
    def getPos(self):
        if self.b_connect.isChecked():
            self.PrintHAT_serial.writeGetPosition()
            self.log.appendPlainText("Getting position...")
        else:
            self.log.appendPlainText("Please connect first with your serial port")
        
        self.log.appendPlainText(str(self.readData()))
        return
        
    # button FIRMWARE_RESTART
    def firmRes(self):
        if self.b_connect.isChecked():
            self.PrintHAT_serial.writeFirmwareRestart()
        else:
            self.log.appendPlainText("Please connect first with your serial port")
        self.log.appendPlainText(str(self.readData()))
        return

    def turnUp(self):
        print("\nDEBUG: in function MainWindow::turnUp()")
        if self.PrintHAT_serial.getConnectionState():
            pos = self.stepper_Y.getPosition()
            pos += 1
            self.stepper_Y.setPosition(pos)
            self.PrintHAT_serial.writeGotoY(pos)
            self.log.appendPlainText("Go to Y-coordinate " + str(pos))
            self.log.appendPlainText(str(self.readData()))
        else:
            self.log.appendPlainText("Please connect first with your serial port")
        return

    def turnRight(self):
        print("\nDEBUG: in function MainWindow::turnRight()")
        if self.PrintHAT_serial.getConnectionState():
            pos = self.stepper_X.getPosition()
            pos += 1
            self.stepper_X.setPosition(pos)
            self.PrintHAT_serial.writeGotoX(pos)
            self.log.appendPlainText("Go to X-coordinate " + str(pos))
            self.log.appendPlainText(str(self.readData()))
        else:
            self.log.appendPlainText("Please connect first with your serial port")
        return

    def turnLeft(self):
        print("\nDEBUG: in function MainWindow::turnLeft()")
        if self.PrintHAT_serial.getConnectionState():
            pos = self.stepper_X.getPosition()
            if pos > 0:
                pos -= 1
            else:
                self.log.appendPlainText("Moving out of range, current position: " + str(pos))

            self.stepper_X.setPosition(pos)
            self.PrintHAT_serial.writeGotoX(pos)
            self.log.appendPlainText("Go to X-coordinate " + str(pos))
            self.log.appendPlainText(str(self.readData()))
        else:
            self.log.appendPlainText("Please connect first with your serial port")
        return

    def turnDown(self):
        print("\nDEBUG: in function MainWindow::turnDown()")
        if self.PrintHAT_serial.getConnectionState():
            pos = self.stepper_Y.getPosition()
            if pos > 0:
                pos -= 1
            else:
                self.log.appendPlainText("Moving out of range, current Y-coordinate: " + str(pos))

            self.stepper_Y.setPosition(pos)
            self.PrintHAT_serial.writeGotoY(pos)
            self.log.appendPlainText("Go to Y-coordinate " + str(pos))
            self.log.appendPlainText(str(self.readData()))
        else:
            self.log.appendPlainText("Please connect first with your serial port")
        return
    
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
    #mwi.b_start_batch.clicked.connect(mwi.startBatch)
    #mwi.b_stop_batch.clicked.connect(mwi.stopBatch)
    mwi.b_home_x.clicked.connect(stepper_well_positioning.homeX)
    mwi.b_get_pos.clicked.connect(stepper_well_positioning.getPosition)
    #mwi.b_turn_up.clicked.connect(mwi.turnUp)
    mwi.b_turn_left.clicked.connect(stepper_well_positioning.turnLeft)
    #mwi.b_turn_right.clicked.connect(mwi.turnRight)
    #mwi.b_turn_down.clicked.connect(mwi.turnDown)
    ret = app.exec_()
    mwi.PrintHAT_serial.disconnect()
    sys.exit(ret)
