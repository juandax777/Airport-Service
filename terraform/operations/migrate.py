"""Apply the versioned SQL of one service using its PostgreSQL migration role."""

import argparse
import hashlib
import os
from pathlib import Path

import psycopg
from psycopg import sql

SERVICES = {
    "itineraries": "itinerary_service",
    "notifications": "notification_service",
}


def migrate(database: str) -> None:
    repo = Path(__file__).resolve().parents[2]
    files = sorted((repo / "services" / SERVICES[database] / "migrations").glob("*.sql"))
    if not files:
        raise RuntimeError("No se encontraron migraciones SQL")

    # libpq reads host, port, role and TLS settings from the environment.
    with psycopg.connect(dbname=database) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT current_user")
        if cursor.fetchone()[0] != f"{database}_migrator":
            raise RuntimeError("La conexión debe usar el rol de migración del servicio")

        cursor.execute("SELECT pg_advisory_xact_lock(1937010521)")
        cursor.execute("SET LOCAL search_path TO public")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS migrations.applied (
                version text PRIMARY KEY,
                sha256 text NOT NULL
            )
            """
        )
        cursor.execute("SELECT version, sha256 FROM migrations.applied")
        applied = dict(cursor.fetchall())
        scripts = {path.name: path.read_text(encoding="utf-8") for path in files}
        hashes = {
            name: hashlib.sha256(script.encode("utf-8")).hexdigest()
            for name, script in scripts.items()
        }
        for name, digest in applied.items():
            if hashes.get(name) != digest:
                raise RuntimeError(f"Se modificó o eliminó una migración aplicada: {name}")
        cursor.execute(
            sql.SQL(
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT "
                f"{'SELECT, INSERT, UPDATE, DELETE' if database == 'itineraries' else 'SELECT, INSERT'} "
                "ON TABLES TO {}"
            ).format(sql.Identifier(f"{database}_app"))
        )
        for name, script in scripts.items():
            if name in applied:
                continue
            cursor.execute(script, prepare=False)
            cursor.execute(
                "INSERT INTO migrations.applied (version, sha256) VALUES (%s, %s)",
                (name, hashes[name]),
            )
    print(f"Migraciones al día para {database}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", choices=SERVICES)
    args = parser.parse_args()
    if os.environ.get("PGSSLMODE") != "verify-full":
        parser.error("Configura PGSSLMODE=verify-full y el certificado de RDS.")
    migrate(args.database)
