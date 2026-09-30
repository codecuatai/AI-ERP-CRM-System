#!/bin/sh
set -eu

psql --set=ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set=crm_database="$POSTGRES_DB" \
  --set=crm_app_user="$CRM_DB_USER" \
  --set=crm_app_password="$CRM_DB_PASSWORD" \
  --set=readonly_password="$SUPERSET_READONLY_PASSWORD" <<'SQL'
CREATE ROLE :"crm_app_user" LOGIN CREATEDB PASSWORD :'crm_app_password';
CREATE ROLE superset_ro LOGIN PASSWORD :'readonly_password';
ALTER DATABASE :"crm_database" OWNER TO :"crm_app_user";
ALTER SCHEMA public OWNER TO :"crm_app_user";
GRANT CONNECT ON DATABASE :"crm_database" TO superset_ro;
SQL
