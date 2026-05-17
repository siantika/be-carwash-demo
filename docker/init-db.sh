#!/bin/sh
set -eu

required_tables_sql="
SELECT CASE WHEN
  EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='identity' AND table_name='accounts')
  AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='identity' AND table_name='devices')
  AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='identity' AND table_name='refresh_tokens')
  AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='service_catalog' AND table_name='service_types')
  AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='carwash_operation' AND table_name='tickets')
  AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='billing' AND table_name='payments')
THEN 1 ELSE 0 END
"

export PGPASSWORD="${DB_PASSWORD}"

is_ready="$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -tAc "${required_tables_sql}" | tr -d '[:space:]')"

if [ "${is_ready}" = "1" ]; then
  echo "Schema already exists, skipping schema.sql import."
  exit 0
fi

echo "Importing schema.sql into ${DB_NAME}..."
sed \
  -e '/^\\restrict /d' \
  -e '/^\\unrestrict /d' \
  -e '/^ALTER .* OWNER TO /d' \
  /schema.sql \
  | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}"

echo "Schema import completed."
