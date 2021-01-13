from m5stack import *
from m5ui import *
from uiflow import *
from machine import Pin, I2C
from m5mqtt import M5mqtt
import time

i2c = I2C(0, scl=Pin(23), sda=Pin(21), freq=400000)
i2c.scan()

p12 = Pin(12, Pin.OUT)
p12.off()
p13 = Pin(13, Pin.OUT)
p13.off()

mqtt = M5mqtt('room-1', 'mqtt.dit.htwk-leipzig.de', 1883, 'lab', 'fdit', 300)
mqtt.start()
topic = str('lab/03/room-1')

lcd.font(lcd.FONT_DejaVu40)

humidity = 0.0
stateOut1 = False
stateOut2 = False
ventilationNeeded = False

def readHumidity():
	buf = bytearray(5)
	i2c.readfrom_into(0x5c, buf)
	if (buf[0] + buf[1] + buf[2] + buf[3]) & 0xff != buf[4]:
		raise Exception("checksum error")
	humidity = buf[0] + buf[1] * 0.1

def showDisplay():
	lcd.clear()

	colorRed = 0xff0000
	colorGreen = 0x00ff00

	if (humidity >= 40.0):
		lcd.rect(0, 0, 320, 60, color=colorGreen)
	else:
		lcd.rect(0, 0, 320, 60, color=colorRed)
	lcd.print('humidity: {}%'.format(humidity), 0, 0, 0xffffff)

	if (ventilationNeeded == True):
		lcd.rect(0, 60, 320, 60, color=colorRed)
		lcd.print('ventilation needed', 0, 60, 0xffffff)
	else:
		lcd.rect(0, 60, 320, 60, color=colorGreen)
		lcd.print('no ventilation needed', 0, 60, 0xffffff)

	if (stateOut1 == True):
		lcd.rect(0, 120, 320, 60, color=colorGreen)
		lcd.print('output1 state: on'.format(stateOut1), 0, 120, 0xffffff)
	else:
		lcd.rect(0, 120, 320, 60, color=colorRed)
		lcd.print('output1 state: off'.format(stateOut1), 0, 120, 0xffffff)

	if (stateOut2 == True):
		lcd.rect(0, 180, 320, 60, color=colorGreen)
		lcd.print('output2 state: on'.format(stateOut2), 0, 180, 0xffffff)
	else:
		lcd.rect(0, 180, 320, 60, color=colorRed)
		lcd.print('output2 state: off'.format(stateOut2), 0, 180, 0xffffff)

def sendMQTT():
	message = str('\{"humidity":"{}","ventilationNeeded":"{}","stateOut1":"{}","stateOut2":"{}"\}'.format(str(humidity), str(ventilationNeeded), str(stateOut1), str(stateOut2)))
	mqtt.publish(topic, message)

def onOut1():
	p12.on()
	stateOut1 = True
	
def offOut1():
	p12.off()
	stateOut1 = False

def onOut2():
	p13.on()
	stateOut2 = True

def offOut2():
	p13.off()
	stateOut2 = False

while True:
	readHumidity()

	if (humidity < 40.0):
		if (ventilationNeeded == False && stateOut1 == False && stateOut2 == False):
			ventilationNeeded = True
			onOut1()
			onOut2()
			showDisplay()
			sendMQTT()
		else:
			showDisplay()
			sendMQTT()
	elif (humidity > 60.0):
		if (ventilationNeeded == True && stateOut1 == True && stateOut2 == True):
			ventilationNeeded == False
			offOut1()
			offOut2()
			showDisplay()
			sendMQTT()
		else:
			showDisplay()
			sendMQTT()
	else:
		showDisplay()
		sendMQTT()

	wait_ms(300000)
