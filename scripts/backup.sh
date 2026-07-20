#!/bin/bash

echo "Database Backup started"

# Pfad des Skripts auf dem Google-Server ermitteln
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Backup-Name generieren (Format: db-backup__JAHR-MONAT-TAG__STUNDE-MINUTE.db)
BACKUP_NAME="db-backup__$(date "+%F__%H-%M").db"

# Lokale Kopie der DB auf dem Google-Server erstellen
# cp "$SCRIPT_DIR/../db.db" "$BACKUP_NAME"
cp "$SCRIPT_DIR/../Backend/db.sqlite3" "$BACKUP_NAME"
echo "Uploading file: $BACKUP_NAME"

# SFTP-Upload zur DockStar über die INTERNE IP und den NEUEN BENUTZER
# Nutzt gezielt den RSA-Schlüssel und erzwingt die Kompatibilität für das alte Debian
sftp -i ~/.ssh/id_rsa -oKexAlgorithms=+diffie-hellman-group1-sha1 -oHostKeyAlgorithms=+ssh-rsa -oPubkeyAcceptedKeyTypes=+ssh-rsa aleksandr_ogloblin_job@192.168.35.55 <<EOF
cd /media/storage/Backup/
put $BACKUP_NAME
bye
EOF

# Überprüfen, ob der SFTP-Upload erfolgreich war (Exit-Code 0)
if [ $? -eq 0 ]; then
    echo "Backup successful"
    rm "$BACKUP_NAME"
else
    echo "Backup failed!"
    exit 1
fi
