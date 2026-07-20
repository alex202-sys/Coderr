#!/bin/bash

echo "Database Backup started"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Backup-Name (Format: db-backup__JAHR-MONAT-TAG__STUNDE-MINUTE.db)
BACKUP_NAME="db-backup__$(date "+%F__%H-%M").db"

cp "$SCRIPT_DIR/../Backend/db.sqlite3" "$BACKUP_NAME"
echo "Uploading file: $BACKUP_NAME"

echo "
 verbose
 open BACKUP_SERVER.com
 user USER_NAME PASSWORT
 bin
 put $BACKUP_NAME
 bye
" | ftp -n > ftp_$$.log
echo "Backup successful"

rm $BACKUP_NAME
rm ftp_$$.log
