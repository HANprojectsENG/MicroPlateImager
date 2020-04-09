## @package stepper.py
## @brief stepper.py contains classes for stepper motor control, G-code string creation, homing and well positioning.
## @author Gert van Lagen

import main
import motor_control.serial_printhat as serial_printhat
import lib.imageProcessor as imageProcessor
import lib.signal as signal
import numpy as np
import math
import os
import sys
import cv2
from PySide2.QtCore import QTimer, Signal, Slot, QEventLoop, QObject, QSettings, QThread
import time

current_milli_time = lambda: int(round(time.time() * 1000))

## @brief StepperControl contains steppermotor specific information and creates G-code strings when called specific functions like turnRight().
## @author Gert van Lagen
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
            gcode_string = "M114\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)
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
        return

    ## @brief StepperControl::setPositionY(self) sets the position of the Y-axis
    ## @param y_pos is the new position of the Y-axis which is set.  
    def setPositionY(self, y_pos):
        self.position_y = float(y_pos)
        return        

    @Slot()
    def setMoveConfirmed(self):
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
                #print("Waiting for gotoXY move confirmation")
                read = str(self.PrintHAT_serial.readPort())
                if read.find(confirmation, 0, len(read)) >= 0:
                    #self.msg("Move confirmed by STM")
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
        print("StepperControl::moveToWell thread check: " + str(QThread.currentThread()))
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
                #print("Waiting for moveToWell move confirmation")
                read = str(self.PrintHAT_serial.readPort())
                ## If manually confirmed somewhere in software
                if self.move_confirmed is True:
                    #self.msg("Move to well manually confirmed in software")
                    break  
                if read.find(confirmation, 0, len(read)) >= 0:
                    #self.msg("Move confirmed by STM")
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
        self.signals.process_inactive.emit() ## Stops current batch process if running
        return

    @Slot(float)
    def setLightPWM(self, val):
        ''' Set PrintHAT light output pin to PWM value.
            Args:
                val (float): PWM dutycycle, between 0.0 and 1.0.
            Raises:
            Returns:
        '''
        print("in function Steppercontrol::setLightPWM(self, val)")
        if self.PrintHAT_serial.getConnectionState():
            gcode_string = "SET_PIN PIN=light VALUE=" + str(val) + "\r\n"
            self.PrintHAT_serial.executeGcode(gcode_string)        
        else:
            self.msg("DEBUG: No serial connection with STM microcontroller. Restart the program.")
        return 

## @brief StepperWellPositioning(QObject) takes care of the positioning of the wells under the camera.
## @author Gert van Lagen
## @author Robin Meekers (StepperWellPositioning::goto_well, StepperWellPositioning::goto_target, StepperWellPositioning::snapshot*)
## @author Jeroen Veen added light control    
class StepperWellPositioning():
    signals = signal.signalClass()
    process_activity = False
    stepper_control = None ## object StepperControl instance
    current_well_row = None
    current_well_column = None
    Stopped = True
    GeneralEventLoop = None
    SnapshotEventLoop = None
    SnapshotTaken = False
    image = np.ndarray
    image_area = None
    WPE = None
    WPE_target = None
    WPE_targetRadius = None
    Well_Map = None
    log_fine_tuning = True

    ## @brief StepperWellPositioning()::__init__ initialises the stepper objects for X and Y axis and initialises the gcodeSerial to the class member variable.
    ## @param steppers is the StepperControl object representing the X- and Y-axis
    ## @param Well_data contains the target well specified by the user in the batch.ini file
    def __init__(self, steppers, Well_data):
        self.stepper_control = steppers
        self.Well_Map = Well_data
        return

    ## @brief StepperWellPositioning()::msg emits the message signal. This emit will be catched by the logging slot function in main.py.
    ## @param message is the string message to be emitted.
    @Slot(str)
    def msg(self, message):
        if message is not None:
            self.signals.mes.emit(self.__class__.__name__ + ": " + str(message))
        return

    ## @brief StepperWellPositioning()::reset_current_well(self) sets the current well position (XY) to None
    def reset_current_well(self):
        self.set_current_well(None, None)
        return

    ## @brief StepperWellPositioning()::set_current_well(self) sets the current well position.
    ## @param column is the column or x well coordinate
    ## @param row is the row or y well coordinate
    def set_current_well(self, column, row):
        self.current_well_column = column
        self.current_well_row = row
        return
        
    ## @brief StepperWellPositioning()::get_current_well(self) is the well position getter.
    ## @return current_well_column (x position in mm from home) and current_well_row (y position in mm from home).
    def get_current_well(self):
        if self.current_well_column == None or self.current_well_row == None:
            self.current_well_column = None
            self.current_well_row = None
        return self.current_well_column, self.current_well_row

    ## @brief StepperWellPositioning()::wait_ms(self, milliseconds) is a delay function.
    ## @param milliseconds is the number of milliseconds to wait.
    def wait_ms(self, milliseconds):
        GeneralEventLoop = QEventLoop()
        QTimer.singleShot(milliseconds, GeneralEventLoop.exit)
        GeneralEventLoop.exec_()
        return
    
    ## @brief StepperWellPositioning()::goto_well(self, row, column): 
    ## @author Robin Meekers
    ## @author Gert van Lagen (ported to new prototype which makes use of the Wrecklab PrintHAT)
    @Slot()
    def goto_well(self, row, column):
        print("In goto_well function")
        self.signals.process_active.emit()
        self.Stopped = False
        self.stepper_control.setLightPWM(1.0)

        ## If the Well Position Evaluator is not initialized.
        if self.WPE is None:
            ## define the resolution of the received images to be entered into the evaluator.
            self.snapshot_request()
            self.snapshot_await()
            self.WPE_target = (int(self.image.shape[1] / 2), int(self.image.shape[0] / 2))
            self.WPE = imageProcessor.WellPositionEvaluator((self.image.shape[0], self.image.shape[1]))

        self.msg("Current well: " + str(self.get_current_well()))
        current_row, current_column = self.get_current_well()
        
        ## Position unknown
        if current_row is None or current_column is None:
            ## Need to go to home position first
            self.msg("Current position unknown. Moving to home...")
            self.stepper_control.homeXY()

            ## If homing is succeeded and confirmed by the STM of the Wrecklab PrintHAT
            if self.stepper_control.homing_confirmed is True:
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
                self.msg("WPE_target: " + str(self.WPE_target[0]) + " | " + str(self.WPE_target[1]))
                
                self.signals.target_located.emit((self.WPE_target[0], self.WPE_target[1], self.WPE_targetRadius))
                
                self.WPE.circle_minRadius = int(self.WPE_targetRadius * 0.8) ## Roughly the amount remaining if the target is on the edge between wells.
                self.WPE.circle_maxRadius = int(self.WPE_targetRadius) ## The well can never be larger than the diaphragm of the light source.
                
##                ## Homing succeeded, light source found, lets move to the first target of Well_map
##                self.set_current_well(column, row)
##                self.stepper_control.moveToWell(column, row)
                self.signals.first_move.emit()
            else:
                return False
       
        ## position known 
        if self.process_activity is True:

            # JV: column and row is probablyX and Y in Robin's functions, also in Gert's functions?
            self.stepper_control.moveToWell(column, row)
            
            ## Wait for ms depending on moving distance, JV:why?
            if self.current_well_column is None or self.current_well_row is None:
                dist = 50
            else:
                dist = math.sqrt(float(abs(float(column)-float(self.current_well_column)) * abs(float(column)-float(self.current_well_column))) + float(abs(float(row)-float(self.current_well_row)) * abs(float(row)-float(self.current_well_row))))
            self.msg("Moving distance: " + str(dist))
            if dist < 20:
                self.msg("Delay: 1000ms | dist: " + str(dist) + "mm")
                self.wait_ms(1000)
            elif dist < 50:
                self.msg("Delay: 3000ms | dist: " + str(dist) + "mm")
                self.wait_ms(3000)
            elif dist > 50 and dist < 70:
                self.msg("Delay: 5000ms | dist: " + str(dist) + "mm")
                self.wait_ms(5000)
            elif dist > 70 and dist < 85:
                self.msg("Delay: 8000ms | dist: " + str(dist) + "mm")
                self.wait_ms(8000)
            elif dist > 85:
                self.msg("Delay: 11000ms | dist: " + str(dist) + "mm")
                self.wait_ms(11000)
            else:
                self.msg("Delay: 4000ms | Unknown dist: " + str(dist) + "mm")
                self.wait_ms(4000)
            
            self.set_current_well(column, row)

            if not self.goto_target():
                self.msg("Well positioning not succeeded.")
                self.set_current_well(None, None) ## Never reached reference point
                self.Stopped = True
                self.signals.process_inactive.emit()

                ## Manual confirmation needed. STM is too fast for the software to catch the last confirmation.
                self.stepper_control.move_confirmed = True 
                return False
            else:
                self.msg("Well positioning succeeded.")
                ## Manual confirmation needed. STM is too fast for the software to catch the last confirmation.
                self.stepper_control.move_confirmed = True

        else:
            print("Positioning process inactive, cannot call goto_target positioning controller function.")
            self.msg("Positioning process inactive, cannot call goto_target positioning controller function.")
        ## Different row?
        if row != self.current_well_row or column != self.current_well_column:
            self.msg("moving from: (" + str(self.current_well_row) + " | " + str(self.current_well_column) + ") to: (" + str(row) + " | " + str(column) + ")")
            
        self.stepper_control.setLightPWM(0.0)
        return True

    ## @brief StepperWellPositioning()::goto_target(self) evaluates the target circle using class Well_Position_Evaluator, updates the snapshot, 
    ## and corrects the position of the well while not aligned with the light source.
    def goto_target(self):
        loops_ = 0
        error_count = 0
        WPE_Error = None
        new_column = 0
        new_row = 0
        error_threshold = 200#50#120 # higher number means lower error...

        if self.log_fine_tuning:
            column, row = self.get_current_well()
            run_start_time = current_milli_time()
            recording_file_name = os.path.sep.join([os.getcwd(),'goto_target_' + str(round(column)) + '_' + str(round(row)) + '_' + str(run_start_time) + '.csv'])
            recording_file = open(recording_file_name, "w")
            record_str = "run_time, WPE_target[0], WPE_target[1], WPE_Error[0][0], WPE_Error[0][1]" 
            recording_file.write(record_str + "\n")
        else:
            recording_file = None
        
        ## Do while the well is not aligned with the light source. 
        while True:
            if (self.stepper_control.move_confirmed is True):
                if self.process_activity is False:
                    #self.msg("!Returning from alignment controller loop in StepperWellPositioning::goto_target")
                    print("!Returning from alignment controller loop in StepperWellPositioning::goto_target")
                    return False
                ## Wait for image to stabilize and request new snapshot
                self.wait_ms(2000)
                self.snapshot_request()
                
                ## Wait for snapshot to be stored in self.image
                self.wait_ms(1000) 

                ## Evaluate current wellposition relative to the light source.
                WPE_Error = self.WPE.evaluate(self.image, self.WPE_target)
                self.msg("WPE target at (" + str(self.WPE_target[0]) + " | " + str(self.WPE_target[1]) + ")")

                ## Area error, surface smaller or equal to 0
                if WPE_Error[1] <= 0:
                    self.msg("Possibly something wrong with captured frame, retry with another snapshot")
                    error_count = error_count + 1
                    if (error_count >=3):
                        self.msg("Error_count = " + str(error_count))
                        return False
                    continue
                else:
                    self.msg("Well found at offset (" + str(WPE_Error[0][0]) + " | " + str(WPE_Error[0][1]) + ")")
                    self.signals.well_located.emit((self.WPE_target[0]+WPE_Error[0][0], self.WPE_target[1]+WPE_Error[0][1], WPE_Error[2]))

#                     ## Some 
#                     error_count = 0
#                     if (abs(WPE_Error[0][0]-30) < (self.image.shape[0] / error_threshold) and abs(WPE_Error[0][1]+30) < (self.image.shape[0] / error_threshold)) or (loops_ >20): ## No more adjustments to make or system is oscilating
#                         if loops_ > 20:loops_
#                             self.msg("More than 20 correction loops, return False")
#                             return False
#                         self.msg("Returning from positioner controller, loops: " + str(loops_))
#                         return True

                ## Define controller variables for column and row | x and y.
                # Don't know resolution [px/mm] so just guess a step and lower on each step
                new_column = float(WPE_Error[0][0]) / ((loops_+1)*20.0)
                new_row = float(WPE_Error[0][1]) / ((loops_+1)*15.0)
                column, row = self.get_current_well()

                run_time = current_milli_time()-run_start_time
                if recording_file:
                    record_str = str(run_time) + ',' + str(self.WPE_target[0]) + ',' + str(self.WPE_target[1]) + ',' + str(WPE_Error[0][0]) + ',' + str(WPE_Error[0][1]) 
                    recording_file.write(record_str + "\n")                
                
                ## if the error values or column and row are larger or equal to 1/120th of the image height. 
                ## @note Detection software returned incorrect error. Solved by the small offset (-30 for the column, +30 for the row) added to the error value. 
#                 if abs(WPE_Error[0][0]-30) >= (self.image.shape[0] / error_threshold) or abs(WPE_Error[0][1]+30) >= (self.image.shape[0] / error_threshold):
                if abs(WPE_Error[0][0]) >= (self.image.shape[1] / error_threshold) or abs(WPE_Error[0][1]) >= (self.image.shape[0] / error_threshold):
                    ## @note A small offset had to be added by the column and row controller variables as well
                    new_column += column # float(column)-float(new_column)
                    new_row += row # float(row) - float(new_row)
                    new_column = round(new_column,1)
                    new_row = round(new_row,1)
                    self.stepper_control.moveToWell(new_column, new_row)
                    self.set_current_well(new_column, new_row)
                else:
                    break
                loops_ += 1
                if loops_ > 20:
                    self.msg("More than 20 correction loops, return False")
                    return False
            if self.process_activity is False:
                #self.msg("Returning from alignment controller loop in StepperWellPositioning::goto_target")
                print("Returning from alignment controller loop in StepperWellPositioning::goto_target")
                return False
            
        if recording_file:
            recording_file.close()                
          
        return True

    ## @brief StepperWellPositioning()::snapshot_request(self) emits the snapshot_request signal
    def snapshot_request(self):
            self.signals.snapshot_requested.emit(str((1,1)))

    ## @brief StepperWellPositioning()::snapshot_awiat(self) runs an eventloop while the new snapshot is not stored in self.image yet.
    def snapshot_await(self):
        self.SnapshotTaken = False
        while not self.Stopped and not self.SnapshotTaken:
            self.SnapshotEventLoop = QEventLoop()
            QTimer.singleShot(10, self.SnapshotEventLoop.exit)
            self.SnapshotEventLoop.exec_()

    ## @brief StepperWellPositioning()::snapshot_confirmed(self, snapshot) exits the event loop of snapshot_await when the new image is arived. 
    ## It updates the self.image variable with the new variable and defines the image area and WPE_target. 
    @Slot(np.ndarray)
    def snapshot_confirmed(self, snapshot):
        self.image = snapshot
#         self.WPE_target = (int(self.image.shape[1] / 2), int(self.image.shape[0] / 2))
        self.image_area = int((self.image.shape[0]*self.image.shape[1]))
        self.SnapshotTaken = True
        if not (self.SnapshotEventLoop is None):
            self.SnapshotEventLoop.exit()
        return
    
    ## @brief StepperWellPositioning()::setProcessInactive(self) disables the positionings process if the signal is emitted.
    @Slot()
    def setProcessInactive(self):
        #self.msg("Disabled positioning process activity")
        print("Disabled positioning process activity")
        self.process_activity = False
        self.Stopped = True
        if not (self.GeneralEventLoop is None):
            self.GeneralEventLoop.exit()
            #self.msg("Exit StepperWellPositioning::GeneralEventloop")
            print("Exit StepperWellPositioning::GeneralEventloop")
        if not (self.SnapshotEventLoop is None):
            self.SnapshotEventLoop.exit()
            #self.msg("Exit StepperWellPositioning::SnapshotEventLoop")
            print("Exit StepperWellPositioning::SnapshotEventLoop")
        return

    ## @brief StepperWellPositioning()::setProcessActive(self) enables the positionings process if the signal is emitted.
    @Slot()
    def setProcessActive(self):
        self.process_activity = True
        self.Stopped = False
        return

    @Slot()
    def close(self):
        self.stepper_control.setLightPWM(0.0)        
        self.process_activity = False
        self.Stopped = True
        return
