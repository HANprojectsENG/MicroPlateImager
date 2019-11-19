import sys
import serial_comm

from PyQt5.QtCore import QIODevice, QByteArray
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QDialog

class Gcode_controller(QDialog):

    PrintHAT_serial = serial_comm.ser_comm()
    
    def __init__(self, parent=None):
        super().__init__()
        
        layout = QVBoxLayout()
        
        # button CONNECT
        self.b_connect = QPushButton("CONNECT")
        self.b_connect.setCheckable(True)
        self.b_connect.setChecked(True)
        self.b_connect.toggle()
        self.b_connect.clicked.connect(self.btnstate)
        layout.addWidget(self.b_connect)

        # button HOME X
        self.b_home_x = QPushButton("HOME X")
        self.b_home_x.setCheckable(True)
        self.b_home_x.setChecked(False)
        self.b_home_x.clicked.connect(self.homeX)
        layout.addWidget(self.b_home_x)

        # button GET_POSITION
        self.b_get_pos = QPushButton("GET_POSITION")
        self.b_get_pos.setCheckable(False)
        self.b_get_pos.setChecked(False)
        self.b_get_pos.clicked.connect(self.btnstate)
        layout.addWidget(self.b_get_pos)

        # button FIRMWARE_RESET
        self.b_firm_rest = QPushButton("FIRMWARE_RESTART")
        self.b_firm_rest.setCheckable(False)
        self.b_firm_rest.setChecked(False)
        self.b_firm_rest.clicked.connect(self.btnstate)
        layout.addWidget(self.b_firm_rest)

        # button G0 X0
        self.b_x_zero = QPushButton("G0 X0")
        self.b_x_zero.setCheckable(False)
        self.b_x_zero.setChecked(False)
        self.b_x_zero.clicked.connect(self.btnstate)
        layout.addWidget(self.b_x_zero)

        # button G0 X10
        self.b_x_ten = QPushButton("G0 X10")
        self.b_x_ten.setCheckable(False)
        self.b_x_ten.setChecked(False)
        self.b_x_ten.clicked.connect(self.btnstate)
        layout.addWidget(self.b_x_ten)
        
        # button READ FOR 10S
        self.b_read = QPushButton("READ FOR 10S")
        self.b_read.setCheckable(True)
        self.b_read.setChecked(True)
        self.b_read.toggle()
        self.b_read.clicked.connect(self.btnstate)
        layout.addWidget(self.b_read)    
        
        self.setWindowTitle("Serial Dashbord PrintHAT")
        self.setLayout(layout)

    def btnstate(self):
        # button CONNECT / DISCONNECT
        if self.b_connect.isChecked():
            self.b_connect.setText("DISCONNECT")
            self.PrintHAT_serial.connect("/tmp/printer") # = serial_comm.ser_comm("/tmp/printer", None)
        else:
            self.b_connect.setText("CONNECT")
            self.PrintHAT_serial.disconnect()

        # button START READING / STOP READING
        if self.b_read.isChecked():
            if self.b_connect.isChecked():
                ready_to_read = PrintHAT_serial.dataAvailable()
                if ready_to_read == False:
                    print("no data")
                else:
                    print("Data captured:")
                    PrintHAT_serial.readData()
            else:
                print("You try to read data while port is not connected")

        # button FIRMWARE_RESTART
        if self.b_firm_rest.isChecked():
            if self.b_connect.isChecked():
                PrintHAT_serial.writeFirmwareRestart()
            else:
                print("Please connect first with your serial port")

        # button GET_POSITION
        if self.b_get_pos.isChecked():
            if self.b_connect.isChecked():
                PrintHAT_serial.writeGetPosition()
            else:
                print("Pleas connect first with your serial port")

                
        # button G0 X0
        if self.b_x_zero.isChecked():
            if self.b_connect.isChecked():
                PrintHAT_serial.writeXZero()
            else:
                print("Pleas connect first with your serial port")


        # button G0 X10
        if self.b_x_ten.isChecked():
            if self.b_connect.isChecked():
                PrintHAT_serial.writeXTen()
            else:
                print("Pleas connect first with your serial port")

    def homeX(self):
        # button HOME X
        if self.b_home_x.isChecked():
            if self.b_connect.isChecked():
                self.PrintHAT_serial.writeHomeX()
            else:
                print("Please connect first with your serial port")

####################################################
################# MAIN APPLICATION #################
####################################################
app = QApplication([])
ex = Gcode_controller()
ex.show()
sys.exit(app.exec_())
