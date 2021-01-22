from m5stack import *
from m5ui import *
from uiflow import *
from machine import Pin, I2C
from m5mqtt import M5mqtt
import time
from machine import RTC
rtc = RTC()

import urequests
import json

def getWeekday(weekday):
  if weekday == 'Monday':
    return 1
  elif weekday == 'Tuesday':
    return 2
  elif weekday == 'Wednesday':
    return 3
  elif weekday == 'Thursday':
    return 4
  elif weekday == 'Friday':
    return 5
  elif weekday == 'Saturday':
    return 6
  else:
    return 7

def parseDateTimeStr(dts, weekday):
  # 2021-01-22 T 14:30+01:00
  parts = dts.split('T')
  # date
  datep = parts[0].split('-')
  #time
  timep0 = parts[1].split('+')
  timep = timep0[0].split(':')
  #rtc.init( (int(datep[0]), int(datep[1]), int(datep[2]), int(timep[0]), int(timep[1])) )
  rtc.datetime(( int(datep[0]), int(datep[1]), int(datep[2]), getWeekday(weekday), int(timep[0]), int(timep[1]), 0, 0)) # set a specific date and time

req = urequests.request(method='GET', url='http://worldclockapi.com/api/json/cet/now', headers={'Content-Type':'json/html'})
#date_time_str = '2018-06-29 08:15:27.243860'
date = json.loads(req.text)
parseDateTimeStr(date["currentDateTime"], date["dayOfTheWeek"])
#date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')

# 400kHz is already default
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

p12 = Pin(12, Pin.OUT)
p12.off()
p13 = Pin(13, Pin.OUT)
p13.off()

#rtc = RTC()

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

CHECK_INTERVAL = 3000
# 30min ventilation check
VENTILATION_RATE = 6
ventilationCounter = 0


#relais outputs
stateOut1 = False
stateOut2 = False
ventilationNeeded = False

def zfl(s, width):
  return '{:0>{w}}'.format(s, w=width)

def readHumidity():
  #hum_int = int.from_bytes(i2c.readfrom_mem(0x5c, 0x00, 1), 'big')
  #wait_ms(100)
  #hum_dec = int.from_bytes(i2c.readfrom_mem(0x5c, 0x01, 1), 'big')

	#return data_humidity_high + (data_humidity_low * 0.1)
  #data = i2c.readfrom_mem(0x5c,0x00, 5)
  #temp_int = int.from_bytes(data,'big') >> 16 & 0xff
  #temp_dec = int.from_bytes(data,'big') >> 8 & 0xff
  #hum_int = int.from_bytes(data,'big') >> 32 & 0xff
  #hum_dec = int.from_bytes(data,'big') >> 24 & 0xff
  #cs = int.from_bytes(data,'big') >> 0 & 0xff

  #return hum_int + hum_dec*0.1
  buf = bytearray(5)
  i2c.readfrom_mem_into(0x5c, 0, buf)
  return buf[0] + buf[1] * 0.1

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
  # (2021, 1, 22, 4, 15, 9, 32, 321231) to 2019-09-07T15:50:00
  dt = rtc.datetime()
  datetimestr = "{}-{}-{}T{}:{}:{}+01:00".format(str(dt[0]), zfl(str(dt[1]),2), zfl(str(dt[2]),2), zfl(str(dt[4]),2), zfl(str(dt[5]),2), zfl(str(dt[6]),2) )
  message = str('{{"timestamp":"{}","humidity":{},"ventilationNeeded":{},"stateOut1":{},"stateOut2":{}}}'.format(datetimestr, str(humidity), str(ventilationNeeded).lower(), str(stateOut1).lower(), str(stateOut2).lower()))
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
	elif (humidity > 55.0):
		if (ventilationNeeded == True and stateOut1 == True and stateOut2 == True):
			ventilationNeeded = False
			offOut1()
			offOut2()
	# either way, print value and send status
	showDisplay(humidity)
	sendMQTT(humidity)

	if (ventilationCounter < VENTILATION_RATE):
		ventilationCounter = ventilationCounter + 1
	else:
		# ventilate and reset
		ventilationNeeded = True
		onOut1()
		onOut2()
		ventilationCounter = 0

	wait_ms(CHECK_INTERVAL)
