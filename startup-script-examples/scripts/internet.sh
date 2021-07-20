#!/bin/bash

# Set the profile name for wvdial:
DIALPROFILE=internet

case "$1" in
  --connect)
    sudo wvdial pin &
    wait
    sudo wvdial $DIALPROFILE &
    sleep 30
    sudo route add default dev ppp0
    exit 0
    ;;
  --disconnect)
    sudo killall -9 pppd wvdial
    exit 0
    ;;
  *)
    Usage: --connect or --disconnect
    exit 1
    ;;
esac
