import serial_printhat

from PySide2.QtCore import QTimer, Signal, Slot, QEventLoop, QObject

class signalClass(QObject):
    sig = Signal(str)

class StepperControl:
    message = Signal(str)

    def __init__(self):
        self.position = 0 # instance variable for each stepper motor
    
    def msg(self, message):
        if message is not None:
            self.message.emit(self.__class__.__name__ + ": " + str(message))
        return

    def getPosition(self):
        return float(self.position)

    def setPosition(self, pos):
        self.position = float(pos)
        return

    def homeX(self):
        gcode_string = "G28 X0 Y0\r\n"
        return gcode_string

    def homeY(self):
        gcode_string = "G28 Y0\r\n"
        return gcode_string

    def gotoX(self, pos):
        gcode_string = "G0 X" 
        gcode_string += str(pos)
        gcode_string += "\r\n"
        self.setPosition(pos)
        return gcode_string

    def gotoY(self, pos):
        gcode_string = "G0 Y" 
        gcode_string += str(pos)
        gcode_string += "\r\n"
        self.setPosition(pos)
        return gcode_string

    def turnUp(self):
        print("in function StepperControl::turnUp()")
        newPosition = self.getPosition()
        newPosition +=1
        self.setPosition(newPosition)
        gcode_string = "G0 Y"
        gcode_string += str(self.getPosition())
        gcode_string += "\r\n"
        return gcode_string

    def turnLeft(self):
        print("in function StepperControl::turnLeft()")
        newPosition = self.getPosition()
        newPosition -=1
        self.setPosition(newPosition)
        gcode_string = "G0 X"
        gcode_string += str(self.getPosition())
        gcode_string += "\r\n"
        return gcode_string

    def turnRight(self):
        print("in function StepperControl::turnRight()")
        newPosition = self.getPosition()
        newPosition +=1
        self.setPosition(newPosition)
        gcode_string = "G0 X"
        gcode_string += str(self.getPosition())
        gcode_string += "\r\n"
        return gcode_string

    def turnDown(self):
        print("in function StepperControl::turnDown()")
        newPosition = self.getPosition()
        newPosition -=1
        self.setPosition(newPosition)
        gcode_string = "G0 Y"
        gcode_string += str(self.getPosition())
        gcode_string += "\r\n"
        return gcode_string

class StepperWellpositioning(QObject):
    message = signalClass()
    stepper_X = None # object MotorControl class
    stepper_Y = None # object MotorControl class
    gcode_serial = None # object GcodeSerial class
    current_well_x = None
    current_well_y = None
    GeneralEventLoop = None

    def __init__(self, stepperX, stepperY, gcodeSerial):
        self.stepper_X = stepperX
        self.stepper_Y = stepperY
        self.gcode_serial = gcodeSerial
        return

    @Slot(str)
    def msg(self, message):
        if message is not None:
            print("emitting in msg of wellp class")
            self.message.sig.emit(self.__class__.__name__ + ": " + str(message))
        return

    def reset_current_well(self):
        self.set_current_well(None, None)
        return

    def set_current_well(self, x, y):
        self.current_well_x = x
        self.current_well_y = y
        return
        
    def get_current_well(self):
        if self.current_well_x == None or self.current_well_y == None:
            return None
        else: 
            return self.current_well_x, self.current_well_y
        return

    def wait_ms(self, milliseconds):
        for n in range(milliseconds):
            self.GeneralEventLoop = QEventLoop(self)
            QTimer.singleShot(1, self.GeneralEventLoop.exit)
            self.GeneralEventLoop.exec_()
        return

    @Slot()
    def goto_wel(self, x_pos, y_pos):
        return

    @Slot()
    def firmwareRestart(self):
        self.gcode_serial.executeGcode("FIRMWARE_RESTART\r\n")
        print(self.gcode_serial.readPort())
        return

    @Slot()
    def homeX(self):
        self.gcode_serial.executeGcode(str(self.stepper_X.homeX()))
        print(self.gcode_serial.readPort())
        return

    @Slot()
    def getPosition(self):
        self.gcode_serial.executeGcode("M114\r\n")
        print(self.gcode_serial.readPort())
        self.msg("test signal message in getPos()")
        return

    @Slot()
    def turnUp(self):
        self.gcode_serial.executeGcode(str(self.stepper_Y.turnUp()))
        return

    @Slot()
    def turnLeft(self):
        self.gcode_serial.executeGcode(str(self.stepper_X.turnLeft()))
        return

    @Slot()
    def turnRight(self):
        self.gcode_serial.executeGcode(str(self.stepper_X.turnRight()))
        return

    @Slot()
    def turnDown(self):
        self.gcode_serial.executeGcode(str(self.stepper_Y.turnDown()))
        return

    @Slot()
    def gotoXY(self, posX, posY):        
        #self.msg("Goto X, Y: " + str(posX) + ", " + str(posY))
        self.gcode_serial.executeGcode("G0 X" + str(posX) + " Y" + str(posY) + "\r\n")
        self.stepper_X.setPosition(posX)
        self.stepper_Y.setPosition(posY)
        return

    @Slot()
    def emergencyBreak(self):
        print("in function Wellpositioning::emergencyBreak(self)")
        self.gcode_serial.executeGcode("M112\r\n")
        return


