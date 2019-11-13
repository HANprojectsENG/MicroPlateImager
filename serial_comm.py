from PyQt5.QtCore import QIODevice, QByteArray
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtWidgets import *

class ser_comm:
    def __init__(self, port, parent=None):
        super().__init__()
        self.isOpen = False
        
        # OPEN THE SERIAL PORT
        self.serial = QSerialPort(port)
        self.serial.setPortName(port)

        if self.serial.open(QIODevice.ReadWrite):
            self.isOpen = True
            print("Opened serial communication on port {}".format(port))
            self.serial.setBaudRate(115200)
            
        else:
            raise IOError("Cannot connect to device on port {}".format(port))
            self.isOpen = False

    def writeHelloWorld(self):
        print("\nDEBUG: in function ser_comm::writeHelloWorld()")
        homing = QByteArray()
        homing.append("Hello World\r\n")
        self.serial.write(homing)
        return
    
    def dataAvailable(self):
        print("\nDEBUG: in function ser_comm::dataAvailable()")
        readLine = self.serial.waitForReadyRead(10000)
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
