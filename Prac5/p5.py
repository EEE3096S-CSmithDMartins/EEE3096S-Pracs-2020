import threading
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import RPi.GPIO as GPIO

time_interval = 1.0

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

	# the button pin (in BCM mode)
	button_pin = 23

	# setting GPIO 23 (BCM) as an input
	GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	# adding a callback for when the button is clicked
	GPIO.add_event_detect(button_pin, GPIO.FALLING, callback=lambda _: print("clicked"), bouncetime=300)



def toggle_rate():
	global time_interval

	if time_interval == 10:
		time_interval = 5

	elif time_interval = 5:
		time_interval = 1
		
	elif time_interval = 1:
		time_interval = 10


# parameters of the temperature sensor (from datasheet)
Tc = 10e-3 # temperature coefficient, in V/ºC
V0 = 500e-3 # output voltage at 0 ºC, in V

def print_values():
	thread = threading.Timer(time_interval, print_values)
	thread.daemon = True
	thread.start()

	Vout = chan.voltage
	T_ambient = (Vout - V0)/Tc

	value = chan.value
	print("{:7s}\t\t{:<12d}\t{:.3f}  C".format('100s', value, T_ambient))

if __name__ == "__main__":
	setup()

	print("Runtime\t\tTemp Reading\tTemp")
	print_values()

	while True:
		pass
