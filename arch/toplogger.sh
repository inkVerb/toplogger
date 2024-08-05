#!/bin/bash

if [ -f "/etc/toplogger/conf" ]; then
  interval=$(grep interval_seconds /etc/toplogger/conf | awk '{print $2}')
  if [ $interval -gt 3600 ] || [ $interval -lt 30 ]; then
    interval=60    
  fi
else
  interval=60
fi

if [ -f "/etc/toplogger/logdir" ]; then
  logdir=$(cat /etc/toplogger/logdir | awk '{print $1}')
else
  logdir="/var/log/toplogger"
fi

while :; do
  /usr/bin/mkdir -p $logdir
  if [ -d "$logdir" ]; then
    this_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) 0 month" +%B`
    last_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) -1 month" +%B`
    last_last_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) -2 month" +%B`
    time_stamp="$(/usr/bin/date +%Y-%m-%d_%H:%M:%S)"
    /usr/bin/mkdir -p $logdir/${this_month}
    if [ ! -d "$logdir/${this_month}" ] && [ -d "$logdir/${last_month}" ]; then
      /usr/bin/rm -rf $logdir/${last_last_month}
    fi
    if [ -d "$logdir" ]; then
      top -b -n 1 > $logdir/${this_month}/${time_stamp}
    fi
  fi
  sleep $interval
done