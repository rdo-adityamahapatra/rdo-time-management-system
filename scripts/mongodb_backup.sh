#!/usr/bin/env bash
# Backup script for MongoDB database "time_management_system"

# Set variables
DB_NAME="time_management_system"
COLLECTIONS=("users" "time_logs")
BACKUP_DIR="/home/aditya/Dev/Python/rdo-time-management-system/backups/$(date +%Y-%m-%d_%H-%M-%S)"
MONGO_HOST="localhost"
MONGO_PORT="27017"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Loop through collections and dump each one
for COLLECTION in "${COLLECTIONS[@]}"; do
    mongodump --host "$MONGO_HOST" --port "$MONGO_PORT" \
        --db "$DB_NAME" --collection "$COLLECTION" \
        --out "$BACKUP_DIR"
done

# Optional: Remove backups older than 7 days
find /home/aditya/Dev/Python/rdo-time-management-system/backups/ -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +

# Log backup completion
echo "MongoDB backup completed at $(date) in $BACKUP_DIR"
