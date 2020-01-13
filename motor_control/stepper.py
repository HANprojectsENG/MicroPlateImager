## @package stepper.py
## @brief stepper.py contains classes for stepper motor control, G-code string creation, homing and well positioning.
## @author Gert van Lagen

import main
import motor_control.serial_printhat as serial_printhat
import lib.imageProcessor as imageProcessor
import lib.signal as signal
import numpy as np
import os
import cv2
from PySide2.QtCore import QTimer, Signal, Slot, QEventLoop, QObject, QSettings

## @brief StepperControl contains steppermotor specific information and creates G-code strings when called specific functions like turnRight().
class StepperControl():
    signals = signal.signalClass()
    PrintHAT_serial = serial_printhat.GcodeSerial()

    ## @brief StepperControl::__init__(self) sets the motor position instance variable to zero.
    def __init__(self):
         ## @param position_x is the x-coordinate in mm of the wellplate reader measured from the homeposition
         self.position_x = 0

         ## @param position_y is the y-coordinate in mm of the wellplate reader measured from the homeposition
         self.position_y = 0

    ## @brief StepperControl::msg(self, message) emits the message signal. This emit will be catched by the logging slot function in main.py.
    ## @param message is the string message to be emitted.
    def msg(self, message):
        if message is not None:
            self.signals.mes.emit(self.__class__.__name__ + ": " + str(message))
        return

    def getPositionFromSTM(self):
        if self.PrintHAT_serial.getConnectionState():
            self.msg("Retrieving position from STM microcontroller...")
            gcode_string = "M114\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
            self.PrintHAT_serial.readPort()
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return

    ## @brief StepperControl::getPositionX(self) returns the position of the X stepper
    ## @return position_x of the stepper motors
    def getPositionX(self):
        return float(self.position_x)

    ## @brief StepperControl::getPositionY(self) returns the position of the Y stepper
    ## @return position_y of the stepper motors
    def getPositionY(self):
        return float(self.position_y)

    ## @brief StepperControl::setPositionX(self) sets the position of the X-axis
    ## @param x_pos is the new position of the X-axis which is set.
    def setPositionX(self, x_pos):
        self.position_x = float(x_pos)
        #self.msg("New XY-position: " + str(self.position_x) + ", " + str(self.position_y))
        return

    ## @brief StepperControl::setPositionY(self) sets the position of the Y-axis
    ## @param y_pos is the new position of the Y-axis which is set.  
    def setPositionY(self, y_pos):
        self.position_y = float(y_pos)
        #self.msg("New XY-position: " + str(self.position_x) + ", " + str(self.position_y))
        return        

    ## @brief StepperControl::homeX(self) creates and executes a homing G-code string for the X-axis.
    def homeXY(self):
        if self.PrintHAT_serial.getConnectionState():
            self.msg("Homing X and Y axis")
            gcode_string = "G28 X0 Y0\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
            self.setPositionX(0)
            self.setPositionY(0)
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return

    ## @brief StepperControl::gotoX(self, pos) creates and executes a move G-code string for the X-axis.
    ## @param x_pos is the desired position
    ## @depricated this function is not in use
    def gotoX(self, x_pos):
        if self.PrintHAT_serial.getConnectionState():
            gcode_string = "G0 X" 
            gcode_string += str(x_pos)
            gcode_string += "\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
            self.setPositionX(x_pos)
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return 

    ## @brief StepperControl::gotoY(self, pos) creates and executes a move G-code string for the Y-axis.
    ## @param y_pos is the desired position
    ## @depricated this function is not in use
    def gotoY(self, y_pos):
        if self.PrintHAT_serial.getConnectionState():
            gcode_string = "G0 Y" 
            gcode_string += str(y_pos)
            gcode_string += "\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
            self.setPositionY(y_pos)
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return 

    ## @brief StepperControl::gotoXY(self, x_pos, y_pos) creates and executes a move G-code string for the XY-axis
    ## @param x_pos is the desired X-position
    ## @param y_pos is the desired Y-position
    def gotoXY(self, x_pos, y_pos):
        print("in functionStepperControl::gotoXY")
        if self.PrintHAT_serial.getConnectionState():
            gcode_string = "G0 X" + str(x_pos) + " Y" + str(y_pos) + "\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
            self.setPositionX(x_pos)
            self.setPositionY(y_pos)
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return 

    ## @brief StepperControl::turnUp(self) creates and executes a move G-code string for the Y-axis. Each call results in a fixed distance movement.
    def turnUp(self):
        print("in function StepperControl::turnUp()")
        if self.PrintHAT_serial.getConnectionState():
            newPosition = self.getPositionY()
            newPosition +=1
            self.setPositionY(newPosition)
            gcode_string = "G0 Y"
            gcode_string += str(self.getPositionY())
            gcode_string += "\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return 

    ## @brief StepperControl::turnLeft(self) creates and executes a move G-code string for the X-axis. Each call results in a fixed distance movement.
    def turnLeft(self):
        print("in function StepperControl::turnLeft()")
        if self.PrintHAT_serial.getConnectionState():
            if self.getPositionX() > 0:
                newPosition = self.getPositionX()
                newPosition -=1
                self.setPositionX(newPosition)
                gcode_string = "G0 X"
                gcode_string += str(self.getPositionX())
                gcode_string += "\r\n"
                self.PrintHAT_serial.executeGcode(gcode_string)
            else:
                self.msg("You try to move beyond the minimum X position. X position is: " + str(self.getPositionX()))
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return

    ## @brief StepperControl::turnRight(self) creates and executes a move G-code string for the X-axis. Each call results in a fixed distance movement.
    def turnRight(self):
        print("in function StepperControl::turnRight()")
        if self.PrintHAT_serial.getConnectionState():
            newPosition = self.getPositionX()
            newPosition +=1
            self.setPositionX(newPosition)
            gcode_string = "G0 X"
            gcode_string += str(self.getPositionX())
            gcode_string += "\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return

    ## @brief StepperControl::turnDown(self) creates and executes a move G-code string for the Y-axis. Each call results in a fixed distance movement.
    def turnDown(self):
        print("in function StepperControl::turnDown()")
        if self.PrintHAT_serial.getConnectionState():
            if self.getPositionY() > 0:
                newPosition = self.getPositionY()
                newPosition -=1
                self.setPositionY(newPosition)
                gcode_string = "G0 Y"
                gcode_string += str(self.getPositionY())
                gcode_string += "\r\n"
                self.PrintHAT_serial.executeGcode(gcode_string)
            else:
                self.msg("You try to move beyond the minimum Y position. Y position is: " + str(self.getPositionY()))
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return

    ## @brief StepperControl::firmwareRestart(self) restarts the firmware and reloads the config in the klipper software.
    def firmwareRestart(self):
        print("in function StepperControl::firmwareRestart(self)")
        gcode_string = "FIRMWARE_RESTART\r\n"
        self.PrintHAT_serial.executeGcode(gcode_string)
        return

    ## @brief StepperControl::emergencyBreak(self) stops all motors and shuts down the STM microcontroller. A firmware restart command is necessary to restart the system.
    def emergencyBreak(self):
        print("in function Steppercontrol::emergencyBreak(self)")
        gcode_string = "M112\r\n"
        self.msg("Emergency break! Restart the firmware usingn the button FIRMWARE_RESTART")
        self.PrintHAT_serial.executeGcode(gcode_string)
        return

## @brief StepperWellPositioning(QObject) takes care of the positioning of the wells under the camera.
## @param QObject is used to be able to use QObject
## @todo check if param QObject is necessary or if class signalClass() solves the QObject inheritance already.
class StepperWellPositioning():
    signals = signal.signalClass()
    stepper_control = None ## object MotorControl class
    current_well_row = None
    current_well_column = None
    Well_Map = None
    Stopped = True
    GeneralEventLoop = None
    SnapshotEventLoop = None
    SnapshotTaken = False
    image = np.ndarray
    image_area = None
    WPE = None
    WPE_target = None
    WPE_targetRadius = None

    ## @brief StepperWellPositioning(QObject)::__init__ initialises the stepper objects for X and Y axis and initialises the gcodeSerial to the class member variable.
    ## @param steppers is the StepperControl object representing the X- and Y-axis
    def __init__(self, steppers, Well_data):
        self.stepper_control = steppers
        self.Well_Map = Well_data
        return

    ## @brief StepperWellPositioning(QObject)::msg emits the message signal. This emit will be catched by the logging slot function in main.py.
    ## @param message is the string message to be emitted.
    @Slot(str)
    def msg(self, message):
        if message is not None:
            self.signals.mes.emit(self.__class__.__name__ + ": " + str(message))
        return

    ## @brief StepperWellPositioning(QObject)::reset_current_well(self) sets the current well position (XY) to None
    def reset_current_well(self):
        self.set_current_well(None, None)
        return

    ## @brief StepperWellPositioning(QObject)::set_current_well(self) sets the current well position.
    ## @param column is the column or x well coordinate
    ## @param row is the row or y well coordinate
    def set_current_well(self, column, row):
        self.current_well_column = column
        self.current_well_row = row
        return
        
    ## @brief StepperWellPositioning(QObject)::get_current_well(self) is the well position getter.
    ## @return current_well_column and current_well_row, the XY well position coordinates
    def get_current_well(self):
        if self.current_well_column == None or self.current_well_row == None:
            self.current_well_column = None
            self.current_well_row = None
        return self.current_well_column, self.current_well_row

    ## @brief StepperWellPositioning(QObject)::wait_ms(self, milliseconds) is a delay function.
    ## @param milliseconds is the number of milliseconds to wait.
    def wait_ms(self, milliseconds):
        GeneralEventLoop = QEventLoop()
        QTimer.singleShot(milliseconds, GeneralEventLoop.exit)
        GeneralEventLoop.exec_()
        return
    
    ## @brief StepperWellPositioning(QObject)::goto_well(self, x_pos, y_pos) navigates to the desired well.
    ## @param row is the row at which the well is on the well plate. Changing the row affects the y-axis position.
    ## @param column is the column at which the well is on the well plate. Changing the row affects the x-axis position.
    ## @depricated goto_well(_old) is depricated. New version below
    @Slot()
    def goto_well_old(self, row, column):
        self.msg("goto_well at row " + str(row) + ", column:" + str(column))
        self.stepper_control.gotoXY(column, row)
        self.set_current_well(column, row)
        return

    @Slot()
    def goto_well(self, row, column):
        self.signals.process_active.emit()
        self.Stopped = False
        if self.WPE is None:
            ## define the resolution of the received images to be entered into the evaluator.
            self.snapshot_request()
            print(self.image)
            self.WPE_target = (int(self.image.shape[1] / 2), int(self.image.shape[0] / 2))
            self.WPE = imageProcessor.WellPositionEvaluator((self.image.shape[0], self.image.shape[1]))
        if row == 0 or column == 0: # don' t move to location, just evaluate the position.
            if not self.goto_target():
                self.set_current_well(None, None) # never reached reference point
                self.Stopped = True
                self.signal.process_inactive.emit()
                return False
            else:
                self.process_inactive.emit()
                return True
        else:
            ## self.msg("Attempting to move to: (" + str(row) + " | " + str(column) + ") at: (" + str(self.Well_Map[int(row)][1][0]) + " | " + str(self.Well_Map[1][int(column)][1]) + ").")
            self.msg("current well: " + str(self.get_current_well()))
            current_row, current_column = self.get_current_well()
            #if self.get_current_well() is None:
            if current_row is None or current_column is None:
                ## Need to go to home position first
                self.msg("Position is undefined. Moveing to home first")
                self.stepper_control.homeXY()
            
                ## Arrived at home, move to first well.
                ## The exact centre of the image can more easily be determined at the home position,
                ## as there is no distortion in the image by light refracting.
                ## Do note .shape[1] is ??row, .shape[0] is ??column!
                self.snapshot_request()
                WPE_Error = self.WPE.evaluate(self.image, (int(self.image.shape[1] / 2), int(self.image.shape[0] / 2)))
                self.msg("Found light-source at: (" + str(WPE_Error[0][0]) + " | " + str(WPE_Error[0][1]) + "). Radius: " + str(WPE_Error[2]))
                self.WPE_targetRadius = WPE_Error[2]
                self.WPE_target = (int(self.image.shape[1] / 2) + WPE_Error[0][0], int(self.image.shape[0] / 2) + WPE_Error[0][1])
                self.signals.target_located.emit((self.WPE_target[0], self.WPE_target[1], self.WPE_targetRadius))
                self.WPE.circle_minRadius = int(self.WPE_targetRadius * 0.8) ## Roughly the amount remaining if the target is on the edge between wells.
                self.WPE.circle_maxRadius = int(self.WPE_targetRadius) ## The well can never be larger than the diaphragm of the light source.
                # goto well with ... mm for x and y axis using the Well_Map
                
                ## Arrived at location, use machine vision to correct position if necessary.
                if not self.goto_target():
                    self.set_current_well(None, None) ## Never reached reference point
                    self.Stopped = True
                    self.process_inactive.emit()
                    return False
                else:
                    self.set_current_well(1, 1)
        if row != self.current_well_row or column != self.current_well_column:
            self.msg("moving from: (" + str(self.current_well_row) + " | " + str(self.current_well_column) + ") to: (" + str(row) + " | " + str(column) + ")")
            ## calculate movement distance based on Well_Map
        return True

    def goto_target(self):
        return True

    ## @todo substitude this function into goto_well(self, row, column)
    def snapshot_request(self):
        self.signals.snapshot_requested.emit(str((1,1)))
        self.msg("Emitted snapshot request str((1, 1))")

    def snapshot_await(self):
        self.SnapshotTaken = False
        while not self.Stopped and not self.SnapshotTaken:
            self.SnapshotEventLoop = QEventLoop(self)
            QTimer.singleShot(10, self.SnapshotEventLoop.exit)
            self.SnapshotEventLoop.exec_()

    @Slot(np.ndarray)
    def snapshot_confirmed(self, snapshot):
        self.image = snapshot
        self.WPE_target = (int(self.image.shape[1] / 2), int(self.image.shape[0] / 2))
        self.msg("Snapshot confirmed")
        self.image_area = int((self.image.shape[0]*self.image.shape[1]))
        self.SnapshotTaken = True
        if not (self.SnapshotEventLoop is None):
            self.SnapshotEventLoop.exit()