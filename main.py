import sys
import serial_comm
import stepper_motor

from PySide2.QtWidgets import QPlainTextEdit, QApplication, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QDialog, QLineEdit
from PySide2.QtGui import QFont

class MainWindow(QDialog):

    PrintHAT_serial = serial_comm.ser_comm()

    stepperX = stepper_motor.stepper()

    def __init__(self, parent=None):
        super().__init__()
        
        self.mainWindowLayout = QGridLayout()    
           
        # groupbox with manual control widgets
        mgb = self.createManualGroupBox()

        # groupbox with batch process control widgets
        bgb = self.createBatchGroupBox()
        
        # groupbox with log window
        lgb = self.createLogWindow()

        # fill mainWindowLayout
        self.mainWindowLayout.addWidget(bgb,0,0)
        self.mainWindowLayout.addWidget(mgb,1,0)
        self.mainWindowLayout.addWidget(lgb,1,1)
        
        self.setWindowTitle("PrintHAT")
        self.setLayout(self.mainWindowLayout)

    def createBatchGroupBox(self):
        self.processControlGridLayout = QGridLayout()        

        self.batchGroupBox = QGroupBox("Batch control")

        # button CONNECT
        self.b_connect = QPushButton("DISCONNECTED")
        self.b_connect.setStyleSheet('QPushButton {background-color: #ff0000; border: none}')
        self.b_connect.setCheckable(True)
        self.b_connect.setChecked(True)
        self.b_connect.toggle()
        self.b_connect.clicked.connect(self.connectHandler)
        self.processControlGridLayout.addWidget(self.b_connect,0,0)

        # button FIRMWARE_RESET
        self.b_firm_rest = QPushButton("FIRMWARE_RESTART")
        self.b_firm_rest.clicked.connect(self.firmRes)
        self.processControlGridLayout.addWidget(self.b_firm_rest,1,0)
        
        # button START BATCH
        self.b_start_batch = QPushButton("START BATCH")
        #self.b_start_batch.clicked.connect(self.startBatch)
        self.processControlGridLayout.addWidget(self.b_start_batch)

        # button STOP BATCH
        self.b_stop_batch = QPushButton("STOP BATCH")
        #self.b_start_batch.clicked.connect(self.stopBatch)
        self.processControlGridLayout.addWidget(self.b_stop_batch)
    
        self.batchGroupBox.setLayout(self.processControlGridLayout)

        return self.batchGroupBox

    def createManualGroupBox(self):
        self.manualControlGridLayout = QGridLayout()   
        self.manualGroupBox = QGroupBox("Manual XY-control")

        # button MOVE - deprecated
        self.b_goto_x = QPushButton("MOVE")
        self.b_goto_x.clicked.connect(self.gotoX)
        #self.manualControlGridLayout.addWidget(self.b_goto_x,0,0)

        # X position input field - deprecated
        self.x_pos = QLineEdit()
        self.x_pos.setFont(QFont("Arial",20))
        #self.manualControlGridLayout.addWidget(self.x_pos,0,1)

        # button HOME X
        self.b_home_x = QPushButton("HOME X")
        self.b_home_x.clicked.connect(self.homeX)
        self.manualControlGridLayout.addWidget(self.b_home_x,0,0,1,2)

        # button GET_POSITION
        self.b_get_pos = QPushButton("GET_POSITION")
        self.b_get_pos.clicked.connect(self.getPos)
        self.manualControlGridLayout.addWidget(self.b_get_pos,1,0,1,2)
        
        # button TURN UP
        self.b_turn_up = QPushButton("^")
        self.b_turn_up.clicked.connect(self.turnUp)
        self.manualControlGridLayout.addWidget(self.b_turn_up,2,0,1,2)

        # button TURN LEFT
        self.b_turn_left = QPushButton("<")
        self.b_turn_left.clicked.connect(self.turnLeft)
        self.manualControlGridLayout.addWidget(self.b_turn_left,3,0)

        # button TURN RIGHT
        self.b_turn_right = QPushButton(">")
        self.b_turn_right.clicked.connect(self.turnRight)
        self.manualControlGridLayout.addWidget(self.b_turn_right,3,1)

        # button TURN DOWN
        self.b_turn_down = QPushButton("v")
        self.b_turn_down.clicked.connect(self.turnDown)
        self.manualControlGridLayout.addWidget(self.b_turn_down,4,0,1,2)
        
        self.manualGroupBox.setLayout(self.manualControlGridLayout)
        
        return self.manualGroupBox

    def createLogWindow(self):
        self.logGridLayout = QGridLayout()
        self.logGroupBox = QGroupBox("Logger")
        
        # logger screen
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.logGridLayout.addWidget(self.log,0,0)

        self.logGroupBox.setLayout(self.logGridLayout)

        return self.logGroupBox
    
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
        #self.log.appendPlainText(str(self.readData()))
        return
        
    # button HOME X
    def homeX(self):
        if self.b_connect.isChecked():
            self.PrintHAT_serial.writeHomeX()
        else:
            print("Please connect first with your serial port")
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

    def gotoX(self):
        pos = self.x_pos.text()
        self.PrintHAT_serial.writeGotoX(pos)
        self.log.appendPlainText("Go to X-coordinate " + str(pos))
        self.log.appendPlainText(str(self.readData()))
        return

    def turnUp(self):
        print("in function turnUp()")
        return

    def turnRight(self):
        print("in function turnRight()")
        return

    def turnLeft(self):
        print("in function turnLeft()")
        return

    def turnDown(self):
        print("in function turnDown()")
        return
    # button readData from port
    def readData(self):
        data = ""
        if self.b_connect.isChecked():
            data = self.PrintHAT_serial.readPort()
        else:
            print("You try to read data while port is not connected")
        return data
    
    def disconnectFromPortAtExit(self):
        print("Disconnecting from port")
        self.PrintHAT_serial.disconnect()
        return
    

####################################################
################# MAIN APPLICATION #################
####################################################
app = QApplication([])
mwi = MainWindow()
mwi.show()
ret = app.exec_()
mwi.disconnectFromPortAtExit()
sys.exit(ret)
