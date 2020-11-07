
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

buzzer = None  # this will represent the buzzer component

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

    buzzer = GPIO.PWM(buzzer_pin, 1)

    buzzer.start(50)

    # adding a callback for when the button is clicked
    GPIO.add_event_detect(rate_pin, GPIO.FALLING, callback=toggle_rate, bouncetime=300)
    GPIO.add_event_detect(start_stop_pin, GPIO.FALLING, callback=start_stop, bouncetime=300)


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
    global program_is_running

    program_is_running = not program_is_running

    _not = "not " if not program_is_running else ""

    print("The program is " + _not + "running")

    print_values()


def beep():
    # turn the buzzer on
    GPIO.output(buzzer_pin, 1)
    # leave it on for a while
    time.sleep(0.5)
    # turn the buzzer off
    GPIO.output(buzzer_pin, 0)


def print_values():
    # using thread as a global variable
    global thread

    if program_is_running:
        thread = threading.Timer(time_interval, print_values)
        thread.daemon = True
        thread.start()

        Vout = chan.voltage
        T_ambient = (Vout - V0)/Tc

        value = chan.value
        
        end = datetime.datetime.now()
        runtime_s = (end - start).seconds
        runtime = str(runtime_s) + "s"
        print("{:7s}\t\t{:<12d}\t{:.3f}  C".format(runtime, value, T_ambient))


if __name__ == "__main__":
    try:
        setup()

        print("Runtime\t\tTemp Reading\tTemp")
        print_values()

        while True:
            pass
    
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()