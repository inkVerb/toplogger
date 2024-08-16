#include <tunables/global>

/usr/lib/toplogger/toplogger.sh {
    # Include necessary abstractions
    #include <abstractions/base>
    
    # Allow read access to configuration files
    /etc/toplogger/** r,

    # Allow read & write access to log files
    /var/log/toplogger/** rw,
    
    # Allow execution of the script
    /usr/lib/toplogger/toplogger.sh ix,
    
    # Allow read access to the service file
    /usr/lib/systemd/system/toplogger.service r,
    
    # Deny everything else by default
    deny /etc/** w,
    deny /usr/** w,
    deny /var/** w,
}
