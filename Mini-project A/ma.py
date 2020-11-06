
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


def setup():
	# the following variables must be global
	global spi, cs, mcp, chan

	# create the spi bus 
	spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

	# create the cs (chip select) 
	cs = digitalio.DigitalInOut(board.D5)

	# create the mcp object 
	mcp = MCP.MCP3008(spi, cs)

	# create an analog input channel on pin 1 
	chan = AnalogIn(mcp, MCP.P1)

	# the taggle rate button pin (in BCM mode)
	button_pin = 23

	# setting GPIO 23 (BCM) as an input
	GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	# adding a callback for when the button is clicked
	GPIO.add_event_detect(button_pin, GPIO.FALLING, callback=toggle_rate, bouncetime=300)


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