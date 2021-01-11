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

mqtt = M5mqtt('room-1', 'mqtt.dit.htwk-leipzig.de', 1883, 'mqtt', '12345', 300)
mqtt.start()
topic = str('group-3/room-1')

lcd.font(lcd.FONT_DejaVu40)

outsideHumidity = 0.0
humidity = 0.0
windows = str('closed')
humidifier = str('off')

def readHumidity():
	buf = bytearray(5)
	i2c.readfrom_into(0x5c, buf)
	if (buf[0] + buf[1] + buf[2] + buf[3]) & 0xff != buf[4]:
		raise Exception("checksum error")
	humidity = buf[0] + buf[1] * 0.1

def getOutsideHumidity():
	outsideHumidity = 80.0

def showDisplay():
	lcd.clear()

	colorRed = 0xff0000
	colorGreen = 0x00ff00

	if (humidity >= 40.0):
		lcd.rect(0, 0, 320, 60, color=colorGreen)
	else:
		lcd.rect(0, 0, 320, 60, color=colorRed)
	lcd.print('Humidity: {}%'.format(humidity), 0, 0, 0xffffff)

	if (outsideHumidity >= 50.0):
		lcd.rect(0, 60, 320, 60, color=colorGreen)
	else:
		lcd.rect(0, 60, 320, 60, color=colorRed)
	lcd.print('Outside Humidity: {}%'.format(outsideHumidity), 0, 60, 0xffffff)

	if (windows == "open"):
		lcd.rect(0, 120, 320, 60, color=colorGreen)
	else:
		lcd.rect(0, 120, 320, 60, color=colorRed)
	lcd.print('Windows State: {}'.format(windows), 0, 120, 0xffffff)

	if (humidifier == "on"):
		lcd.rect(0, 180, 320, 60, color=colorGreen)
	else:
		lcd.rect(0, 180, 320, 60, color=colorRed)
	lcd.print('Humidifier State: {}'.format(humidifier), 0, 180, 0xffffff)


def sendMQTT():
	message = str('\{"humidity":"{}","outsideHumidity":"{}","windows":"{}","humidifier":"{}"\}'.format(str(humidity), str(outsideHumidity), windows, humidifier))
	mqtt.publish(topic, message)

def openWindows():
	p12.on()
	windows = str('open')
	
def closeWindows():
	p12.off()
	windows = str('closed')

def startHumidifier():
	p13.on()
	humidifier = str('on')

def stopHumidifier():
	p13.off()
	humidifier = str('off')

while True:
	readHumidity()
	getOutsideHumidity()

	if (humidity <= 40.0):
		if (outsideHumidity >= 50.0 && windows == "closed"):
			openWindows()
			showDisplay()
			sendMQTT()
		elif (outsideHumidity < 50.0 && humidifier == "off"):
			startHumidifier()
			showDisplay()
			sendMQTT()
	elif (humidity >= 50.0):
		if (windows == "open" || humidifier == "on"):
			closeWindows()
			stopHumidifier()
			showDisplay()
			sendMQTT()
		else:
			showDisplay()
			sendMQTT()
	else:
		showDisplay()
		sendMQTT()

	wait_ms(300000)