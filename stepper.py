## @package stepper.py
# @brief stepper.py contains classes for stepper motor control, G-code string creation, homing and well positioning.

import serial_printhat

from PySide2.QtCore import QTimer, Signal, Slot, QEventLoop, QObject

## @brief signalClass(QObject) contains a signal. 
# @param QObject is passed because Signal() may be used only when the class is inherited from QObject. 
# this way the signal can be used by each class, even though it does not inherit from QObject.
class signalClass(QObject):
    sig = Signal(str)

## @brief StepperControl contains steppermotor specific information and creates G-code strings when called specific functions like turnRight().
class StepperControl:
    ## @param message is the class message signal used to display the result in the window log using its slot function.
    message = Signal(str)

    ## @brief StepperControl::__init__(self) sets the motor position instance variable to zero.
    def __init__(self):
         ## @param self.position is the instance position variable specific for each stepper motor
         self.position = 0

    ## @brief StepperControl::msg(self, message) emits the message signal. This emit will be catched by the logging slot function in main.py.
    # @param message is the string message to be emitted.
    def msg(self, message):
        if message is not None:
            self.message.emit(self.__class__.__name__ + ": " + str(message))
        return

    ## @brief StepperControl::getPosition(self) returns the position of the motor instance.
    # @return position of the motor instance
    def getPosition(self):
        return float(self.position)

    ## @brief StepperControl::getPosition(self) sets the position of the motor instance.
    # @param pos is the new position which is set.
    def setPosition(self, pos):
        self.position = float(pos)
        return

    ## @brief StepperControl::homeX(self) creates a homing G-code string for the X-axis.
    # @return gcode_string is the homing string to be executed.
    def homeX(self):
        gcode_string = "G28 X0 Y0\r\n"
        return gcode_string

    ## @brief StepperControl::homeY(self) creates a homing G-code string for the Y-axis.
    # @return gcode_string is the homing string to be executed.
    def homeY(self):
        gcode_string = "G28 Y0\r\n"
        return gcode_string

    ## @brief StepperControl::gotoX(self, pos) creates a move G-code string for the X-axis.
    # @param pos is the desired position
    # @return gcode_string is the move string to be executed.
    def gotoX(self, pos):
        gcode_string = "G0 X" 
        gcode_string += str(pos)
        gcode_string += "\r\n"
        self.setPosition(pos)
        return gcode_string

    ## @brief StepperControl::gotoY(self, pos) creates a move G-code string for the Y-axis.
    # @param pos is the desired position
    # @return gcode_string is the move string to be executed.
    def gotoY(self, pos):
        gcode_string = "G0 Y" 
        gcode_string += str(pos)
        gcode_string += "\r\n"
        self.setPosition(pos)
        return gcode_string

    ## @brief StepperControl::turnUp(self) creates a move G-code string for the Y-axis. Each call results in a fixed distance movement.
    # @return gcode_string is the move string to be executed.
    def turnUp(self):
        print("in function StepperControl::turnUp()")
        newPosition = self.getPosition()
        newPosition +=1
        self.setPosition(newPosition)
        gcode_string = "G0 Y"
        gcode_string += str(self.getPosition())
        gcode_string += "\r\n"
        return gcode_string

    ## @brief StepperControl::turnLeft(self) creates a move G-code string for the X-axis. Each call results in a fixed distance movement.
    # @return gcode_string is the move string to be executed.
    def turnLeft(self):
        print("in function StepperControl::turnLeft()")
        newPosition = self.getPosition()
        newPosition -=1
        self.setPosition(newPosition)
        gcode_string = "G0 X"
        gcode_string += str(self.getPosition())
        gcode_string += "\r\n"
        return gcode_string

    ## @brief StepperControl::turnRight(self) creates a move G-code string for the X-axis. Each call results in a fixed distance movement.
    # @return gcode_string is the move string to be executed.
    def turnRight(self):
        print("in function StepperControl::turnRight()")
        newPosition = self.getPosition()
        newPosition +=1
        self.setPosition(newPosition)
        gcode_string = "G0 X"
        gcode_string += str(self.getPosition())
        gcode_string += "\r\n"
        return gcode_string

    ## @brief StepperControl::turnDown(self) creates a move G-code string for the Y-axis. Each call results in a fixed distance movement.
    # @return gcode_string is the move string to be executed.
    def turnDown(self):
        print("in function StepperControl::turnDown()")
        newPosition = self.getPosition()
        newPosition -=1
        self.setPosition(newPosition)
        gcode_string = "G0 Y"
        gcode_string += str(self.getPosition())
        gcode_string += "\r\n"
        return gcode_string

## @brief StepperWellpositioning(QObject) takes care of the positioning of the wells under the camera.
# @param QObject is used to be able to use QObject
# @todo check if param QObject is necessary or if class signalClass() solves the QObject inheritance already.
class StepperWellpositioning(QObject):
    message = signalClass()
    stepper_X = None ## object MotorControl class
    stepper_Y = None ## object MotorControl class
    gcode_serial = None ## object GcodeSerial class
    current_well_x = None
    current_well_y = None
    GeneralEventLoop = None

    ## @brief StepperWellpositioning(QObject)::__init__ initialises the stepper objects for X and Y axis and initialises the gcodeSerial to the class member variable.
    # @param stepperX is the StepperControl object representing the X-axis
    # @param stepperY is the StepperControl object representing the Y-axis
    # @param gcodeSerial is the GcodeSerial object representing the serial connection with the PrintHAT
    def __init__(self, stepperX, stepperY, gcodeSerial):
        self.stepper_X = stepperX
        self.stepper_Y = stepperY
        self.gcode_serial = gcodeSerial
        return

    ## @brief StepperWellpositioning(QObject)::msg emits the message signal. This emit will be catched by the logging slot function in main.py.
    # @param message is the string message to be emitted.
    @Slot(str)
    def msg(self, message):
        if message is not None:
            print("emitting in msg of wellp class")
            self.message.sig.emit(self.__class__.__name__ + ": " + str(message))
        return

    ## @brief StepperWellpositioning(QObject)::reset_current_well(self) sets the current well position (XY) to None
    def reset_current_well(self):
        self.set_current_well(None, None)
        return

    ## @brief StepperWellpositioning(QObject)::set_current_well(self) sets the current well position.
    # @param x is the x well coordinate
    # @param y is the y well coordinate
    def set_current_well(self, x, y):
        self.current_well_x = x
        self.current_well_y = y
        return
        
    ## @brief StepperWellpositioning(QObject)::get_current_well(self) is the well position getter.
    # @return current_well_x and current_well_y, the XY well position coordinates
    def get_current_well(self):
        if self.current_well_x == None or self.current_well_y == None:
            return None
        else: 
            return self.current_well_x, self.current_well_y
        return

    ## @brief StepperWellpositioning(QObject)::wait_ms(self, milliseconds) is a delay function.
    # @param milliseconds is the number of milliseconds to wait.
    def wait_ms(self, milliseconds):
        for n in range(milliseconds):
            self.GeneralEventLoop = QEventLoop(self)
            QTimer.singleShot(1, self.GeneralEventLoop.exit)
            self.GeneralEventLoop.exec_()
        return

    ## @brief StepperWellpositioning(QObject)::goto_well(self, x_pos, y_pos) 
    # @todo implement function
    @Slot()
    def goto_wel(self, x_pos, y_pos):
        return

    ## @brief StepperWellpositioning(QObject)::firmwareRestart(self) is the slot function which restarts the firmware and reloads the printer.cfg file when the firmwarerestartbutton in the window is pressed.
    @Slot()
    def firmwareRestart(self):
        self.gcode_serial.executeGcode("FIRMWARE_RESTART\r\n")
        print(self.gcode_serial.readPort())
        return

    ## @brief StepperWellpositioning(QObject)::hoemX(self) is executed when homeX button is pressed in the MainWindow.
    @Slot()
    def homeX(self):
        self.gcode_serial.executeGcode(str(self.stepper_X.homeX()))
        print(self.gcode_serial.readPort())
        return
 
    ## @brief StepperWellpositioning(QObject)::homeX(self) is executed when the get position button is pressed in the main MainWindow.
    # It retrieves the position from the STM microcontroller with G-code command M114.
    @Slot()
    def getPosition(self):
        self.gcode_serial.executeGcode("M114\r\n")
        print(self.gcode_serial.readPort())
        self.msg("test signal message in getPos()")
        return

    ## @brief StepperWellpositioning(QObject)::turnUp(self) is executed when the turnUp button is pressed. It calls the execute function of Serial_Gcode which sends the move G-code to the STM.
    @Slot()
    def turnUp(self):
        self.gcode_serial.executeGcode(str(self.stepper_Y.turnUp()))
        return

    ## @brief StepperWellpositioning(QObject)::turnLeft(self) is executed when the turnLeft button is pressed. It calls the execute function of Serial_Gcode which sends the move G-code to the STM.
    @Slot()
    def turnLeft(self):
        self.gcode_serial.executeGcode(str(self.stepper_X.turnLeft()))
        return

    ## @brief StepperWellpositioning(QObject)::turnRight(self) is executed when the turnRight button is pressed. It calls the execute function of Serial_Gcode which sends the move G-code to the STM.
    @Slot()
    def turnRight(self):
        self.gcode_serial.executeGcode(str(self.stepper_X.turnRight()))
        return

    ## @brief StepperWellpositioning(QObject)::turnDown(self) is executed when the turnDown button is pressed. It calls the execute function of Serial_Gcode which sends the move G-code to the STM.
    @Slot()
    def turnDown(self):
        self.gcode_serial.executeGcode(str(self.stepper_Y.turnDown()))
        return

    ## @brief StepperWellpositioning(QObject)::gotoXY(self, posX, posY) is executed when the goto XY button is pressed. It calls the execute function of Serial_Gcode which sends the move G-code to the STM.
    # @param posX is the desired X position retrieved from the MainWindow user input.
    # @param posY is the desired Y position retrieved from the MainWindow user input.
    @Slot()
    def gotoXY(self, posX, posY):        
        #self.msg("Goto X, Y: " + str(posX) + ", " + str(posY))
        self.gcode_serial.executeGcode("G0 X" + str(posX) + " Y" + str(posY) + "\r\n")
        self.stepper_X.setPosition(posX)
        self.stepper_Y.setPosition(posY)
        return

    ## @brief StepperWellpositioning(QObject)::emergencyBreak(self) is executed when the emergency break button is pressed. It stops all motors and puts the STM microcontroller in shutdown. A firmware_restart is necessary to restart the software.
    @Slot()
    def emergencyBreak(self):
        print("in function Wellpositioning::emergencyBreak(self)")
        self.gcode_serial.executeGcode("M112\r\n")
        return


