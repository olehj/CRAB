#!/bin/bash

# Script for CRAB to connect to the internet before posting data
# to the web site. It will disconnect when it has completed.
#
# Version: 20200415

# Set the device to turn off when script is done, set false to keep it running (ex: if handled by a cronjob for 24/7 online operation).
SHUTDOWN="true" 	# Default: true			Options: true | false

# Set HOME directory:
HOMEDIR="/home/pi"	# Default: /home/pi

# Set logfile, leave empty or comment out to disable:
#LOGFILE="crab.log"	# Default: crab.log

# Load the system before we start:
sleep 30		# Default: 30

# Script starting, no modifications needed:

# Connect and check connection to CRAB. If not, try to reconnect up to 10 times:
while ! ping -q -c 1 -W 1 send.crab.today >/dev/null; do
  $HOMEDIR/scripts/internet.sh --connect
  ((c++)) && ((c==10)) && break
done

CONNECTION="false"
if ping -q -c 1 -W 1 send.crab.today >/dev/null; then
  CONNECTION="true"
else
  CONNECTION="false"
fi

if [ -n "$LOGFILE" ]; then
  # Set header, date and time for the log
  echo "*******************************************************************************" >> $HOMEDIR/$LOGFILE
  date "+%Y-%m-%d %H:%M:%S" >> $HOMEDIR/$LOGFILE
  echo "" >> $HOMEDIR/$LOGFILE
fi

if [ $CONNECTION == true ]; then
  # Time sync for PiJuice HAT
  sudo $HOMEDIR/scripts/pj_timesync.sh
  
  # Enable Wakeup Alarm for PiJuice HAT after reboot
  sudo $HOMEDIR/scripts/pj_wakeup_enable.py

  # Add custom log for CRAB
  sudo $HOMEDIR/scripts/pj_status.py &> /tmp/customlog.txt
  
  sleep 5

  # Enter $HOME/crab:
  cd $HOMEDIR/crab

  for i in {1..10}
  do
    CRAB_STATUS=$(php crab.php)
    if [ -n "$LOGFILE" ]; then
      echo -n $CRAB_STATUS >> $HOMEDIR/$LOGFILE
    fi
    if [ $CRAB_STATUS != "ERROR" ]; then
      break
    fi
  done
else
  if [ -n "$LOGFILE" ]; then
    echo "Could not connect." >> $HOMEDIR/$LOGFILE
  fi
fi

# Disconnect from the internet:
if [ $CONNECTION == true ]; then
  $HOMEDIR/scripts/internet.sh --disconnect
fi

# Shutdown system after job when running PiJuice with RTC Alarm, and retry shutdown every 10s if it fails:
if [ $SHUTDOWN == true ]; then
  while sleep 10
  do
    sudo $HOMEDIR/scripts/pj_shutdown.py
  done
fi
