#!/usr/bin/python3
#
# Get power and battery status from PiJuice
# Last update: 2020.04.15

import os, time
from pijuice import PiJuice

while not os.path.exists('/dev/i2c-1'):
    time.sleep(0.1)

pijuice = PiJuice(1, 0x14)

status = pijuice.status.GetStatus()
# battery_status is string constant that describes current battery status, one of four: 'NORMAL', 'CHARGING_FROM_IN', 'CHARGING_FROM_5V_IO', 'NOT_PRESENT'.
status_battery = status['data']['battery'] if status['error'] == 'NO_ERROR' else status['error']
# power_input_status is string constant that describes current status of USB Micro power input, one of four: 'NOT_PRESENT', 'BAD', 'WEAK', 'PRESENT'.
status_powerInputIn = status['data']['powerInput'] if status['error'] == 'NO_ERROR' else status['error']
# 5v_power_input_status: is string constant that describes current status of 5V GPIO power input, one of four: 'NOT_PRESENT', 'BAD', 'WEAK', 'PRESENT'.
status_powerInput5vIo = status['data']['powerInput5vIo'] if status['error'] == 'NO_ERROR' else status['error']

charge = pijuice.status.GetChargeLevel()
charge = charge['data'] if charge['error'] == 'NO_ERROR' else charge['error']
temp =  pijuice.status.GetBatteryTemperature()
temp = temp['data'] if temp['error'] == 'NO_ERROR' else temp['error']
vbat = pijuice.status.GetBatteryVoltage()	        
vbat = vbat['data'] if vbat['error'] == 'NO_ERROR' else vbat['error'] 
ibat = pijuice.status.GetBatteryCurrent()
ibat = ibat['data'] if ibat['error'] == 'NO_ERROR' else ibat['error']
vio =  pijuice.status.GetIoVoltage()
vio = vio['data'] if vio['error'] == 'NO_ERROR' else vio['error']
iio = pijuice.status.GetIoCurrent()
iio = iio['data'] if iio['error'] == 'NO_ERROR' else iio['error']

status_battery = status_battery.replace("CHARGING_FROM_IN", "charging").replace("CHARGING_FROM_5V_IO", "charging").replace("_", " ").lower()
status_powerInputIn = 'NOT_PRESENT' if status_powerInputIn == 'NOT_PRESENT' else status_powerInputIn
status_powerInput5vIo = 'NOT_PRESENT' if status_powerInput5vIo == 'NOT_PRESENT' else status_powerInput5vIo

status_powerInput = 'NOT_PRESENT'

if status_powerInputIn == 'NOT_PRESENT' and status_powerInput5vIo != 'NOT_PRESENT':
	status_powerInput = status_powerInput5vIo
elif status_powerInputIn != 'NOT_PRESENT' and status_powerInput5vIo == 'NOT_PRESENT':
	status_powerInput = status_powerInputIn

status_powerInput = status_powerInput.replace("_", " ").lower()

print('Power Input:',status_powerInput,'('+str(vio/1000)+'V',str(iio)+'mAh)')
print('Battery:    ',status_battery,'('+str(charge)+'%',str(temp)+chr(176)+'C',str(vbat/1000)+'V',str(ibat)+'mAh)')
