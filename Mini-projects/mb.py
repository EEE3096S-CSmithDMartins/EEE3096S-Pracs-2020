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
import blynklib


BLYNK_AUTH = "dbRneQ7iQIH-TkBb6ZoM0qqrNkUcf6Ew"

blynk = blynklib.Blynk(BLYNK_AUTH)

buzzer_pin = 13  # the buzzer pin in BCM mode

sample_count = 0  # the number of samples up to now

eeprom_index = 0
eeprom = ES2EEPROMUtils.ES2EEPROM()
time_interval = 5
thread = None

program_is_running = True  # this variable will be toggled when the start-stop button is pressed

# parameters of the temperature sensor (from datasheet)
Tc = 10e-3 # temperature coefficient, in V/℃
V0 = 500e-3 # output voltage at 0 ℃, in V
T_ambient = 0

# to calculate runtime
start = datetime.datetime.now()

def setup():
    # the following variables must be global
    global spi, cs, mcp, chan, buzzer

    #region Setup ADC
    # create the spi bus 
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

    # create the cs (chip select) 
    cs = digitalio.DigitalInOut(board.D5)

    # create the mcp object 
    mcp = MCP.MCP3008(spi, cs)

    # create an analog input channel on pin 1 
    chan = AnalogIn(mcp, MCP.P1)
    #endregion Setup ADC

    # the pin to start/stop printing to the console
    start_stop_pin = 24  # this is pin 18 in BOARD MODE 

    # setting GPIO 24 (BCM) as an input
    GPIO.setup(start_stop_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    #region Setup buzzer
    GPIO.setup(buzzer_pin, GPIO.OUT, initial=GPIO.LOW)

    # adding a callback for when the start/stop button is clicked
    GPIO.add_event_detect(start_stop_pin, GPIO.FALLING, callback=start_stop, bouncetime=300)

    # handling the virtual button clicks
    @blynk.handle_event('write V1')
    def write_virtual_pin_handler(pin, value):
        toggle_rate()

    @blynk.handle_event('read V2')
    def read_virtual_pin_handler(pin):
        blynk.virtual_write(pin, round(T_ambient, 3))


    # an extra button to quit
    @blynk.handle_event('write V3')
    def write_virtual_pin_handler(pin, value):
        exit()


def fetch_scores():
	data = eeprom.read_block(eeprom_index, 4)
	print(data)


def save_scores(data):
	global eeprom_index
	#if index smaller than 20 we read data and increment index
	if eeprom_index < 20:
		eeprom.write_block(eeprom_index, data)
		#fetch_scores()
		eeprom_index += 1

	#if index greater than 20 we reset it to 0 and start writing new data...
	#...from index 0
	else:
		eeprom_index = 0

		#add data
		eeprom.write_block(eeprom_index,data)
		#fetch_scores()
		eeprom_index += 1

def toggle_rate():
    """
        This function toggles the sampling time
    """
    global time_interval, thread

    # stopping the thread
    thread.cancel()

    if time_interval == 10:
        time_interval = 5

    elif time_interval == 5:
        time_interval = 2
        
    elif time_interval == 2:
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
    print("{:8s}\t{:9s}\t{:4s}".format("Time", "Sys Timer", "Temp"))


def print_values():
    # using thread as a global variable
    global thread
    global sample_count
    global T_ambient

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
    seconds = int(end.strftime("%S"))
    temperature = round(T_ambient)
    eeprom_data = [hours, minutes, seconds, temperature]
    save_scores(eeprom_data)

    sample_count += 1

    times_and_temperature = "{:8s}\t{:9s}\t{:.3f}  C".format(current_time, sys_time, T_ambient)

    # printing to the Pi's console
    print(times_and_temperature)

    # printing to the Blynk console whenever blynk requests the temperature. really bad solution
    # @blynk.handle_event('read V2')
    # def my_virtual_pin_handler(pin):
    #     blynk.virtual_write(0, times_and_temperature+'\n')   


    

    # beep in the first sample and every 5th sample
    if sample_count == 1 or sample_count % 5 == 0:
        beep()


if __name__ == "__main__":
    try:
        setup()
        # clearing the blynk logo
        os.system("clear")
        print_header()
        print_values()

        while True:
            blynk.run()
            pass
    
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
