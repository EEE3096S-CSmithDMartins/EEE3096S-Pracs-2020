import threading
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# create the spi bus 
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select) 
cs = digitalio.DigitalInOut(board.D5)

# create the mcp object 
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on pin 1 
chan = AnalogIn(mcp, MCP.P1)

# parameters of the temperature sensor (from datasheet)
Tc = 10e-3 # temperature coefficient, in V/ºC
V0 = 500e-3 # output voltage at 0 ºC, in V

Vout = chan.voltage
T_ambient = (Vout - V0)/Tc

print('Raw ADC Value: ', chan.value)
print('ADC Voltage: ' + str(chan.voltage) + 'V')
print('Temperature:', T_ambient, 'ºC')

