import os
import serial

from PySide2.QtWidgets import *

class GcodeSerial:
    ins = 0 # static instance counter, may not exceed 1
    connectionState = False
    
    def __init__(self):#, parent=None):
        super().__init__()
        
        # if already an instance exist
        if GcodeSerial.ins >= 1:
            del self
            print("ERROR: you create multiple instances of " + __class__.__name__ + " while only 1 instance is allowed")
            return
        
        GcodeSerial.ins+=1
        
        # make sure klipper service is active
        os.system('sudo service klipper restart')
        
    def getConnectionState(self)    :
        return self.connectionState

    def setConnectionState(self, conState):
        self.connectionState = conState
        return

    def connect(self, port):
        print("\nDEBUG: in function ser_comm::connect(port)")
        
        try:
            # open the serial port
            self.serial = serial.Serial(port, timeout=3.0)

            if not self.serial.is_open:
                print("\nERROR: Cannot connect to device on port {}".format(port))
            else:
                print("\nDEBUG: Opened serial communication on port {}".format(port))
                self.setConnectionState(True)
        except Exception as e:
            print("Exception in Ser_comm::connect(self, port)", e)
        return
    
    def executeGcode(self, gcode_string):
        try:
            gcode_byte_array = bytearray(gcode_string, 'utf-8')
            self.serial.write(gcode_byte_array)
        except Exception as e:
            print("Exception in Ser_comm::executeGode(self, gcode_string)", e)
        return

    # @TODO: fuse writeGotoX with writeGotoY in one G0 X<pos> Y<pos> F<velocity> command
    def writeGotoX(self, pos):
        print("\nDEBUG: in function ser_comm::writeGotoX()")
        posStr = "G0 X" 
        posStr += str(pos)
        posStr += "\r\n"
        posByteArray = bytearray(posStr, 'utf-8')
        self.serial.write(posByteArray)
        return
    
    def writeGotoY(self, pos):
        print("\nDEBUG: in function ser_comm::writeGotoX()")
        posStr = "G0 Y" 
        posStr += str(pos)
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
        if self.getConnectionState():
            self.serial.close()
        else:
            print("No connection to be closed\n")

