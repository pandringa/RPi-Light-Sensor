from Adafruit_I2C import Adafruit_I2C
import eeml
import time
API_KEY = '[API KEY]'
FEED = 98565
API_URL = '/v2/feeds/{feednum}.xml' .format(feednum = FEED)
address = 0x39
i2c = Adafruit_I2C(address)
control_on = 0x03
control_off = 0x00

def enable():
	print "enabling"
	i2c.write8(0x80, control_on)
	
def disable():
	print "disabling"
	i2c.write8(0x80, control_off)
	
def getLight():
	c0 = i2c.readU16(0xAC);
 	c1 = i2c.readU16(0xAE);
	return c0, c1
	
def getLux(c0, c1):
	ratio = c1/c0
	Lux = 0
	if ratio > 0 and ratio <= 0.5:
		Lux = 0.0304*c0-0.062*ch0*(ratio^1.4)
	elif ratio <= 0.61:
		Lux = 0.0224*c0-0.031*c1
	elif ratio <= 0.8:
		Lux = 0.0128*c0-0.0153*c1
	elif ratio <= 1.3:
		Lux = 0.00146*c0 - 0.00112*c1
	return Lux
	
	
enable()
time.sleep(1)
while True:
	c0, c1 = getLight()
	light = getLux(c0, c1)
	print "Light: "+str(light)+" Lux"
	pac = eeml.Pachube(API_URL, API_KEY)
	pac.update([eeml.Data(0, light)])
	pac.put()
	time.sleep(30)

