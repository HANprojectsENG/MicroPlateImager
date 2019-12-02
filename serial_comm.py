import os
import serial

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
            self.serial = serial.Serial(port)#QSerialPort(port)

            if not self.serial.is_open:
                print("\nDEBUG: Cannot connect to device on port {}".format(port))
            else:
                print("\nDEBUG: Opened serial communication on port {}".format(port))

        except Exception as e:
            print("Exception in Ser_comm::connect(self, port)", e)
            
        return
    
    def writeFirmwareRestart(self):
        print("\nDEBUG: in function ser_comm::writeFirmwareRestart()")
        self.serial.write(b'FIRMWARE_RESTART\r\n')
        return

    def writeHomeX(self):
        print("\nDEBUG: in function ser_com::writeHomeX()")
        self.serial.write(b'G28 X0\r\n')
        return

    def writeGetPosition(self):
        print("\nDEBUG: in function ser_com::writeGetPosition()")
        self.serial.write(b'M114\r\n')
        return

    def writeGotoX(self, pos):
        print("\nDEBUG: in function ser_comm::writeGotoX()")
        posStr = "G0 X" 
        posStr += pos
        posStr += "\r\n"
        posByteArray = bytearray(posStr, 'utf-8')
        self.serial.write(posByteArray)
        return
    
    def readPort(self):
        print("\nDEBUG: in function ser_comm::readPort()")
        return self.serial.readline()

    def disconnect(self):
        print("\nDEBUG: in function ser_comm::disconnect()")
        self.serial.close()
