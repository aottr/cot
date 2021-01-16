from m5stack import *
from m5ui import *
from uiflow import *
from machine import Pin, I2C
from m5mqtt import M5mqtt
import time

# 400kHz is already default
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

p12 = Pin(12, Pin.OUT)
p12.off()
p13 = Pin(13, Pin.OUT)
p13.off()

#connect to broker
mqtt = M5mqtt('room-1', 'mqtt.dit.htwk-leipzig.de', 1883, 'lab', 'fdit', 300)
mqtt.start()

# load from json or equivalent later, testing purposes only
roomSetups = {
	"room-1": {
		"humidity":0.0,
		"stateOut1":False,
		"stateOut2":False,
		"ventilationNeeded":False
	},
	"room-2": {
		"humidity":0.0,
		"stateOut1":False,
		"stateOut2":False,
		"ventilationNeeded":False
	}
}


lcd.font(lcd.FONT_DejaVu24)
lcd.setBrightness(10)

#humidity reference value
GOOD_HUMIDITY = 40.0
ROOM_ID = "room-1"

CHECK_INTERVAL = 300000
# 30min ventilation check
VENTILATION_RATE = 6
ventilationCounter = 0


#relais outputs
stateOut1 = False
stateOut2 = False
ventilationNeeded = False

def readHumidity():
	# data is 4 bites
	buf = bytearray(5)
	i2c.readfrom_into(0x5c, buf)
	#if (buf[0] + buf[1] + buf[2] + buf[3]) & 0xff != buf[4]:
	#	raise Exception("checksum error")

	# first two byte are humidity, next two byte are temperature
	return (buf[0] + buf[1]) * 0.1

def showDisplay(humidity):
	lcd.clear()

	# set colourcodes
	colourBad = 0xff0000
	colourGood = 0x006400

	if (humidity >= GOOD_HUMIDITY):
		lcd.rect(0, 0, 320, 60, colourGood, colourGood)
	else:
		lcd.rect(0, 0, 320, 60, colourBad, colourBad)

	lcd.print('humidity: {}%'.format(humidity), 0, 13, 0xffffff)

	if ventilationNeeded:
		lcd.rect(0, 60, 320, 60, colourBad, colourBad)
		lcd.print('ventilation needed', 0, 73, 0xffffff)
	else:
		lcd.rect(0, 60, 320, 60, colourGood, colourGood)
		lcd.print('no ventilation needed', 0, 73, 0xffffff)

	if stateOut1:
		lcd.rect(0, 120, 320, 60, colourGood, colourGood)
		lcd.print('output1 state: on', 0, 133, 0xffffff)
	else:
		lcd.rect(0, 120, 320, 60, colourBad, colourBad)
		lcd.print('output1 state: off', 0, 133, 0xffffff)

	if stateOut2:
		lcd.rect(0, 180, 320, 60, colourGood, colourGood)
		lcd.print('output2 state: on', 0, 193, 0xffffff)
	else:
		lcd.rect(0, 180, 320, 60, colourBad, colourBad)
		lcd.print('output2 state: off', 0, 193, 0xffffff)

def sendMQTT(humidity):
	topic = str('lab/03/{}'.format(ROOM_ID))
	message = str('{{"humidity":"{}","ventilationNeeded":"{}","stateOut1":"{}","stateOut2":"{}"}}'.format(str(humidity), str(ventilationNeeded), str(stateOut1), str(stateOut2)))
	mqtt.publish(topic, message)

def onOut1():
	p12.on()
	global stateOut1
	stateOut1 = True

def offOut1():
	p12.off()
	global stateOut1
	stateOut1 = False

def onOut2():
	p13.on()
	global stateOut2
	stateOut2 = True

def offOut2():
	p13.off()
	global stateOut2
	stateOut2 = False

while True:
	humidity = readHumidity()
	# if bad humidity
	if (humidity < GOOD_HUMIDITY):
		if (ventilationNeeded == False and stateOut1 == False and stateOut2 == False):
			ventilationNeeded = True
			onOut1()
			onOut2()
			# reset counter bc windows open
			ventilationCounter = 0
	# very good -> turn off vents
	elif (humidity > 60.0):
		if (ventilationNeeded == True and stateOut1 == True and stateOut2 == True):
			ventilationNeeded = False
			offOut1()
			offOut2()
	# either way, print value and send status
	showDisplay(humidity)
	sendMQTT(humidity)

	if (ventilationCounter < VENTILATION_RATE):
		ventilationCounter += 1
	else:
		# ventilate and reset
		onOut1()
		onOut2()
		ventilationCounter = 0

	wait_ms(CHECK_INTERVAL)
