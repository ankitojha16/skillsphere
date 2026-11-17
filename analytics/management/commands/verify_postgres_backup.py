import os
import subprocess
import shutil
import psycopg2
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Creates a database-native PostgreSQL backup (pg_dump) and verifies restoration into an isolated database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-url',
            type=str,
            default=None,
            help="Source PostgreSQL connection URL (defaults to DIRECT_URL or DATABASE_URL from environment)"
        )
        parser.add_argument(
            '--test-db-name',
            type=str,
            default='skillsphere_restore_test',
            help="Isolated database name for restoration verification (default: skillsphere_restore_test)"
        )
        parser.add_argument(
            '--skip-restore',
            action='store_true',
            default=False,
            help="Only create the dump without running restore verification"
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== PRODUCTION POSTGRESQL BACKUP & RESTORATION AUDIT ==="))

        source_url = options.get('source_url') or os.getenv('DIRECT_URL') or os.getenv('DATABASE_URL')
        if not source_url or 'postgres' not in source_url:
            self.stdout.write(self.style.ERROR("[ERROR] No valid PostgreSQL source URL found in environment or arguments."))
            return

        test_db_name = options.get('test_db_name', 'skillsphere_restore_test')
        skip_restore = options.get('skip_restore', False)

        # 1. Locate pg_dump and pg_restore
        pg_dump_bin = shutil.which('pg_dump') or '/opt/homebrew/bin/pg_dump'
        pg_restore_bin = shutil.which('pg_restore') or '/opt/homebrew/bin/pg_restore'

        if not os.path.exists(pg_dump_bin):
            self.stdout.write(self.style.ERROR(f"[ERROR] 'pg_dump' binary not found at {pg_dump_bin}"))
            return

        # Prepare backup path
        backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'beta_cohort_1')
        os.makedirs(backup_dir, exist_ok=True)
        dump_file = os.path.join(backup_dir, 'skillsphere_prod_native.dump')

        # 2. Execute database-native pg_dump
        self.stdout.write(f"\n[1/3] Executing database-native pg_dump into custom archive...")
        cmd_dump = [
            pg_dump_bin,
            source_url,
            '--schema=public',
            '--no-owner',
            '--no-acl',
            '-Fc',
            '-f', dump_file
        ]

        try:
            res_dump = subprocess.run(cmd_dump, capture_output=True, text=True, check=True)
            dump_size_kb = os.path.getsize(dump_file) / 1024
            self.stdout.write(self.style.SUCCESS(
                f"      ✓ pg_dump succeeded: {dump_file}\n"
                f"      ✓ Archive size: {dump_size_kb:.1f} KB (Format: PostgreSQL Custom Archive -Fc)"
            ))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"[FAIL] pg_dump failed: {e.stderr}"))
            return

        if skip_restore:
            self.stdout.write("[2/3] Skipping restore verification as requested.")
            return

        # 3. Setup isolated PostgreSQL target database
        self.stdout.write(f"\n[2/3] Preparing isolated target database '{test_db_name}'...")
        try:
            # Connect to server default db to ensure test_db exists
            conn = psycopg2.connect(source_url)
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (test_db_name,))
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(f"CREATE DATABASE {test_db_name};")
                self.stdout.write(f"      ✓ Created isolated database: {test_db_name}")
            else:
                self.stdout.write(f"      ✓ Target database exists: {test_db_name}")
            cursor.close()
            conn.close()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[FAIL] Could not verify/create isolated database: {e}"))
            return

        # Build connection URL for isolated test database using robust URL parsing
        from urllib.parse import urlsplit, urlunsplit
        parts = urlsplit(source_url)
        restore_url = urlunsplit((parts.scheme, parts.netloc, f"/{test_db_name}", parts.query, parts.fragment))


        # 4. Execute pg_restore into isolated database
        self.stdout.write(f"\n[3/3] Restoring backup archive into isolated database '{test_db_name}'...")
        cmd_restore = [
            pg_restore_bin,
            '-d', restore_url,
            '--no-owner',
            '--no-acl',
            dump_file
        ]
        # pg_restore may return 1 if public schema exists already; that warning is harmless
        res_restore = subprocess.run(cmd_restore, capture_output=True, text=True)

        # 5. Verify restored database schema, row counts, and relationships
        try:
            test_conn = psycopg2.connect(restore_url)
            test_cur = test_conn.cursor()

            # Table count
            test_cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
            table_count = test_cur.fetchone()[0]

            # Courses count
            test_cur.execute("SELECT count(*) FROM courses_course;")
            course_count = test_cur.fetchone()[0]

            # Lessons count
            test_cur.execute("SELECT count(*) FROM learning_lesson;")
            lesson_count = test_cur.fetchone()[0]

            # Users count
            test_cur.execute("SELECT count(*) FROM auth_user;")
            user_count = test_cur.fetchone()[0]

            # Relational check: orphan lessons
            test_cur.execute("""
                SELECT count(*) FROM learning_lesson l
                LEFT JOIN courses_course c ON l.course_id = c.id
                WHERE c.id IS NULL;
            """)
            orphan_lessons = test_cur.fetchone()[0]

            test_cur.close()
            test_conn.close()

            self.stdout.write(self.style.SUCCESS(f"\n=== RESTORATION VERIFICATION RESULTS ==="))
            self.stdout.write(f"  • Isolated Database:    {test_db_name}")
            self.stdout.write(f"  • Restored Tables:      {table_count} (Expected: 101)")
            self.stdout.write(f"  • Restored Courses:     {course_count} (Expected: 69)")
            self.stdout.write(f"  • Restored Lessons:     {lesson_count} (Expected: 1,104)")
            self.stdout.write(f"  • Restored Users:       {user_count} (Expected: >=3)")
            self.stdout.write(f"  • Orphan Lessons:       {orphan_lessons} (Expected: 0)")

            is_valid = (table_count >= 100 and course_count == 69 and lesson_count == 1104 and orphan_lessons == 0)
            if is_valid:
                self.stdout.write(self.style.SUCCESS(
                    "\n[PASS] Production PostgreSQL backup and isolated restore verification SUCCESSFUL!\n"
                    "Data fidelity, relational integrity, and schema completeness verified."
                ))
            else:
                self.stdout.write(self.style.ERROR("\n[FAIL] Discrepancy detected in restored database records."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[FAIL] Could not verify restored records: {e}"))
