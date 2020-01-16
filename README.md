1. Run system
    - Connect monitor, mouse, keyboard, (optionally ethernet), endstops, steppers X and Y, and finally the power sources (RPI and LED).
    - Run the program with the command "run" or "python3 main.py"
    - If the systems doesn't work, you can switch to branch Demo with "git checkout Demo" and run this system with the previously mentioned commands. 
      This Demo system doesn't contain the well positioning based on image processing software.

2. Systems functionality at 16th of January 2020 (last version before open day of Saterday 18th)
    !!IMPORTANT BUTTON Emergency break:
	    The emergency break stops the motors and the klipper and STM firmware fully. A (button) firmware restart is necessary to restart the software and motor configuration.

    BUTTON home X0 Y0:
	    Manual homing with button home X0 Y0. Trigger the endstops manually.
    
    BUTTON Goto XY:
	    Goto XY button can be used to move the the entered X and Y coordinates.
    
    BUTTON Goto well:
	    Goto well moves to the selected well and positions it with a simple image processing algorithm. 
		!!Note: this functionality works, but doesn't position very exact yet. 
		    - Sometimes the systems hangs in a whileloop and the motors aren't stopped when closing the window. Restart the system and after a new manual homing, the system can be closed correctly.
    
    BUTTON STM read:
	    Prints data in the log window if it is available in the serial read buffer.
    
    BUTTON start batch and stop batch:
	    Not in use.
    
    BUTTON Doxygen:
	    Internet connection necessary!! Generates doxygen documentation and opens a chromium-browser instance of the documentation. 
	    Follow the process of the generation in the terminal, some patience might be needed:)
    
    BUTTONS <>v^:
            Move the well plate. First home the wellplate

3. Run and display Doxygen documentation via commandline
    Make sure doxygen is installed using sudo apt-get install doxygen.

    Make sure chromium-browser is installed using sudo apt-get install chromium-browser.

    make sure graphviz is installed using sudo apt-get install graphviz.

    Run and open the documentation with the command "make docs && make open-docs". 

    Delete generated documentation with the command "make clean-docs"

4. Run Doxygen documentation via the well reader GUI
    Make sure doxygen is installed using sudo apt-get install doxygen.

    Make sure chromium-browser is installed using sudo apt-get install chromium-browser.

    make sure graphviz is installed using sudo apt-get install graphviz.

    Hit the orange button
