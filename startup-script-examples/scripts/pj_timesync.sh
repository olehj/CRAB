#!/bin/bash

# Script for CRAB to sync time with NTP and store it for PiJuice RTC clock
# It will also re-enable the Wakeup Alarm function.
#
# Run as root
#
# Version: 20200411

# Set time
for i in {1..10}
do
  if ntpdate -s -b pool.ntp.org; then
    sleep 5
    hwclock -w
    break
  fi
done
