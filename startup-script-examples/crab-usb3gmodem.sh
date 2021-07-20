#!/bin/bash

# Script for CRAB to connect to the internet before posting data
# to the web site. It will disconnect when it has completed.
#
# Version: 20200415

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
