from PyQt5.QtCore import QIODevice, QByteArray
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtWidgets import *

class ser_comm:
    def __init__(self, parent=None):
        super().__init__()
        self.isOpen = False

    def connect(self, port):
        # OPEN THE SERIAL PORT
        self.serial = QSerialPort(port)
        self.serial.setPortName(port)

        if self.serial.open(QIODevice.ReadWrite):
            self.isOpen = True
            print("Opened serial communication on port {}".format(port))
            self.serial.setBaudRate(250000)
            
        else:
            raise IOError("Cannot connect to device on port {}".format(port))
            self.isOpen = False
        return
    
    def writeFirmwareRestart(self):
        print("\nDEBUG: in function ser_comm::writeFirmwareRestart()")
        firm_rest = QByteArray()
        firm_rest.append("FIRMWARE_RESTART\r\n")
        self.serial.write(firm_rest)
        return

    def writeHomeX(self):
        print("\nDEBUG: in function ser_com::writeHomeX()")
        HomeX = QByteArray()
        HomeX.append("G28 X0")
        self.serial.write(HomeX)
        return

    def writeGetPosition(self):
        print("\nDEBUG: in function ser_com::writeGetPosition()")
        position = QByteArray()
        position.append("M114")
        self.serial.write(position)
        return

    def writeXZero(self):
        print("\nDEBUG: in function ser_com::writeXZero()")
        position = QByteArray()
        position.append("G0 X0")
        self.serial.write(position)
        return    

    def writeXten(self):
        print("\nDEBUG: in function ser_com::writeXTen()")
        position = QByteArray()
        position.append("G0 X10")
        self.serial.write(position)
        return  
    
    def dataAvailable(self):
        print("\nDEBUG: in function ser_comm::dataAvailable()")
        readLine = self.serial.waitForReadyRead(2000)
        return readLine

    def readData(self):
        print("\nDEBUG: in function ser_comm::readData()")
        output = self.serial.readAll()
        print("output: " + str(output))
        return

    def disconnect(self):
        print("\nDEBUG: in function ser_comm::disconnect()")
        self.serial.close()
        self.isOpen = False
