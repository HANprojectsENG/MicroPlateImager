## @package batch_processor.py
## @brief the classes in batch_processor.py handle the batch process of the well plate reader
## @author Gert van Lagen (snapshot handle functions token from @author Robin Meekers)

import os
import sys
import time
import numpy as np
import lib.signal as signal
import motor_control.stepper as stepper

from PySide2.QtCore import Slot, QEventLoop, QTimer, QThread

current_milli_time = lambda: int(round(time.time() * 1000))

## @brief BatchProcessor() handles the batch process in which designated wells are photographed with the specified resolution, intervals and duration.
## @author Gert van Lagen (snapshot handle functions token from @author Robin Meekers)
class BatchProcessor():
    signals = signal.signalClass()
    GeneralEventLoop = None
    SnapshotEventLoop = None
    SnapshotTaken = False
    is_active = False
    well_positioner = None
    Well_Map = None
    Well_Targets = None
    ID = str
    info = str    
    duration = 0
    interleave = 0
    start_time = 0
    end_time = 0
    logging = True

    
    ## @brief BatchProcessor()::__init__ sets the batch settings
    ## @param well_controller is the well positioning class instance used to position the wells under the camera.
    ## @param well_map is the list of target wells with their positions in mm of both row and column.
    ## @param well_targets is the list of the target wells with their column and row index positions and ID.
    ## @param ID is the batch ID.
    ## @param info is the batch information.
    ## @param dur is the batch duration.
    ## @param interl is the time between the photographing of each well.
    def __init__(self, well_controller, well_map, well_targets, ID, info, path, dur, interl):
        #super().__init__()
        self.is_active = False
        self.well_positioner = well_controller
        self.Well_Map = well_map
        self.Well_Targets = well_targets
        self.batch_id = ID
        self.batch_info = info
        self.duration = dur
        self.interleave = interl
        self.path = os.path.sep.join([path, ID])
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        
    ## @brief BatchProcessor()::msg emits the message signal. This emit will be catched by the logging slot function in main.py.
    ## @param message is the string message to be emitted.
    @Slot(str)
    def msg(self, message):
        if message:
            self.signals.mes.emit(self.__class__.__name__ + ": " + str(message))
        return

    ## @brief BatchProcessor()::updateBatchSettings(self, well_data, ID, info, dur, interl) can be called to update the batch settings during runtime.
    ## @todo well_data update in MainWindow.
    ## @depricated, BatchProcessor::updateBatchSettings not in use yet. Function might be usefull when updating the batch.ini via the GUI.
    ## @param well_data is the list of target wells with their positions/indexes.
    ## @param ID is the batch ID.
    ## @param info is the batch information.
    ## @param dur is the batch duration.
    ## @param interl is the time between the photographing of each well.
    def updateBatchSettings(self, well_map, well_targets, ID, info, dur, interl):
        self.is_active = False
        self.Well_Map = well_map
        self.Well_Targets = well_targets
        self.batch_id = ID
        self.batch_info = info
        self.duration = dur
        self.interleave = interl
        return

    ## @brief BatchProcessor()::startBatch(self) starts the batch process by setting the current (start)time and the endtime. 
    ## It disables the manual motor control and emits the batch_active signal
    ## @todo call updateBatchSettings function
    @Slot()
    def startBatch(self):
        self.start_time = current_milli_time()
        self.end_time = current_milli_time() + (self.duration*1000)
        self.well_positioner.reset_current_well()
        self.signals.batch_active.emit()
        self.is_active = True
        self.msg("Batch process initialized and started with:\n\tDuration: " + str(self.duration) + "\n\tInterleave: " + str(self.interleave) + "\n\tStart_time: " + str(self.start_time) + "\n\tEnd_time: " + str(self.end_time))
        print("Batch process initialized and started with:\n\tDuration: " + str(self.duration) + "\n\tInterleave: " + str(self.interleave) + "\n\tStart_time: " + str(self.start_time) + "\n\tEnd_time: " + str(self.end_time))
        self.runBatch()
        return

    ## @brief BatchProcessor()::runBatch(self) runs the batch after it is started. 
    ## @note the interleave is actually the interleave + processingtime of the "for target in self.Well_Targets:" loop
    def runBatch(self):
        if self.logging:
            recording_file_name = os.path.sep.join([self.path,'batch_positioning_results.csv'])
            recording_file = open(recording_file_name, "w")
        
            # build csv file heading
            record_str = "run_start_time, run_time,"
            for target in self.Well_Targets:
                record_str += ',' + str(self.Well_Map[target[0][1]][1][1]) + ',' + str(self.Well_Map[1][target[0][0]][0])
            recording_file.write(record_str + "\n")
        else:
            recording_file = None
            
        while True:
            print("BatchProcessor thread check: " + str(QThread.currentThread()))
            ## Run start time
            run_start_time = current_milli_time()
            actual_postions = []
                
            for target in self.Well_Targets:
                if not self.is_active:
                    self.signals.batch_inactive.emit()
                    self.msg("Batch stopped.")
                    print("Batch stopped.")
                    return

                else:
                    row = target[0][0]
                    column = target[0][1]
                    self.msg("Target: " + str(target[0][2]))
                    print("Target: at (" + str(self.Well_Map[column][1][1]) + ", " + str(self.Well_Map[1][row][0]) +")")
                    if (self.well_positioner.goto_well(self.Well_Map[column][1][1], self.Well_Map[1][row][0])): ## if found well
                        self.snapshot_request(str(self.batch_id) + "/" + str(target[0][2]))
                        (self.Well_Map[1][row][0], self.Well_Map[column][1][1]) = self.well_positioner.get_current_well()
                        print("  Target adapted to (" + str(self.Well_Map[column][1][1]) + ", " + str(self.Well_Map[1][row][0]) +")")
                        actual_postions.append(self.well_positioner.get_current_well())
                        
                    while self.SnapshotTaken is False:
                        if not self.is_active:
                            self.signals.batch_inactive.emit()
                            #self.msg("Batch stopped, breaking out of SnapshotTaken is False while loop.")
                            print("Batch stopped, breaking out of SnapshotTaken is False while loop.")
                            return
                        print("Waiting in snapshot loop")
                        self.wait_ms(50)
                    self.msg(str(target) + " finished.")
                    print(str(target) + " finished.")
            
                if self.end_time < current_milli_time():
                    self.msg("batch completed")
                    print("batch completed")
                    self.signals.batch_inactive.emit()
                    self.stopBatch()
                    return
                else:
                    self.msg("Remaining time " + str(self.end_time-current_milli_time()))
                    print("Remaining time " + str(self.end_time-current_milli_time()) + " ms")

            run_time = current_milli_time()-run_start_time
            self.msg("Run time: " + str(run_time))
            print("Run time: " + str(run_time) + "\nWaiting for " + str(self.interleave*1000-run_time) + " s")
            if self.interleave*1000-run_time < 0:
                self.msg("To short interleave, please increase the interleave to at least: " + str(run_time))
                print("To short interleave, please increase the interleave to at least: " + str(run_time))
            else:
                ## Wait for the specified interleave minus the run_time of one run 
                self.msg("Waiting for: " + str(self.interleave*1000-run_time) + " s")
                print("Waiting for: " + str(self.interleave*1000-run_time) + " s")
                self.wait_ms(self.interleave*1000-run_time)
                
            if recording_file:
                record_str = str(run_start_time) + ',' + str(run_time)
                for actual_position in actual_postions:
                    record_str += ',' + str(actual_position[0]) +','+ str(actual_position[1])
                print(record_str)
                recording_file.write(record_str + "\n")
            
        if recording_file:
            recording_file.close()
            
        #self.msg("Breaking out batch process")
        print("Finishing batch process")
        return

    ## @brief BatchProcessor()::wait_ms(self, milliseconds) is a delay function.
    ## @param milliseconds is the number of milliseconds to wait.
    def wait_ms(self, milliseconds):
        self.GeneralEventLoop = QEventLoop()
        QTimer.singleShot(milliseconds, self.GeneralEventLoop.exit)
        self.GeneralEventLoop.exec_()
        return

    ## @brief BatchProcessor()::snapshot_request(self, message) emits the self.signals.snapshot_requested signal.
    ## @param message is the pathname of the desired snapshot
    def snapshot_request(self, message):
        self.msg("Requesting snapshot")
        self.signals.snapshot_requested.emit(message)
        self.snapshot_await()
        return

    ## @brief StepperWellPositioning()::snapshot_await(self) runs an eventloop while the new snapshot is not stored in self.image yet.
    def snapshot_await(self):
        self.SnapshotTaken = False
        while self.is_active and not self.SnapshotTaken:
            #self.msg("Waiting for snapshot")
            self.SnapshotEventLoop = QEventLoop()
            QTimer.singleShot(10, self.SnapshotEventLoop.exit)
            self.SnapshotEventLoop.exec_()
        return

    @Slot()
    def snapshot_confirmed(self):
        self.SnapshotTaken = True
        if not (self.SnapshotEventLoop is None):
            self.SnapshotEventLoop.exit()
        return

    ## @brief BatchProcessor()::stopBatch is a slot function which is called when the button stopBatch is pressed on the MainWindow GUI. 
    ## It stops the batch process and resets the wait eventloop if running.
    @Slot()
    def stopBatch(self):
        #self.msg("Stopping Batch process")
        print("Stopping Batch process")
        self.signals.batch_inactive.emit()
        self.signals.process_inactive.emit() ## Used to stop positioning process of function StepperWellPositioning::goto_target
        self.is_active = False
        self.snapshot_confirmed()
        if not (self.GeneralEventLoop is None):
            self.GeneralEventLoop.exit()
            print("Exit BatchProcessor::GeneralEventloop")
        if not (self.SnapshotEventLoop is None):
            self.SnapshotEventLoop.exit()
            print("Exit BatchProcessor::SnapshotEventLoop")
        return
        
    @Slot()
    def close(self):
        self.stopBatch()
        return
              
