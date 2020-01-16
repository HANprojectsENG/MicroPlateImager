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
    move_confirmed = False
    homing_confirmed = False
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

    ## @brief StepperControl(QObject)::wait_ms(self, milliseconds) is a delay function.
    ## @param milliseconds is the number of milliseconds to wait.
    def wait_ms(self, milliseconds):
        GeneralEventLoop = QEventLoop()
        QTimer.singleShot(milliseconds, GeneralEventLoop.exit)
        GeneralEventLoop.exec_()
        return

    def getPositionFromSTM(self):
        if self.PrintHAT_serial.getConnectionState():
            #self.msg("Retrieving position from STM microcontroller...")
            gcode_string = "M114\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
            #self.PrintHAT_serial.readPort()
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

    @Slot()
    def setConfirms(self):
        self.move_confirmed = True
        return

    ## @brief StepperControl::homeXY(self) creates and executes a homing G-code string for the X-axis.
    def homeXY(self):
        read = str
        confirmation = 'ok'
        triggered = 'still triggered'
        if self.PrintHAT_serial.getConnectionState():
            self.msg("Homing X and Y axis")
            gcode_string = "G28 X0 Y0\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
            
            self.homing_confirmed = False
            read = str(self.PrintHAT_serial.readPort())
            while (read.find(confirmation, 0, len(read)) <= 0) and (read.find(triggered, 0, len(read)) <= 0):
                read = str(self.PrintHAT_serial.readPort())
                ## Manually confirmed somewhere in software
                if self.homing_confirmed is True:
                    self.msg("Homing manually confirmed in software")
                    break
            
                if read.find(confirmation, 0, len(read)) >= 0:
                    self.msg("Homing confirmed by STM")
                    self.homing_confirmed = True

                if read.find(triggered, 0, len(read)) >= 0:
                    self.msg("Homing failed")
                    self.homing_confirmed = False
                
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
        read = str
        confirmation = 'ok'
        if self.PrintHAT_serial.getConnectionState():
            gcode_string = "G0 X" + str(x_pos) + " Y" + str(y_pos) + "\r\n"
            wait_for_finishing = "M400\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
            self.PrintHAT_serial.executeGcode(wait_for_finishing)
            self.signals.well_unknown.emit()
            self.move_confirmed = False
            read = str(self.PrintHAT_serial.readPort())
            while (read.find(confirmation, 0, len(read)) <= 0):
                print("Waiting for gotoXY move confirmation")
                read = str(self.PrintHAT_serial.readPort())
                if read.find(confirmation, 0, len(read)) >= 0:
                    self.msg("Move confirmed by STM")
                    self.move_confirmed = True
                ## If manually confirmed somewhere in software
                if self.move_confirmed is True:
                    break    
            
            self.setPositionX(x_pos)
            self.setPositionY(y_pos)
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return 

    ## @brief StepperControl::moveToWell(self, column, row) creates and executes a move G-code string for the XY-axis
    ## @note Difference between moveToWell(self, column, row) and gotoXY(self, x_pos, y_pos) is that this function raises the manual movement signal which causes to set the current well to None.
    ## @param column is the desired X-position
    ## @param row is the desired Y-position
    def moveToWell(self, column, row):
        print("in functionStepperControl::gotoTargetWell")
        self.move_confirmed = False
        read = str
        confirmation = 'ok'
        if self.PrintHAT_serial.getConnectionState():
            gcode_string = "G0 X" + str(column) + " Y" + str(row) + "\r\n"
            wait_for_finishing = "M400\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
            self.PrintHAT_serial.executeGcode(wait_for_finishing)

            read = str(self.PrintHAT_serial.readPort())
            while (read.find(confirmation, 0, len(read)) <= 0) and self.move_confirmed is False:
                print("Waiting for moveToWell move confirmation")
                read = str(self.PrintHAT_serial.readPort())
                ## If manually confirmed somewhere in software
                if self.move_confirmed is True:
                    self.msg("Move to well manually confirmed in software")
                    break  
                if read.find(confirmation, 0, len(read)) >= 0:
                    self.msg("Move confirmed by STM")
                    self.move_confirmed = True
                    break  

            self.setPositionX(column)
            self.setPositionY(row)
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return 

    ## @brief StepperControl::turnUp(self) creates and executes a move G-code string for the Y-axis. Each call results in a fixed distance movement.
    def turnUp(self):
        print("in function StepperControl::turnUp()")
        if self.PrintHAT_serial.getConnectionState():
            self.signals.well_unknown.emit()
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
            self.signals.well_unknown.emit()
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
            self.signals.well_unknown.emit()
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
            self.signals.well_unknown.emit()
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
    
    ## @todo commenting
    ## @author Robin Meekers
    ## @author Gert van Lagen (ported to new prototype with PrintHAT)
    @Slot()
    def goto_well(self, row, column):
        self.signals.process_active.emit()
        self.Stopped = False
        if self.WPE is None:
            ## define the resolution of the received images to be entered into the evaluator.
            self.snapshot_request()
            self.snapshot_await()
            self.WPE_target = (int(self.image.shape[1] / 2), int(self.image.shape[0] / 2))
            self.WPE = imageProcessor.WellPositionEvaluator((self.image.shape[0], self.image.shape[1]))

        self.msg("current well: " + str(self.get_current_well()))
        current_row, current_column = self.get_current_well()
        
        if current_row is None or current_column is None:
            ## Need to go to home position first
            self.msg("Current position unknown. Moving to home...")
            self.stepper_control.homeXY()

            if self.stepper_control.homing_confirmed is True:
                self.msg("Requesting second snapshot after homing confirmation")
                self.image = None
                self.snapshot_request()
                self.snapshot_await()
                self.wait_ms(1000) ## Wait for the snapshot to be stored in self.image
                
                ## Arrived at home, move to first well.
                ## The exact centre of the image can more easily be determined at the home position,
                ## as there is no distortion in the image by light refracting.
                self.msg("Looking for light source...")
                WPE_Error = self.WPE.evaluate(self.image, (int(self.image.shape[1] / 2), int(self.image.shape[0] / 2)))
                self.msg("Found light-source at: (" + str(WPE_Error[0][0]) + " | " + str(WPE_Error[0][1]) + "). Radius: " + str(WPE_Error[2]))
                
                self.WPE_targetRadius = WPE_Error[2]
                self.WPE_target = (int(self.image.shape[1] / 2) + WPE_Error[0][0], int(self.image.shape[0] / 2) + WPE_Error[0][1])
                
                self.signals.target_located.emit((self.WPE_target[0], self.WPE_target[1], self.WPE_targetRadius))
                
                self.WPE.circle_minRadius = int(self.WPE_targetRadius * 0.8) ## Roughly the amount remaining if the target is on the edge between wells.
                self.WPE.circle_maxRadius = int(self.WPE_targetRadius) ## The well can never be larger than the diaphragm of the light source.
                
                self.stepper_control.moveToWell(column, row)
                self.set_current_well(column, row)
                self.wait_ms(2000) ## First move (from home position) is the biggest, so too early evaluation, due to fast confirmation response of the PrintHAT STM, could result in a targetcircle placed on the light source.
                self.signals.first_move.emit()
                ## Arrived at location, use machine vision to correct position if necessary.
                if not self.goto_target():
                    self.msg("Well positioning not succeeded.")
                    self.set_current_well(None, None) ## Never reached reference point
                    self.Stopped = True
                    self.signals.process_inactive.emit()
                    self.stepper_control.move_confirmed = True ## Manual confirmation needed. STM is to fast for the software to catch the last confirmation.
                    return False
                else:
                    self.msg("Well positioning succeeded.")
                    self.set_current_well(column, row)
                    self.stepper_control.move_confirmed = True ## Manual confirmation needed. STM is to fast for the software to catch the last confirmation.
        ## position known 
        else:
            self.stepper_control.moveToWell(column, row)
            self.set_current_well(column, row)
            if not self.goto_target():
                self.msg("Well positioning not succeeded.")
                self.set_current_well(None, None) ## Never reached reference point
                self.Stopped = True
                self.signals.process_inactive.emit()
                self.stepper_control.move_confirmed = True ## Manual confirmation needed. STM is to fast for the software to catch the last confirmation.
                return False
            else:
                self.msg("Well positioning succeeded.")
                self.set_current_well(column, row)
                self.stepper_control.move_confirmed = True ## Manual confirmation needed. STM is to fast for the software to catch the last confirmation.

        if row != self.current_well_row or column != self.current_well_column:
            self.msg("moving from: (" + str(self.current_well_row) + " | " + str(self.current_well_column) + ") to: (" + str(row) + " | " + str(column) + ")")
        return True

    def goto_target(self):
        loops_ = 0
        error_count = 0
        WPE_Error = None
        controller_column_output=0
        controller_row_output=0

        while True:
            self.wait_ms(500)
            if self.stepper_control.move_confirmed is True:
                self.snapshot_request()
                WPE_Error = self.WPE.evaluate(self.image, self.WPE_target)
                if WPE_Error[1] <= 0: ## Possibly something wrong with captured frame, retry with another snapshot
                    self.msg("Possibly something wrong with captured frame, retry with another snapshot")
                    error_count = error_count + 1
                    if (error_count >=3):
                        self.msg("Error_count = " + str(error_count))
                        return False
                    continue
                else:
                    self.msg("Well found at (" + str(WPE_Error[0][0]) + " | " + str(WPE_Error[0][1]) + ")")
                    self.signals.well_located.emit((self.WPE_target[0]+WPE_Error[0][0], self.WPE_target[1]+WPE_Error[0][1], WPE_Error[2]))
                    error_count = 0
                    if (abs(WPE_Error[0][0]) < (self.image.shape[0] / 120) and abs(WPE_Error[0][1]) < (self.image.shape[0] / 120)) or (loops_ >15): ## No more adjustments to make or system is oscilating
                        #if loops_ > 15: ## Check if image is still of reasonable quality.
                            #self.msg("More than 15 correction loops")
                    #        if (WPE_Error[1] < int(self.image_area*0.55) or abs(WPE_Error[0][1]) >= (self.image.shape[0] / 60) or abs(WPE_Error[0][1]) >= (self.image.spahe[0] / 60)):
                    #            ## Found circle covers less than 40% of the image or to far off.
                    #            self.msg("Found circle covers less than 40 percent of the image or to far off.")
                            #return True ## should be false in the end software
                        self.msg("Returning from positioner controller, loops: " + str(loops_))
                        return True
                ## Position correction calculation and execution
                if abs(WPE_Error[0][0]) >= (self.image.shape[0] / 120):
                    controller_column_output = float(WPE_Error[0][0]/50)
                else:
                    controller_column_output = 0
                if abs(WPE_Error[0][1]) >= (self.image.shape[0] / 120):
                    controller_row_output = (float(WPE_Error[0][1]/50))
                else:
                    controller_row_output = 0
                #self.msg("controller_column_output: " + str(controller_column_output))
                #self.msg("controller_row_output: " + str(controller_row_output))
                column, row = self.get_current_well()

                if abs(WPE_Error[0][0]) >= (self.image.shape[0] / 120) or abs(WPE_Error[0][1]) >= (self.image.shape[0] / 120):
                    self.stepper_control.moveToWell((float(column)+float(controller_column_output)), (float(row) + float(controller_row_output)))
                else:
                    break
                loops_ = loops_ + 1
            else:
                print("Waiting for move confirmation in goto_target function")
                #return False
        return True

    ## @todo substitude this function into goto_well(self, row, column)
    def snapshot_request(self):
            self.signals.snapshot_requested.emit(str((1,1)))

    def snapshot_await(self):
        self.SnapshotTaken = False
        while not self.Stopped and not self.SnapshotTaken:
            self.SnapshotEventLoop = QEventLoop()
            QTimer.singleShot(10, self.SnapshotEventLoop.exit)
            self.SnapshotEventLoop.exec_()

    @Slot(np.ndarray)
    def snapshot_confirmed(self, snapshot):
        self.image = snapshot
        self.WPE_target = (int(self.image.shape[1] / 2), int(self.image.shape[0] / 2))
        self.image_area = int((self.image.shape[0]*self.image.shape[1]))
        self.SnapshotTaken = True
        if not (self.SnapshotEventLoop is None):
            self.SnapshotEventLoop.exit()