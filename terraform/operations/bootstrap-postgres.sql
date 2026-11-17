\set ON_ERROR_STOP on
\set app_role :db '_app'
\set migration_role :db '_migrator'
\set db_valid false
SELECT :'db' IN ('itineraries', 'notifications') AS db_valid \gset
\if :db_valid
\else
  DO $$ BEGIN RAISE EXCEPTION 'Indica -v db=itineraries o -v db=notifications'; END $$;
\endif

SELECT format('CREATE ROLE %I LOGIN', role_name)
FROM (VALUES (:'app_role'), (:'migration_role')) AS roles(role_name)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name)
\gexec

SELECT format('CREATE DATABASE %I', :'db')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'db')
\gexec

REVOKE ALL ON DATABASE :"db" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"db" TO :"app_role", :"migration_role";
\connect :db
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO :"app_role";
GRANT USAGE, CREATE ON SCHEMA public TO :"migration_role";
CREATE SCHEMA IF NOT EXISTS migrations;
REVOKE ALL ON SCHEMA migrations FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA migrations TO :"migration_role";

-- psql solicita cada contraseña de forma interactiva sin mostrarla en pantalla.
\password :app_role
\password :migration_role
