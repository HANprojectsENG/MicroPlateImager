import os
import serial

#from PyQt5.QtCore import QIODevice, QByteArray
#from PyQt5.QtSerialPort import QSerialPort # package QtSerialPort not yet available for PySide2
from PySide2.QtWidgets import *

class ser_comm:
    connectionState = 0

    def __init__(self, parent=None):
        super().__init__()
        # make sure klipper service is active
        os.system('sudo service klipper restart')
        
    def connect(self, port):
        print("\nDEBUG: in function ser_comm::connect(port)")
        
        try:
            # open the serial port
            self.serial = serial.Serial(port, timeout=1)

            if not self.serial.is_open:
                print("\nERROR: Cannot connect to device on port {}".format(port))
            else:
                print("\nDEBUG: Opened serial communication on port {}".format(port))
                self.connectionState = 1

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
        data = self.serial.readline()
        no_bytes_left = self.serial.inWaiting
        if no_bytes_left:
            data += self.serial.readline()
        
        return data

    def disconnect(self):
        print("\nDEBUG: in function ser_comm::disconnect()")
        if self.connectionState == 1:
            self.serial.close()
        else:
            print("No connection to be closed\n")

