#!/bin/bash

# Get conf setting if there
if [ -f "/etc/toplogger/conf" ]; then
  interval=$(grep interval_seconds /etc/toplogger/conf | awk '{print $2}')

  # Wrong conf setting defaults to 60
  if [ $interval -gt 3600 ] || [ $interval -lt 30 ]; then
    interval=60    
  fi
else

  # No conf defaults to 60
  interval=60
fi

# The interval setting is done before the loop starts, so the script will need to be re-started before an config changes take effect; this means using `systemctl restart toplogger`

# Start an infinite loop with `while :`
while :; do
  # Always ensure the directory exists
  /usr/bin/mkdir -p /var/log/toplogger
  if [ -d "/var/log/toplogger" ]; then
    # Set some important dates with command substitutes inside command substitutes
    this_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) 0 month" +%B`
    last_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) -1 month" +%B`
    last_last_month=`/usr/bin/date -d "$(/usr/bin/date +%Y-%m-1) -2 month" +%B`
    time_stamp="$(/usr/bin/date +%Y-%m-%d_%H:%M:%S)"
    /usr/bin/mkdir -p /var/log/toplogger/${this_month}
    # Remove logs older than one month
    if [ ! -d "/var/log/toplogger/${this_month}" ] && [ -d "/var/log/toplogger/${last_month}" ]; then
      /usr/bin/rm -rf /var/log/toplogger/${last_last_month}
    fi
    # Make the log from one, single `top` iteration
    if [ -d "/var/log/toplogger" ]; then
      top -b -n 1 > /var/log/toplogger/${this_month}/${time_stamp}
    fi
  fi
  # Wait 60 seconds before looping again
  sleep $interval
done