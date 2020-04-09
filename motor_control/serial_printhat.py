## @package serial_printhat.py
## @brief serial_printhat.py handles the connection of the /tmp/printer pseudo serial port. It also writes the incoming G-code commands to the STM microcontroller on the PrintHAT.
## @author Gert van Lagen

import os
import sys
import serial
import lib.signal as signal

from PySide2.QtWidgets import *
from PySide2.QtCore import QTimer, QEventLoop, QTimer
from time import sleep

## @brief class GcodeSerial handles the /tmp/printer pseudoserial connection and writes incoming G-code. It also reads responses of the serial port.
## @author Gert van Lagen
class GcodeSerial:
    ## @param message is the class message signal used to display the result in the window log using its slot function.
    signals = signal.signalClass()

    ## @param first_move is set to True if the first move of the batch process is performed. When not using this boolean, the movement will be confirmed by this serial port to quick and the analysation of the well position starts to early.
    first_move = False

    ## @param ins is the number of instances created of GcodeSerial. This may not exceed 1.
    ins = 0
    
    ## @param connection_state is the boolean state of the serial interface.
    connection_state = False

    ## @brief GcodeSerial::__init__ creates a serial instance and checks if no more than one instance is created.
    # Furthermore it restarts the klipper service in order to make sure this service is not exited due to unexpected crashes of the window.
    def __init__(self):
        super().__init__()
        
        ## Instance limiter. Checks if an instance exists already. If so, it deletes the current instance.
        if GcodeSerial.ins >= 1:
            del self
            print("ERROR: you create multiple instances of " + __class__.__name__ + " while only 1 instance is allowed")
            return
        
        GcodeSerial.ins+=1
        
        # make sure klipper service is active
        os.system('sudo service klipper restart && sudo service klipper status | more')

        # wait a little bit before doing anything else
##        self.wait_ms(100)
        sleep(.1)
        
        return
        
    ## @brief GcodeSerial::msg(self, message) emits the message signal. This emit will be catched by the logging slot function in main.py.
    # @param message is the string message to be emitted.
    def msg(self, message):
        if message is not None:
            self.signals.mes.emit(self.__class__.__name__ + ": " + str(message))
        return
    
    ## @brief GcodeSerial::setFirstMove(self) sets first_move boolean to True.
    def setFirstMove(self):
        self.first_move = True
        return

    ## @brief GcodeSerial::getConnectionState(self) is a self.connection_state getter.
    # @return self.connection_state
    def getConnectionState(self):
        return self.connection_state

    ## @brief GcodeSerial::setConnectionState(self, conState) is a setter which sets the new connection_state value of the instance
    # @param conState is the boolean value of the new state
    def setConnectionState(self, conState):
        self.connection_state = conState
        return

    ## @brief GcodeSerial::connect connects to the pseudo serial port /tmp/printer. This port is the link with the klipper library which handles all the g-code and communication with the STM microcontroller.
    # On succeed it sets the connection state to true.
    # @param port is the port to be connected to. 
    def connect(self, port):
        print("\nDEBUG: in function ser_comm::connect(port)")
        try:
            ## @param self.serial is the serial instance.
            self.serial = serial.Serial(port, timeout=0.005)
            
            ## Open the serial port if it is not opened already.
            if not self.serial.is_open:
                print("\nERROR: Cannot connect to device on port {}".format(port))
            else:
                print("\nDEBUG: Opened serial communication on port {}".format(port))
                self.setConnectionState(True)
        except Exception as e:
            print("Exception in Ser_comm::connect(self, port)", e)
        return
    
    ## @brief Gcode_serial::executeGcode writes a bytearray containing a G-code to the serial port.
    # @param gcode_string is the string to be written to the serial port.
    def executeGcode(self, gcode_string):
        if self.getConnectionState():
            try:
                gcode_byte_array = bytearray(gcode_string, 'utf-8')
                self.serial.write(gcode_byte_array)
                if self.serial.inWaiting:
                    self.signals.stm_read_request.emit()
            except Exception as e:
                self.msg(e)
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return

    ## @brief Gcode_serial::readPort(self) reads data from port while port is not empty with a timeout of x seconds (which is initialised in the Gcode_serial::__init__ function).
    # @return data is the read data from the port.
    def readPort(self):
        #self.msg("Please wait, reading data from STM...")
        self.wait_ms(1)
        empty = "b\'\'"
        confirmation = 'ok'
        data = self.serial.readline()
        bytes_left = self.serial.inWaiting
        if bytes_left:
            data += self.serial.readline()
        
        read = str(data)
        if not (read.find(empty) >= 0):
            self.msg(read)
        
        ## Check if confirmation is stored in data ("ok"). Alse verify if the first movement is already finished in order to avoid to early well analysation.
        if read.find(confirmation, 0, len(read)) >= 0 and self.first_move is True:
            self.signals.confirmation.emit()
        return data

    ## @brief Gcode_serial::wait_ms(self, milliseconds) is a delay function.
    ## @param milliseconds is the number of milliseconds to wait.
    def wait_ms(self, milliseconds):
        GeneralEventLoop = QEventLoop()
        QTimer.singleShot(milliseconds, GeneralEventLoop.exit)
        GeneralEventLoop.exec_()
        return

    ## @brief Gcode_serial::disconnect stops the motors and the klipper service and then disconnects from pseudo serial port /tmp/printer.
    def disconnect(self):
        print("\nDEBUG: in function ser_comm::disconnect()")
        try:
            ## Stop motors
            print("\nDEBUG: stop motors using M18 G-code command")
            self.serial.write(b"M18\r\n")
        
            ## Stop klipper service and show its status
            print("\nDEBUG: stop klipper service")
            os.system('sudo service klipper stop && sudo service klipper status | more')
        
            ## Disconnect if connection is true
            if self.getConnectionState():
                self.serial.close()
            else:
                print("No connection to be closed\n")
        except Exception as e:
            print("exeption on serial disconnect: \n", e)
        return
