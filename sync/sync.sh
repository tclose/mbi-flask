#!/bin/bash

# Trigger import from filemaker
status=$(curl -s -o /dev/null -w "%{http_code}" http://web:8000/reporting/sync-filemaker)

if [ "$status" == 200 ]; then
    echo "$(date +%Y-%m-%d_%H:%M): Import from filemaker was successful "
else
    echo "$(date +%Y-%m-%d_%H:%M): Import from filemaker failed with status $status"
    echo "Run 'docker-compose logs web' for details.";
    exit 1;
fi

# Trigger export of data from MBI-XNAT to Alfred-XNAT
status=$(curl -s -o /dev/null -w "%{http_code}" http://web:8000/reporting/sync-alfred)

if [ "$status" == 200 ]; then
    echo "$(date +%Y-%m-%d_%H:%M): Export from MBI XNAT to Alfred XNAT was successful "
else
    echo "$(date +%Y-%m-%d_%H:%M): Export from MBI XNAT to Alfred XNAT failed with status $status."
    echo "Run 'docker-compose logs web' for details.";
    exit 1;
fi