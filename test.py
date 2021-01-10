from m5stack import *
from m5ui import *
from uiflow import *
from machine import Pin , I2C

setScreenColor(0xFF0000)

# read out temperature and humidity
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
i2c.scan() # scan for devices

buf = bytearray(5)
i2c.readfrom_into(0x5c, buf)

humidity = buf[0] + buf[1] * 0.1

if humidity > 0.7:
  setScreenColor(0x00FF00)
else:
  setScreenColor(0x0000FF)

