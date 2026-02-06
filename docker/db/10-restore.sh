#!/bin/bash
set -e

echo "Restoring DB from /docker-entrypoint-initdb.d/backup.dump ..."

# DB default yang dipakai init adalah $POSTGRES_DB
pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl /docker-entrypoint-initdb.d/backup.dump
