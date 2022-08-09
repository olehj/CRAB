#!/bin/bash

# Set the profile name for wvdial:
DIALPROFILE=internet
# Set a ping address for connection checking
PINGADDRESS=send.crab.today

case "$1" in
  --connect)
    sudo wvdial -n pin
    sleep 30
    sudo screen -dmS internet wvdial -n $DIALPROFILE
    while ping -q -c 1 -W 60 "$PINGADDRESS" >&/dev/null
    do
      sleep 5
      sudo route add default dev ppp0
      break
    done
    exit 1
    ;;
  --disconnect)
    sudo killall -9 pppd wvdial
    exit 1
    ;;
  *)
    echo "Usage: --connect or --disconnect"
    exit 1
    ;;
esac
