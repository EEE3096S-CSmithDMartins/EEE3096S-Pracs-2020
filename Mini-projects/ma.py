import threading
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import datetime
import RPi.GPIO as GPIO
import ES2EEPROMUtils
import os
import time


buzzer_pin = 13  # the buzzer pin in BCM mode

# buzzer = None  # this will represent the buzzer component

sample_count = 0  # the number of samples up to now

eeprom_index = 0
eeprom = ES2EEPROMUtils.ES2EEPROM()
time_interval = 5
thread = None

program_is_running = True  # this variable will be toggled when the start-stop button is pressed

# parameters of the temperature sensor (from datasheet)
Tc = 10e-3 # temperature coefficient, in V/℃
V0 = 500e-3 # output voltage at 0 ℃, in V

# to calculate runtime
start = datetime.datetime.now()

def setup():
    # the following variables must be global
    global spi, cs, mcp, chan, buzzer

    # create the spi bus 
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

    # create the cs (chip select) 
    cs = digitalio.DigitalInOut(board.D5)

    # create the mcp object 
    mcp = MCP.MCP3008(spi, cs)

    # create an analog input channel on pin 1 
    chan = AnalogIn(mcp, MCP.P1)


    # the toggle rate button pin (in BCM mode)
    rate_pin = 23  # this is pin 16 in BOARD MODE

    # the pin to start/stop printing to the console
    start_stop_pin = 24  # this is pin 18 in BOARD MODE 

    # setting GPIO 23 (BCM) and GPIO 24 (BCM) as an input
    GPIO.setup((rate_pin, start_stop_pin), GPIO.IN, pull_up_down=GPIO.PUD_UP)

    #region Setup buzzer
    GPIO.setup(buzzer_pin, GPIO.OUT, initial=GPIO.LOW)

    # adding a callback for when the button is clicked
    GPIO.add_event_detect(rate_pin, GPIO.FALLING, callback=toggle_rate, bouncetime=300)
    GPIO.add_event_detect(start_stop_pin, GPIO.FALLING, callback=start_stop, bouncetime=300)

#def fetch_scores():
#	eeprom_data = []
#	for x in range(0, eeprom_index):
#		data = eeprom.read_block(x, 4)
#		print(x)

def save_scores(data):
	global eeprom_index
	#if index smaller than 20 we read data and increment index
	if eeprom_index < 20:
		for i in range(0, len(data)):
			#eeprom.write_block(eeprom_index, data[i])
			pass
		eeprom_index += 1
	#if index greater than 20 we reset it to 0 and start writing new data...
	#...from index 0
	else:
		eeprom_index = 0

		#add data
		for i in range(0, len(data)):
			#eeprom.write_block(eeprom_index, data[i])
			pass
		eeprom_index += 1
def toggle_rate(_):
    """
        This function toggles the sampling time
    """
    global time_interval, thread

    # stopping the thread
    thread.cancel()

    if time_interval == 10:
        time_interval = 5

    elif time_interval == 5:
        time_interval = 1
        
    elif time_interval == 1:
        time_interval = 10
    
    thread = threading.Timer(time_interval, print_values)

    # starting the thread with a new time
    thread.start()


def start_stop(_):
    global program_is_running, thread

    # if the program is running
    if program_is_running:
        # stop it
        thread.cancel()

        # clear the screen
        os.system('clear')

        print("Logging has stopped")
    
    # if the program is not running
    else:
        # clear the screen
        os.system('clear')

        # resume running
        print("Logging resumed")
        print_header()
        thread = threading.Timer(time_interval, print_values)
        thread.start()

    program_is_running = not program_is_running


def beep():
    # turn the buzzer on
    GPIO.output(buzzer_pin, 1)
    # leave it on for a while
    time.sleep(0.3)
    # turn the buzzer off
    GPIO.output(buzzer_pin, 0)


def print_header():
    # don't worry about the last column; it will be removed.
    print("{:8s}\t{:9s}\t{:4s}\t\t{:s}".format("Time", "Sys Timer", "Temp", "Buzzer"))


def print_values():
    # using thread as a global variable
    global thread
    global sample_count

    thread = threading.Timer(time_interval, print_values)
    thread.daemon = True
    thread.start()

    Vout = chan.voltage
    T_ambient = (Vout - V0)/Tc

    value = chan.value
    
    # calculating the time since the system started
    end = datetime.datetime.now()
    sys_time = (end - start).total_seconds()
    sys_hours, remainder = divmod(sys_time, 3600)
    sys_minunes, sys_seconds = divmod(remainder, 60)
    sys_time = "{:02d}:{:02d}:{:02d}".format(int(sys_hours), int(sys_minunes), int(sys_seconds))
    
    # the current time as a string
    current_time = end.strftime("%H:%M:%S")

    #isolate current time
    hours = end.hour
    minutes = end.minute
    seconds = end.strftime("%S")
    temperature = round(T_ambient, 2)
    eeprom_data = [hours, minutes, seconds, temperature]
    save_scores(eeprom_data)

    sample_count += 1
    print("{:8s}\t{:9s}\t{:.3f}  C\t {:d}".format(current_time, sys_time, T_ambient, sample_count))

    # beep in the first sample and every 5th sample
    if sample_count == 1 or sample_count % 5 == 0:
        beep()


if __name__ == "__main__":
    try:
        setup()
        print_header()
        print_values()

        while True:
            pass
    
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
