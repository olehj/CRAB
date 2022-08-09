#!/usr/bin/python3
# This script is started at reboot by cron
# Since the start is very early in the boot sequence we wait for the i2c-1 device

import os, pijuice, time

while not os.path.exists('/dev/i2c-1'):
    time.sleep(0.1)

pj = pijuice.PiJuice(1, 0x14)
pj.power.SetWakeUpOnCharge(1,non_volatile=True)
pj.rtcAlarm.SetWakeupEnabled(True)

a={}
a['year'] = 'EVERY_YEAR'
a['month'] = 'EVERY_MONTH'
a['day'] = 'EVERY_DAY'
a['hour'] = 'EVERY_HOUR'
a['minute'] = 0
a['second'] = 0

pj.rtcAlarm.SetAlarm(a)
