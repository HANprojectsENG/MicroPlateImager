README.md V23_01_2020

1. Run system
    - Connect monitor, mouse, keyboard, (optionally ethernet), endstops, steppers X and Y, and finally the power sources (RPI and LED).
    - Run the program with the command "python3 main.py"
    - During running, mind the systems temperature on your monitor. It should not exceed 75 degrees Celcius

2. Systems functionality
    !!IMPORTANT BUTTON Emergency break:
	    The emergency break stops the motors and the klipper and STM firmware fully. A (button) firmware restart is necessary to restart the software and motor configuration.

    BUTTON home X0 Y0:
	    Manual homing with button home X0 Y0. Trigger the endstops manually.
    
    BUTTON Goto XY:
	    Goto XY button can be used to move the the entered X and Y coordinates.
    
    BUTTON Goto well:
	    Goto well moves to the selected well and positions it with a simple image processing algorithm. This button will home again, because the software doesn't know the current well location.
		
    BUTTON STM read:
	    Prints data in the log window if it is available in the serial read buffer. Most prints are done signal triggered, so if nothing happens, the buffer is empty.
    
    BUTTON start batch and stop batch:
	    - Starts/stops the batch process with the settings which are specified in the batch.ini and settings.ini file.
        
        Batch start and process
        - This process wil start with an homing. After that it goes to the first specified target, makes a snapshot, goes on to the next until all wells are photographed   (single run). 
        - After this single run, the system waits for the specified interleave (minus the single runtime).
        - Now the next single run will start. This process goes on, until the specified duration time is passed.
        - If the software cannot find a well, it homes and goes to the next well from the home position. 
        
        Batch stop
        - If you stop the batch process, it might finish its current move, so be patient and wait for the process to finish.
        - The batch process is also correctly stopped at window exit. Please have some patience here also.
    
    BUTTON Doxygen:
	    Internet connection necessary!! Generates doxygen documentation and opens a chromium-browser instance of the documentation. 
	    Follow the process of the generation in the terminal.
    
    BUTTONS <>v^:
            Move the well plate. First home the wellplate with button home X0 Y0

3. Run and display Doxygen documentation via commandline
    Make sure doxygen is installed using sudo apt-get install doxygen.

    Make sure chromium-browser is installed using sudo apt-get install chromium-browser.

    make sure graphviz is installed using sudo apt-get install graphviz.

    Run and open the documentation with the command "make docs && make open-docs". 

    Delete generated documentation with the command "make clean-docs"

    Each make docs will first run a make clean-docs in order to be sure the newest documentation is generated.

4. Run Doxygen documentation via the well reader GUI
    Make sure doxygen is installed using sudo apt-get install doxygen.

    Make sure chromium-browser is installed using sudo apt-get install chromium-browser.

    make sure graphviz is installed using sudo apt-get install graphviz.

    Hit the orange button
