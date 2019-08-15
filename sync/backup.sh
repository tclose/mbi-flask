#!/bin/bash

set -e  # Exit on errors

DATETIME=$(date +%Y-%m-%d_%H:%M)

# Compress, encrypt backup of database and uploads directory
tar -czf tmp.tar.gz databases/app.db uploads
echo $PASSPHRASE | gpg --batch --yes --passphrase-fd 0 --symmetric /tmp.tar.gz

# Move encrypted backup to 'backups' directory and clean up tmp file
mv /tmp.tar.gz.gpg /backups/$DATETIME.tar.gz.gpg
rm /tmp.tar.gz

echo "Successfully backed up database and uploads directory at $DATETIME"
