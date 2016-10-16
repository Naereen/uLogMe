#!/bin/bash
# keyfreq.sh for https://github.com/Naereen/uLogMe/
# MIT Licensed, https://lbesson.mit-license.org/
#
# Logs the key press frequency over 10 second window.
# Logs are written in logs/keyfreqX.txt every 10 seconds, where X is unix timestamp of 7am of the recording day.

# LANG=en_US.utf8
LANG=en

helperfile="../logs/keyfreqraw.txt"  # temporary helper file

mkdir -p ../logs

while true; do
    showkey | tr -d '0-9' &> $helperfile &
    PID=$!

    # work in windows of 10 seconds
    kill $(jobs -rp)
    wait $(jobs -rp) 2>/dev/null
    # count number of key release events
    num=$(grep -c release "$helperfile")

    # append unix time stamp and the number into file
    logfile="../logs/keyfreq_$(python rewind7am.py).txt"
    echo "$(date +%s) $num"  >> $logfile
    # only print if $num > 0
    if [ $num -gt 0 ]; then
        echo "logged key frequency: $(date) $num release events detected into $logfile"
    fi
done

