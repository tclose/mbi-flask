#!/bin/bash
# Restores the database and uploads directory from an encrypted file

set -e  # Exit on errors

if [ ! $# ]; then
    echo "Backup date-time must be supplied in Y-m-d_H:M format (see ./backups dir)"
    exit 1;
fi

BACKUP_DATETIME=$1
DATETIME=$(date +%Y-%m-%d_%H:%M)

if [ ! -f /backups/$BACKUP_DATETIME.tar.gz.gpg ]; then
    echo "Could not find backup for specified date, $BACKUP_DATETIME"
    exit 1;
fi


# Decrypt and extract backup
mkdir /restore-dir
cd /restore-dir
cp /backups/$BACKUP_DATETIME.tar.gz.gpg tmp.tar.gz.gpg
echo $PASSPHRASE | gpg --batch --yes --passphrase-fd 0 -d tmp.tar.gz.gpg > tmp.tar.gz
tar -xzf tmp.tar.gz

# Rename database and archive and remove uploads directory to make way for
# restored databases
if [ -f /database.db ] || [ -d /uploads ]; then
    read -p "Are you sure you want to overwrite database and uploads from $BACKUP_DATETIME [y/N]? " yesno

    if [ "$yesno" == "y" ]; then
        mv /databases/app.db /databases/app-$DATETIME.db
        tar czf /databases/uploads-$DATETIME.tar.gz /uploads
        rm -r /uploads
    else
        echo "Aborting restoration of $BACKUP_DATETIME backup"
        exit 1;
    fi
fi

# Restore extracted backup to original location
mv databases/app.db /databases/app.db
mv uploads /uploads

# Clean up tmp dir
cd /
rm -r /restore-dir

echo "Successfully restored backup of database and uploads directory from $BACKUP_DATETIME"
echo "The overwritten database and uploads directory were moved to "
echo "<PKG-ROOT>/overwritten/app-$DATETIME.db and <PKG-ROOT>/overwritten/uploads-$DATETIME, respectively"
