#!/usr/bin/python

import sys
import smbus
import time
import eeml
from Adafruit_I2C import Adafruit_I2C
from array import *
from datetime import datetime
import urllib
import urllib2
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN)
# info about the cosm.com feed
API_KEY = 'CgG1MFaXSc2HyJAku-xB93v3rLCSAKxLTTZCbFM2eHZQaz0g'
FEED = 98565
API_URL = '/v2/feeds/{feednum}.xml' .format(feednum = FEED)
streamName = 2
name = ""


class Luxmeter:
    i2c = None

    def __init__(self, address=0x39, debug=0, pause=1):
        self.i2c = Adafruit_I2C(address)
        self.address = address
        self.pause = pause
        self.debug = debug

        self.i2c.write8(0x80, 0x03)     # enable the device
        self.i2c.write8(0x81, 0x12)     # set gain = 16X and timing = 101 mSec
        time.sleep(self.pause)          # pause for a warm-up

    def readfull(self, reg=0x8C):
        """Reads visible + IR diode from the I2C device"""
        try:
            fullval = self.i2c.readU16(reg)
            newval = self.i2c.reverseByteOrder(fullval)
            if (self.debug):
                print("I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, fullval & 0xFFFF, reg))
            return newval
        except IOError:
            print("Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1

    def readIR(self, reg=0x8E):
        """Reads IR only diode from the I2C device"""
        try:
            IRval = self.i2c.readU16(reg)
            newIR = self.i2c.reverseByteOrder(IRval)
            if (self.debug):
                print("I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, IRval & 0xFFFF, reg))
            return newIR
        except IOError:
            print("Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1

    def readfullauto(self, reg=0x8c):
        """Reads visible + IR diode from the I2C device with auto ranging"""
        try:
            fullval = self.i2c.readU16(reg)
            newval = self.i2c.reverseByteOrder(fullval)
            if newval >= 37177:
                self.i2c.write8(0x81, 0x01)
                time.sleep(self.pause)
                fullval = self.i2c.readU16(reg)
                newval = self.i2c.reverseByteOrder(fullval)
            if (self.debug):
                print("I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, fullval & 0xFFFF, reg))
            return newval
        except IOError:
            print("Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1

    def readIRauto(self, reg=0x8e):
        """Reads IR diode from the I2C device with auto ranging"""
        try:
            IRval = self.i2c.readU16(reg)
            newIR = self.i2c.reverseByteOrder(IRval)
            if newIR >= 37177:
                self.i2c.write8(0x81, 0x01)     #   remove 16x gain
                time.sleep(self.pause)
                IRval = self.i2c.readU16(reg)
                newIR = self.i2c.reverseByteOrder(IRval)
            if (self.debug):
                print("I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, IRval & 0xFFFF, reg))
            return newIR
        except IOError:
            print("Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1


def luxread(type, address = 0x39, debug = False, autorange = True):
    """Grabs a lux reading either with autoranging or without"""
    LuxSensor = Luxmeter(0x39, False)
    if autorange == True:
        ambient = LuxSensor.readfullauto()
        IR = LuxSensor.readIRauto()
    else:
        ambient = LuxSensor.readfull()
        IR = LuxSensor.readIR()

    if ambient == 0:  # in the dark you cant divide by 0 in the next calculation
        ambient = 0.00001  # so I set it to a small number
        
    ratio = (float) (IR / ambient)

    if ((ratio >= 0) & (ratio <= 0.52)):
        lux = (0.0315 * ambient) - (0.0593 * ambient * (ratio**1.4))
    elif (ratio <= 0.65):
        lux = (0.0229 * ambient) - (0.0291 * IR)
    elif (ratio <= 0.80):
        lux = (0.0157 * ambient) - (0.018 * IR)
    elif (ratio <= 1.3):
        lux = (0.00338 * ambient) - (0.0026 * IR)
    elif (ratio > 1.3):
        lux = 0

    #  I want to know the values for IR, ambient, and lux
        
    if (type==1):
       return IR
    elif (type==2):
       return ambient
    elif (type==3):
       return lux


def writeData(s1, s2, s3):
	global name
	currentTime = datetime.now()
	f = open(str(name)+".csv", "a")
	f.write(str(currentTime.day)+":"+str(currentTime.hour)+":"+str(currentTime.minute)+", "+str(s1)+", "+str(s2)+", "+str(s3)+"\n")
	f.close()
    
def getdata():
	global name
	irbuffer=[]      # place to store multiple IR readings type==1
	ambientbuffer=[] # place to store multiple Ambient readings type==2
	luxbuffer=[]     # place to store multiple Lux readings type==3

	# number of reads to save in the bufer
	for x in range(1,20):
		irbuffer.append(luxread(1, autorange=False))
		luxbuffer.append(luxread(3, autorange=False))
		ambientbuffer.append(luxread(2, autorange=False))

	# calculate the average value within the buffer
	a = (sum(ambientbuffer) / len(ambientbuffer))
	b = int((sum(luxbuffer) / len(luxbuffer))) # convert to integer
	c = (sum(irbuffer) / len(irbuffer))
	writeData(a, b, c)
	# Open up data stream to cosm with your URL and key
	try:
            pac = eeml.Pachube(API_URL, API_KEY)

            # data to send to cosm.  Stuff in the '' is important because these are the titles
            # used in the COSM data stream.  Change to whatever you like.
            pac.update(eeml.Data(name, b))
            #pac.update(eeml.Data('IR', c))
            #pac.update(eeml.Data('Ambient', a))

            # send data to cosm
            pac.put()
        except:
            print("NETWORK ERROR")
        

	# in case you want to get the data to the terminal
	return("Lux: %.2f Ambient: %.2f IR: %.2f" % (b, a, c))  

def changeFeed():
	global streamName, name
	streamName += 1
	name = "B-"+str(streamName)
    
	url = "http://api.cosm.com/v2/feeds/"+str(FEED)+"/datastreams"
	f = open("datafile.json", "w")
	f.write('{"version":"1.0.0","datastreams" : [{"id" : "'+str(name)+'"}]}')
	f.close()
	print("New feed is:", name)
        try:
            headers = { 'X-ApiKey' : API_KEY }
            data = open("datafile.json").read()
            req = urllib2.Request(url, data, headers)
            response = urllib2.urlopen(req)
            the_page = response.read()
        except:
            print("NETWORK ERROR")

def minuteTimer():
	print("Countdown")
	i = 0
	while i <= 60:
		if ( GPIO.input(23) == False ):
			print("Changing feeds!")
			changeFeed()
			break
		i += 1
		time.sleep(1)

print("Program started, logging to COSM, ctrl-C to end")  # a startup service message
name = "B-2" #DEBUG
try:
    while 1:
        print(getdata())  #uncomment if you want to see the readings in the terminal
        minuteTimer()   # change the timing of the feed
except KeyboardInterrupt:
        print "program has ended"
