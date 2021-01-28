from m5stack import *
from m5ui import *
from uiflow import *
from machine import Pin, I2C
from m5mqtt import M5mqtt
import time
import urequests
import json

from machine import RTC
rtc = RTC()


# humidity reference value
GOOD_HUMIDITY = 40.0
# room id of device
ROOM_ID = "room-1"
# check interval in ms
CHECK_INTERVAL = 3000
# rate to trigger ventilation (e.g. 6 means that after 6*CHECK_INTERVAL with no ventilation, ventilation will be initiated anyway)
VENTILATION_RATE = 6


# function to map weekday string to number and return it
def mapWeekdayStr(weekdayStr):
	if weekdayStr == 'Monday':
		return 1
	elif weekdayStr == 'Tuesday':
		return 2
	elif weekdayStr == 'Wednesday':
		return 3
	elif weekdayStr == 'Thursday':
		return 4
	elif weekdayStr == 'Friday':
		return 5
	elif weekdayStr == 'Saturday':
		return 6
	else:
		return 7

# function to parse datetime in format 2021-01-22T14:30+01:00 with weekday and return datetime tuple
def parseDateTime(dateTimeStr, weekdayStr):
	parts = dateTimeStr.split('T')
	date = parts[0].split('-')
	time = parts[1].split('+')
	timeParts = time[0].split(':')
	dateTimeTuple = (int(date[0]), int(date[1]), int(date[2]), mapWeekdayStr(weekdayStr), int(timeParts[0]), int(timeParts[1]), 0, 0)
	return dateTimeTuple

# function to set system datetime with result of clock api request
def setDateTime():
	req = urequests.request(method='GET', url='http://worldclockapi.com/api/json/cet/now', headers={'Content-Type':'json/html'})
	res = json.loads(req.text)
	dateTimeTuple = parseDateTime(res["currentDateTime"], res["dayOfTheWeek"])
	rtc.datetime(dateTimeTuple)

# function to add leading zeros to string with numbers to get certain length
def zfl(s, width):
	return '{:0>{w}}'.format(s, w=width)


# initialize i2c bus for dht12
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

# initialize output pins for relais
p12 = Pin(12, Pin.OUT)
p12.off()
p13 = Pin(13, Pin.OUT)
p13.off()

# set system datetime
setDateTime()

# connect to mqtt broker
mqtt = M5mqtt('room-1', 'mqtt.dit.htwk-leipzig.de', 1883, 'lab', 'fdit', 300)
mqtt.start()

# initialize display
lcd.font(lcd.FONT_DejaVu24)
lcd.setBrightness(10)

# initialize states
stateOut1 = False
stateOut2 = False
ventilationNeeded = False

# initialize ventilation counter
ventilationCounter = 0


# function to read data from i2c dht12 and return humidity
def readHumidity():
	buf = bytearray(5)
	i2c.readfrom_mem_into(0x5c, 0, buf)
	return buf[0] + buf[1] * 0.1

# function to show state on display
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

# function to send state and timestamp to defined mqtt broker
def sendMQTT(humidity):
	topic = str('lab/03/{}'.format(ROOM_ID))
	# (2021, 1, 22, 4, 15, 9, 32, 321231) to 2019-09-07T15:50:00
	dateTime = rtc.datetime()
	timestamp = "{}-{}-{}T{}:{}:{}+01:00".format(str(dateTime[0]), zfl(str(dateTime[1]),2), zfl(str(dateTime[2]),2), zfl(str(dateTime[4]),2), zfl(str(dateTime[5]),2), zfl(str(dateTime[6]),2))
	message = str('{{"timestamp":"{}","humidity":{},"ventilationNeeded":{},"stateOut1":{},"stateOut2":{}}}'.format(timestamp, str(humidity), str(ventilationNeeded).lower(), str(stateOut1).lower(), str(stateOut2).lower()))
	mqtt.publish(topic, message)

	#topic = str('lab/03/room-2')
	#message = str('{{"humidity":{},"ventilationNeeded":{},"stateOut1":{},"stateOut2":{}}}'.format(str(humidity-3), str(ventilationNeeded).lower(), str(stateOut1).lower(), str(stateOut2).lower()))
	#mqtt.publish(topic, message)

	#topic = str('lab/03/room-3')
	#message = str('{{"humidity":{},"ventilationNeeded":{},"stateOut1":{},"stateOut2":{}}}'.format(str(humidity+40), str(ventilationNeeded).lower(), str(stateOut1).lower(), str(stateOut2).lower()))
	#mqtt.publish(topic, message)

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
	elif (humidity > 50.0):
		if (ventilationNeeded == True and stateOut1 == True and stateOut2 == True):
			ventilationNeeded = False
			offOut1()
			offOut2()
	# either way, print value and send status

	if (ventilationCounter < VENTILATION_RATE-1):
		ventilationCounter = ventilationCounter + 1
		showDisplay(humidity)
		sendMQTT(humidity)
	else:
		# ventilate and reset
		ventilationNeeded = True
		onOut1()
		onOut2()
		showDisplay(humidity)
		sendMQTT(humidity)
		wait_ms(CHECK_INTERVAL)
		
		ventilationNeeded = False
		offOut1()
		offOut2()
		showDisplay(humidity)
		sendMQTT(humidity)
		ventilationCounter = 0

	wait_ms(CHECK_INTERVAL)
