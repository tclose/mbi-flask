#!/bin/sh

DATETIME=$(date +%Y-%m-%d_%H:%M)

# Compress, encrypt backup of database and uploads directory
tar -czf /tmp.tar.gz /database.db /uploads
echo $PASSPHRASE | gpg --symmetric --batch --yes --passphrase-fd 0 /tmp-backup.tar.gz /backups/$DATETIME.tar.gz.gpg
rm /tmp-backup.tar.gz
