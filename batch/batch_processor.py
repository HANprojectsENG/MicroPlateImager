## @package batch_processor.py
## @brief the classes in batch_processor.py handle the batch process of the well plate reader

import os
import sys
import time
import numpy as np
import lib.signal as signal
import motor_control.stepper as stepper

from PySide2.QtCore import Slot, QEventLoop, QTimer, QThread

current_milli_time = lambda: int(round(time.time() * 1000))

## @brief BatchProcessor() handles the batch process in which designated wells are photographed with the specified resolution, intervals and duration.
class BatchProcessor():#QThread):
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
    
    ## @brief BatchProcessor()::__init__ sets the batch settings
    ## @param well_pos is the well positioning class instance used to position the wells under the camera.
    ## @param well_data is the list of target wells with their positions/column- rowindexes.
    ## @param ID is the batch ID.
    ## @param info is the batch information.
    ## @param dur is the batch duration.
    ## @param interl is the time between the photographing of each well.
    def __init__(self, well_controller, well_map, well_targets, ID, info, dur, interl):
        #super().__init__()
        self.is_active = False
        self.well_positioner = well_controller
        self.Well_Map = well_map
        self.Well_Targets = well_targets
        self.batch_id = ID
        self.batch_info = info
        self.duration = dur
        self.interleave = interl
        return

    #def __del__(self):
    #    None
    #    self.wait()
        
    ## @brief BatchProcessor()::msg emits the message signal. This emit will be catched by the logging slot function in main.py.
    ## @param message is the string message to be emitted.
    @Slot(str)
    def msg(self, message):
        if message is not None:
            self.signals.mes.emit(self.__class__.__name__ + ": " + str(message))
        return

    ## @brief BatchProcessor()::updateBatchSettings(self, well_data, ID, info, dur, interl) can be called to update the batch settings during runtime.
    ## @todo well_data update in MainWindow.
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
    ## @todo disable manual control buttons
    ## @todo connect batch_active signal in main function
    ## @todo batchrun snapshot directory
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
    ## @todo batch_(in)active signals connection
    ## @todo take snapshot
    def runBatch(self):
        while True:
            print("BatchProcessor thread check: " + str(QThread.currentThread()))
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
                    print("Target: " + str(target[0][2]))
                    if (self.well_positioner.goto_well(self.Well_Map[column][1][1], self.Well_Map[1][row][0])): ## if found well
                        self.snapshot_request(str(self.batch_id) + "/" + str(target[0][2]))
                    while self.SnapshotTaken is False:
                        if not self.is_active:
                            self.signals.batch_inactive.emit()
                            self.msg("Batch stopped.")
                            print("Batch stopped.")
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
                    print("Remaining time " + str(self.end_time-current_milli_time()))

            ## Wait for the specified interval after all wells are photographed
            self.msg("Waiting for: " + str(self.interleave*1000) + " s")
            print("Waiting for: " + str(self.interleave*1000) + " s")
            self.wait_ms(self.interleave*1000)
    
        self.msg("Breaking out batch process")
        print("Breaking out batch process")
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
            self.msg("Waiting for snapshot")
            self.SnapshotEventLoop = QEventLoop()
            QTimer.singleShot(10, self.SnapshotEventLoop.exit)
            self.SnapshotEventLoop.exec_()
        return

    @Slot()
    def snapshot_confirmed(self):
        self.SnapshotTaken = True
        if not (self.SnapshotEventLoop is None):
            self.SnapshotEventLoop.exit()

    ## @brief BatchProcessor()::stopBatch is a slot function which is called when the button stopBatch is pressed on the MainWindow GUI. 
    ## It stops the batch process and resets the wait eventloop if running.
    ## @todo connect batch_inactive to function that sets self.is_active to False like in the StepperWellPositioning class is done
    @Slot()
    def stopBatch(self):
        self.msg("Stopping Batch process")
        print("Stopping Batch process")
        self.signals.batch_inactive.emit()
        self.signals.process_inactive.emit() ## Used to stop positioning process of function StepperWellPositioning::goto_target
        self.is_active = False
        self.snapshot_confirmed()
        if not (self.GeneralEventLoop is None):
            self.GeneralEventLoop.exit()
            self.msg("Exit BatchProcessor::GeneralEventloop")
        if not (self.SnapshotEventLoop is None):
            self.SnapshotEventLoop.exit()
            self.msg("Exit BatchProcessor::SnapshotEventLoop")
        return
        
    @Slot()
    def close(self):
        self.stopBatch()
        return
              
