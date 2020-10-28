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

value = chan.value
print('Raw ADC Value: ', value)
print('ADC Voltage: ' + str(Vout) + 'V')


# print("Runtime", "Temp Reading", "Temp", sep='\t\t')
print("Runtime\t\tTemp Reading\tTemp")
print("{:7s}\t\t{:<12d}\t{:.3f}  C".format('100s', value, T_ambient))
