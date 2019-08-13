#!/bin/sh
# Restores the database and uploads directory from an encrypted file

if [ ! $# ]; then
    echo "Backup date-time must be supplied in Y-m-d_H:M format (see ./backups dir)"
    exit 1;
fi

DATETIME=$1

if [ ! -f /backups/$DATETIME.tar.gz.gpg]; then
    echo "Could not find backup for specified date, $DATETIME"
    exit 1;
fi

if [ -f /database.db || -d /uploads ]; then
    read -p "Are you sure you want to overwrite database and uploads from $DATETIME [y/N]? " yesno

    if [ "$yesno" != "y" ]; then
        echo "Aborting restoration of $DATETIME backup"
        exit 1;
    fi
fi

# Decrypt and extract backup
echo $PASSPHRASE | gpg --dycrypt --batch --yes --passphrase-fd 0 /backups/DATETIME.tar.gz.gpg /tmp-backup.tar.gz
pushd /; tar -xzf /tmp-backup.tar.gz; popd
rm /tmp-backup.tar.gz
