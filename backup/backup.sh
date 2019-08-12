BACKUP_FILE=$(date +%Y-%m-%d_%H:%M).tar.gz

# start backup

# compress and Copy backup to storage
tar -czf /backups/$BACKUP_FILE $DB_FILE


