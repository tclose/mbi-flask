BACKUP_FILE="/backups/$(date +%Y-%m-%d_%H:%M).tar.gz"
DB_FILE="/database.db"

# start backup

# compress and Copy backup to storage
tar -czf $BACKUP_FILE $DB_FILE
mv $DB_FILE /backups/


