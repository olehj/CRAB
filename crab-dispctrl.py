# Copyright (c) 2017 CRAB
# Author: Ole-Henrik Jakobsen
#
# Last update: 2018.05.27
#
# This script runs crab.php in CLI and displays the data on a screen.
# If you don't need the screen and control button, you don't need to use this script.
# Run php crab.php instead.
#
# This script is mainly made for 128x64 screens.
# Modifications can probably be done to fit to x32:
#   Remove the HEADER and FOOTER and "Updates" will probably make it fit.
#
# Requirements: luma.oled
#

import RPi.GPIO as GPIO

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from threading import Thread
from datetime import datetime
from subprocess import call

import sys, time, re, subprocess

# We use luma oled library for our display
from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106

##
# Set variables
##

# luma.oled settings
# substitute spi(device=0, port=0) below if using that interface
serial = spi(device=0, port=0, gpio_DC=24, gpio_RST=25)

# substitute ssd1331(...) or sh1106(...) below if using that device
device = sh1106(serial)

# Set paths and settings for tempreader and gpsreader
tempreader = '../tempreader'
tempreader_sensor = 'ds18b20'

gpsreader = '../gpsreader'
gpsreader_daemon = 'gpsd'

# Seconds to press the button to shut down the unit (one button, dual function)
button_shutdown_holdsec = 5

# Set input GPIO for button:
button_pin = 12 # pin 32

# Set LED didode GPIO pins
led_R_pin = 21 # pin 40
led_G_pin = 20 # pin 38
led_B_pin = 16 # pin 36

##
# Code starts
##

GPIO.setmode(GPIO.BCM)

blink_led = None

GPIO.setup(led_R_pin, GPIO.OUT)
GPIO.setup(led_G_pin, GPIO.OUT)
GPIO.setup(led_B_pin, GPIO.OUT)

global END_BLINK_LOOP
END_BLINK_LOOP = 0

def ledOn(color, blink = 0):
	if blink == 1:
		END_BLINK_LOOP = 0
	else:
		END_BLINK_LOOP = 1
	
	if re.search('r', color):
		if GPIO.input(led_R_pin) == 0:
			GPIO.output(led_R_pin, GPIO.HIGH)
	else:
		GPIO.output(led_R_pin, GPIO.LOW)
	
	if re.search('g', color):
		if GPIO.input(led_G_pin) == 0:
			GPIO.output(led_G_pin, GPIO.HIGH)
	else:
		GPIO.output(led_G_pin, GPIO.LOW)
	
	if re.search('b', color):
		if GPIO.input(led_B_pin) == 0:
			GPIO.output(led_B_pin, GPIO.HIGH)
	else:
		GPIO.output(led_B_pin, GPIO.LOW)

def ledOff(color, blink = 0):
	if blink == 1:
		END_BLINK_LOOP = 0
	else:
		END_BLINK_LOOP = 1
	
	if re.search('r', color):
		GPIO.output(led_R_pin, GPIO.LOW)
	
	if re.search('g', color):
		GPIO.output(led_G_pin, GPIO.LOW)
	
	if re.search('b', color):
		GPIO.output(led_B_pin, GPIO.LOW)

def ledAllOff():
	global blink_led
	blink_led = None
	ledOff('rgb')

def ledBlink(color = None):
	global blink_led
	
	while not END_BLINK_LOOP:
		# This function ledBlink() will stop any running code, so we use this in a thread and call a variable instead:
		# blink_led = 'rgb' (can be seperate and a combination of them all)
		
		color = blink_led
		
		if color is not None:
			ledOff(color, 1)
			time.sleep(.5)
			ledOn(color, 1)
			time.sleep(.5)

# Startup sequence, for checking that all LEDs are working
ledAllOff()
ledOn('b')
time.sleep(.3)
ledAllOff()
ledOn('g')
time.sleep(.3)
ledAllOff()
ledOn('r')
time.sleep(.3)
ledAllOff()

GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up

# Clear display.
device.clear()

# Load image based on OLED display height.  Note that image is converted to 1 bit color.
if device.height == 64:
	image = Image.open('display/crab_64_1b.ppm').convert('1')
elif device.height == 32:
	image = Image.open('display/crab_32_1b.ppm').convert('1')

# Display image.
device.display(image)

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = device.width
height = device.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.		if GPIO.input(led_R_pin) is True:
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = 0
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Load default font.
font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('Minecraftia.ttf', 8)

counter_tmp = 0
counter_loc = 0
counter_con = 0

BUTTON_TIME = 0
BUTTON_SHORTPRESS = False
END_ALL_LOOPS = 0
END_BLINK_LOOP = 0

msg_button =	'not ready'
msg_temp =	'probing'
msg_loc =	'locating'
msg_ip =	'no'

crab_error = False

# Wait until the system is up and running and the modules have started up (like slower GPS modules etc.)
time.sleep(10)

def loopCommandTemp():
	while not END_ALL_LOOPS:
		global msg_temp
		global counter_tmp
		
		cmd = "php "+tempreader+"/tempreader.php "+tempreader_sensor+" | awk '{printf \"%.1f  \", $1}'"
		msg_temp = subprocess.check_output(cmd, shell = True )
		if re.search('0\.0  0\.0  0\.0', msg_temp):
			msg_temp = 'error'
		
		time.sleep(1)
		
		counter_tmp += 1
		
def loopCommandGPS():
	while not END_ALL_LOOPS:
		global msg_loc
		global counter_loc
		
		cmd = "php "+gpsreader+"/gpsreader.php "+gpsreader_daemon+" simple_location | tr ',' '\n' | awk '{printf \"%.2f  \", $1}'"
		msg_loc = subprocess.check_output(cmd, shell = True )
		if re.search('0\.00  0\.00  0\.00', msg_loc):
			msg_loc = 'error'
		
		time.sleep(1)
		
		counter_loc += 1

def loopCommandIP():
	while not END_ALL_LOOPS:
		global msg_ip
		global counter_con
		
		p = subprocess.Popen(['ping','send.crab.today','-c','1',"-W","5"],stdout=subprocess.PIPE)
		p.wait()
		if p.poll():
			msg_ip = 'no'
		else:
			msg_ip = 'yes'
		
		time.sleep(10)
		
		counter_con += 1

def loopScreen():
	while not END_ALL_LOOPS:
		global msg_button
		global BUTTON_SHORTPRESS
		global blink_led
		
		error_reboot = False
		
		if BUTTON_SHORTPRESS is True and msg_ip == "yes" and msg_temp != "probing" and msg_temp != "error" and msg_loc != "locating" and msg_loc != "error":
			crab_error = False
			blink_led = 'rg'
			
			# Display initial image.
			draw.rectangle((0,0,width,height), outline=0, fill=0)
			draw.text((30, top),     "-= CRAB =-", font=font, fill=255)
			draw.text((x, top+54),   "https://crab.today/", font=font, fill=255)
			draw.text((22, top+18),   "Please wait...", font=font, fill=255)
			device.display(image)
			
			msg_button = 'data sent'
			cmd = ["php", "crab.php"]
			#OUT = subprocess.check_output(cmd, shell = True )
			OUT = subprocess.Popen(cmd, stdout=subprocess.PIPE)
			
			draw.rectangle((0,0,width,height), outline=0, fill=0)
			start_y = 18
			next_y = 8
			for LINE in OUT.stdout.readlines():
				if re.search('Error', str(LINE)) or crab_error is True:
					blink_led = None
					time.sleep(1)
					ledOn('r')
					crab_error = True
				else:
					blink_led = None
					time.sleep(1)
					ledOn('g')
				
				draw.text((x, top+start_y), str(LINE), font=font, fill=255)
				start_y = start_y+next_y
			
			# Display final image.
			draw.text((30, top),     "-= CRAB =-", font=font, fill=255)
			draw.text((x, top+54),   "https://crab.today/", font=font, fill=255)
			draw.text((x, top+10),   "Feedback from CRAB:", font=font, fill=255)
			device.display(image)
			
			BUTTON_SHORTPRESS = False
			
			time.sleep(10)
		else:
			if msg_button != "data sent":
				if msg_ip == "yes" and msg_temp != "probing" and msg_temp != "error" and msg_loc != "locating" and msg_loc != "error":
					msg_button = 'ready'
					blink_led = 'g'
				
				elif msg_temp != "error" and msg_loc != "error":
					msg_button = 'not ready'
					blink_led = 'b'
				
				else:
					msg_button = 'rebooting...'
					blink_led = 'r'
					error_reboot = True
			else:
				blink_led = 'g'
			
			draw.rectangle((0,0,width,height), outline=0, fill=0)
			draw.text((30, top),     "-= CRAB =-", font=font, fill=255)
			draw.text((x, top+54),   "https://crab.today/", font=font, fill=255)
			draw.text((x, top+10),   "GPS: " + str(msg_loc), font=font, fill=255)
			draw.text((x, top+18),   "Temp: " + str(msg_temp), font=font, fill=255)
			draw.text((x, top+26),   "Connection: " + str(msg_ip), font=font, fill=255)
			draw.text((x, top+34),   "Updates: " + str(counter_loc) + "|" + str(counter_tmp) + "|" + str(counter_con), font=font, fill=255)
			draw.text((x, top+42),   "Status:" + str(msg_button) + " ", font=font, fill=255)
			
			# Display image data when at least one of the scripts has run.
			if counter_tmp != 0 or counter_loc != 0 or counter_loc != 0:
				device.display(image)
				
				if error_reboot == True:
					call("sudo shutdown -r now", shell=True)
			
			time.sleep(.5)

def PUSH_BUTTON(button_pin):
	global BUTTON_SHORTPRESS
	global END_ALL_LOOPS
	global blink_led
	
	BUTTON_TIME = 0
	BUTTON_STARTTIME = time.time()
	
	time.sleep(.1)
	
	while GPIO.input(button_pin) == 0:
		pass
	
	BUTTON_TIME = time.time() - BUTTON_STARTTIME
	
	if BUTTON_TIME >= button_shutdown_holdsec:
		# button has been pressed for more than BUTTON_SHUTDOWNSEC seconds
		blink_led = None
		BUTTON_SHORTPRESS = False
		BUTTON_TIME = 0
		END_ALL_LOOPS = 1
		END_BLINK_LOOP = 1
		time.sleep(1)
		ledOn('r')
		device.clear()
		draw.rectangle((0,0,width,height), outline=0, fill=0)
		draw.text((30, top),     "-= CRAB =-", font=font, fill=255)
		draw.text((x, top+54),   "https://crab.today/", font=font, fill=255)
		draw.text((5, top+18),   "Turn off the device", font=font, fill=255)
		draw.text((10, top+26),   "after 10 seconds.", font=font, fill=255)
		device.display(image)
		call("sudo shutdown -h now", shell=True)
		device.clear()
	elif BUTTON_TIME >= .1:
		# short press (0,1 sec.)
		BUTTON_SHORTPRESS = True
		BUTTON_TIME = 0

GPIO.add_event_detect(button_pin, GPIO.FALLING, callback=PUSH_BUTTON, bouncetime=100)

threadCmdTemp = Thread(target = loopCommandTemp)
threadCmdGPS = Thread(target = loopCommandGPS)
threadCmdIP = Thread(target = loopCommandIP)
threadScr = Thread(target = loopScreen)
threadLed = Thread(target = ledBlink)

threadCmdTemp.start()
threadCmdGPS.start()
threadCmdIP.start()
threadScr.start()
threadLed.start()

threadCmdTemp.join()
threadCmdGPS.join()
threadCmdIP.join()
threadScr.join()
threadLed.join()
