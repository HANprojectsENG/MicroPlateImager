import os

from PyQt5.QtCore import QIODevice, QByteArray
from PyQt5.QtSerialPort import QSerialPort # package QtSerialPort not yet available for PySide2
from PySide2.QtWidgets import *

class ser_comm:
    def __init__(self, parent=None):
        super().__init__()
        # make sure klipper service is active
        os.system('sudo service klipper restart')
        
    def connect(self, port):
        print("\nDEBUG: in function ser_comm::connect(port)")
        
        try:
            # open the serial port
            self.serial = QSerialPort(port)
            self.serial.setPortName(port)

            if self.serial.open(QIODevice.ReadWrite):
                print("\nDEBUG: Opened serial communication on port {}".format(port))
                self.serial.setBaudRate(115200)
            else:
                raise IOError("\nDEBUG: Cannot connect to device on port {}".format(port))

        except Exception as e:
            print("Unable to open serial port", e)
            
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
        HomeX.append("G28 X0\r\n")
        self.serial.write(HomeX)
        return

    def writeGetPosition(self):
        print("\nDEBUG: in function ser_com::writeGetPosition()")
        position = QByteArray()
        position.append("M114\r\n")
        self.serial.write(position)
        return

    def writeGotoX(self, pos):
        print("\nDEBUG: in function ser_comm::writeGotoX()")
        position = QByteArray()
        position.append("G0 X")
        position.append(pos)
        position.append("\r\n")
        self.serial.write(position)
        return
                          
    def writeXZero(self):
        print("\nDEBUG: in function ser_com::writeXZero()")
        position = QByteArray()
        position.append("G0 X0\r\n")
        self.serial.write(position)
        return    
    
    def readPort(self):
        print("\nDEBUG: in function ser_comm::readPort()")
        readLine = QByteArray()
        if self.serial.bytesAvailable():
            while not self.serial.atEnd():
                newByte = self.serial.read(1)
                readLine.append(newByte)
            print(str(readLine))
        return readLine

    def disconnect(self):
        print("\nDEBUG: in function ser_comm::disconnect()")
        self.serial.close()
