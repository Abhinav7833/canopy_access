-- Provision the test database on a fresh Postgres volume (mounted into
-- /docker-entrypoint-initdb.d). Inherits PostGIS from template1 (the postgis
-- image installs it there). conftest._ensure_test_database() is the runtime
-- fallback for volumes that were created before this script existed.
CREATE DATABASE canopy_test;
