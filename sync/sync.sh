#!/bin/bash

# Trigger import from filemaker
status=$(curl -s -o /output.html -w "%{http_code}" http://web:8000/reporting/import)

if [ "$status" != 200 ]; then
    echo "Import from filemaker failed with status $status";
    echo "------------------------------------------------"
    cat /output.html
    exit 1;
fi

# Trigger export of data from MBI-XNAT to Alfred-XNAT
status=$(curl -s -o cat /output.html -w "%{http_code}" http://web:8000/reporting/export)

if [ "$status" != 200 ]; then
    echo "Export from MBI to Alfred XNATs failed with status $status";
    echo "----------------------------------------------------------"
    cat /output.html
    exit 1;
fi