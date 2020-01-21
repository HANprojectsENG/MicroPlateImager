## @package batch_processor.py
## @brief the classes in batch_processor.py handle the batch process of the well plate reader

import os
import sys
import time
import lib.signal as signal
import motor_control.stepper as stepper

from PySide2.QtCore import Slot, QEventLoop, QTimer, QThread

current_milli_time = lambda: int(round(time.time() * 1000))

## @brief BatchProcessor() handles the batch process in which designated wells are photographed with the specified resolution, intervals and duration.
class BatchProcessor(QThread):
    signals = signal.signalClass()
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
        super().__init__()
        self.is_active = False
        self.well_positioner = well_controller
        self.Well_Map = well_map
        self.Well_Targets = well_targets
        self.batch_id = ID
        self.batch_info = info
        self.duration = dur
        self.interleave = interl
        return

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
        self.msg("Batch process initialized and started")
        self.runBatch()
        return

    ## @brief BatchProcessor()::runBatch(self) runs the batch after it is started. 
    ## @todo batch_(in)active signals connection
    ## @todo time handling and conversion
    def runBatch(self):
        while True:
            if not self.is_active:
                self.signals.batch_inactive.emit()
                return

            for target in self.Well_Targets:
                self.msg("Moving to: " + str(target))
                
                column = target[0][0]
                row = target[0][1]
                self.msg("Go to target column: " + str(self.Well_Map[target[0][0]][1][1]) + " and row: " + str(self.Well_Map[1][target[0][1]][0]))
                self.well_positioner.goto_well(self.Well_Map[column][1][1], self.Well_Map[1][row][0])
                ## Take snapshot            
                self.msg("Target: " + str(target) + " finished.")
            
            #if self.end_time > current_milli_time():
            #    self.msg("batch completed")
            #    self.signals.batch_inactive.emit()
            #    return
        
            self.signals.batch_active.emit()
            self.wait_ms(self.interleave*1000)
            self.msg("Waiting for: " + str(self.interleave*1000) + " s")
        return

    ## @brief BatchProcessor()::wait_ms(self, milliseconds) is a delay function.
    ## @param milliseconds is the number of milliseconds to wait.
    def wait_ms(self, milliseconds):
        GeneralEventLoop = QEventLoop()
        QTimer.singleShot(milliseconds, GeneralEventLoop.exit)
        GeneralEventLoop.exec_()
        return

    @Slot()
    def stopBatch(self):
        self.signals.batch_inactive.emit()
        self.is_active = False
        return
        
    @Slot()
    def close(self):
        self.exit(0)
        return
              
