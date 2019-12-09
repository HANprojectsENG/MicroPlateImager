import serial_printhat

from PySide2.QtCore import QTimer, Signal, Slot, QEventLoop

class StepperControl:
    def __init__(self):
        self.position = 0
    
    def getPosition(self):
        return self.position

    def setPosition(self, pos):
        self.position = pos
        return

    def homeX(self):
        print("in StepperControl::homeX()")
        gcode_string = "G28 X0\r\n"
        return gcode_string

    def homeY(self):
        gcode_string = "G28 Y0\r\n"
        return gcode_string

    def gotoX(self, pos):
        gcode_string = "G0 X" 
        gcode_string += str(pos)
        gcode_string += "\r\n"
        return gcode_string

    def gotoY(self, pos):
        gcode_string = "G0 Y" 
        gcode_string += str(pos)
        gcode_string += "\r\n"
        return gcode_string

    def turnLeft(self):
        print("in function StepperControl::turnLeft()")
        gcode_string = "G0 Y"
        gcode_string += str(self.position-1)
        gcode_string += "\r\n"
        print("gcode_string")
        return gcode_string

    def turnLeft(self):
        print("in function StepperControl::turnLeft()")
        gcode_string = "G0 Y"
        gcode_string += str(self.position+1)
        gcode_string += "\r\n"
        print("gcode_string")
        return gcode_string

class StepperWellpositioning:
    message = Signal(str)
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
    
    def msg(self, message):
        self.message.emit(self.__class__.__name__ + ": " + str(message))
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
    def homeX(self):
        print("in wellpositioner::homeX()")
        self.gcode_serial.executeGcode(str(self.stepper_X.homeX()))

    def getPosition(self):
        self.gcode_serial.executeGcode("M114\r\n")
        print(self.gcode_serial.readPort())
        return

    def turnLeft(self):
        self.gcode_serial.executeGcode(str(self.stepper_X.turnLeft()))
        return

    def turnRight(self):
        self.gcode_serial.executeGcode(str(self.stepper_X.turnRight()))
        return