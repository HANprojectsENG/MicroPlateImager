import atexit
import sys
import serial_comm

from PyQt5.QtCore import QIODevice, QByteArray
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtWidgets import QPlainTextEdit, QApplication, QLabel, QPushButton, QVBoxLayout, QGroupBox, QGridLayout, QDialog, QLineEdit
from PyQt5.QtGui import QFont

class GUI(QDialog):

    PrintHAT_serial = serial_comm.ser_comm()
    
    def __init__(self, parent=None):
        super().__init__()
        
        layout = QVBoxLayout()

        self.gridGroupBox = QGroupBox("Control panel")
        layoutGrid = QGridLayout()       
        
        # button CONNECT
        self.b_connect = QPushButton("CONNECT")
        self.b_connect.setCheckable(True)
        self.b_connect.setChecked(True)
        self.b_connect.toggle()
        self.b_connect.clicked.connect(self.connectHandler)
        layoutGrid.addWidget(self.b_connect,0,0)

        # button FIRMWARE_RESET
        self.b_firm_rest = QPushButton("FIRMWARE_RESTART")
        self.b_firm_rest.clicked.connect(self.firmRes)
        layoutGrid.addWidget(self.b_firm_rest,0,1)
        
        # button HOME X
        self.b_home_x = QPushButton("HOME X")
        self.b_home_x.clicked.connect(self.homeX)
        layoutGrid.addWidget(self.b_home_x,0,2)

        # X position input field
        self.x_pos = QLineEdit()
        self.x_pos.setFont(QFont("Arial",20))
        layoutGrid.addWidget(self.x_pos,1,0)

        # button GOTO X
        self.b_goto_x = QPushButton("GOTO X")
        self.b_goto_x.clicked.connect(self.gotoX)
        layoutGrid.addWidget(self.b_goto_x,1,1)
        
        # button GET_POSITION
        self.b_get_pos = QPushButton("GET_POSITION")
        self.b_get_pos.clicked.connect(self.getPos)
        layoutGrid.addWidget(self.b_get_pos,2,0)
        
        # button READ FOR 10S
        self.b_read = QPushButton("REFRESH LOGGER")
        self.b_read.toggle()
        self.b_read.clicked.connect(self.readData)
        layoutGrid.addWidget(self.b_read,2,1)    

        # logger screen
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.gridGroupBox.setLayout(layoutGrid)
        layout.addWidget(self.gridGroupBox)
        layout.addWidget(self.log)
        
        self.setWindowTitle("PrintHAT")
        self.setLayout(layout)
        
    # button CONNECT / DISCONNECT
    def connectHandler(self):
        if self.b_connect.isChecked():
            self.b_connect.setText("DISCONNECT")
            self.PrintHAT_serial.connect("/tmp/printer")
            self.log.appendPlainText("Connected to port /tmp/printer")
        else:
            self.b_connect.setText("CONNECT")
            self.PrintHAT_serial.disconnect()
            self.log.appendPlainText("Disconnected from port /tmp/printer")
        self.log.appendPlainText(str(self.readData()))
        return
        
    # button HOME X
    def homeX(self):
        if self.b_connect.isChecked():
            self.PrintHAT_serial.writeHomeX()
        else:
            print("Please connect first with your serial port")
            self.log.append("Please connect first with your serial port")
        self.log.appendPlainText(str(self.readData()))
        return

    # button GET_POSITION
    def getPos(self):
        if self.b_connect.isChecked():
            self.PrintHAT_serial.writeGetPosition()
        else:
            print("Pleas connect first with your serial port")
            self.log.appendPlainText("Please connect first with your serial port")
        self.log.appendPlainText(str(self.readData()))
        return
        
    # button FIRMWARE_RESTART
    def firmRes(self):
        if self.b_connect.isChecked():
            self.PrintHAT_serial.writeFirmwareRestart()
        else:
            print("Please connect first with your serial port")
            self.log.appendPlainText("Please connect first with your serial port")
        self.log.appendPlainText(str(self.readData()))
        return

    def gotoX(self):
        pos = self.x_pos.text()
        self.PrintHAT_serial.writeGotoX(pos)
        self.log.appendPlainText("Go to X-coordinate " + str(pos))
        self.log.appendPlainText(str(self.readData()))
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
ex = GUI()
ex.show()
ret = app.exec_()
ex.disconnectFromPortAtExit()
sys.exit(ret)
