#!/bin/sh

# create backup-cron file...
echo "$SETUP_CRON root /root/backup.sh > /proc/1/fd/1 2>/proc/1/fd/2" > /etc/cron.d/backup-cron
chmod 0644 /etc/cron.d/backup-cron


# Run cron.....
crond -f
