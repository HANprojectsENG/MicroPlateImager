import sys
import serial_comm

from PyQt5.QtCore import QIODevice, QByteArray
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QDialog

class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        
        layout = QVBoxLayout()

        self.b_connect = QPushButton("CONNECT")
        self.b_connect.setCheckable(True)
        self.b_connect.setChecked(True)
        self.b_connect.toggle()
        self.b_connect.clicked.connect(self.btnstate)
        layout.addWidget(self.b_connect)

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
        PrintHAT_serial = serial_comm.ser_comm("/dev/ttyUSB0", None)
        
        if self.b_connect.isChecked():
            self.b_connect.setText("DISCONNECT")
            if not PrintHAT_serial.isOpen:
                PrintHAT_serial = serial_comm.ser_comm("/dev/ttyUSB0", None)           
            PrintHAT_serial.writeHelloWorld()
        else:
            self.b_connect.setText("CONNECT")
            if PrintHAT_serial.isOpen:
                PrintHAT_serial.disconnect()

        # button START READING / STOP READING
        if self.b_read.isChecked():
            if self.b_connect.isChecked():
                self.b_read.setText("STOP READING")
                ready_to_read = PrintHAT_serial.dataAvailable()
                if ready_to_read == False:
                    print("no data")
                else:
                    print("Data captured:")
                    PrintHAT_serial.readData()
                    self.b_read.setChecked(False)
                    self.b_read.setText("READ FOR 10S")
            else:
                print("You try to read data while port is not connected")
        else:    
            self.b_read.setText("READ FOR 10S")                            
                    
####################################################
################# MAIN APPLICATION #################
####################################################
app = QApplication([])
ex = Form()
ex.show()
sys.exit(app.exec_())
