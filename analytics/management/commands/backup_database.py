import os
import shutil
import hashlib
import sqlite3
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Creates a verified snapshot backup of the database with SHA-256 checksum and retention rotation."

    def add_arguments(self, parser):
        parser.add_argument(
            '--rotate',
            type=int,
            default=10,
            help="Number of latest backups to retain (older backups are pruned). Default is 10."
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            default=True,
            help="Perform SQLite integrity verification on the generated snapshot."
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help="Custom output directory for backups (defaults to backups/beta_cohort_1)."
        )

    def handle(self, *args, **options):
        rotate_count = options['rotate']
        verify = options['verify']
        custom_dir = options.get('output_dir')

        self.stdout.write(self.style.MIGRATE_HEADING("=== SKILLSPHERE DATABASE BACKUP & ROTATION UTILITY ==="))

        db_path = settings.DATABASES['default'].get('NAME', '')
        local_sqlite = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        target_file = None

        if db_path and os.path.exists(str(db_path)):
            target_file = str(db_path)
        elif os.path.exists(local_sqlite):
            target_file = local_sqlite

        if not target_file:
            self.stdout.write(self.style.WARNING(
                f"[INFO] Default database is configured for remote host (NAME: {db_path}) and no local 'db.sqlite3' was found.\n"
                "For managed PostgreSQL (e.g. Supabase / RDS), automated snapshots or 'pg_dump' should be used."
            ))
            return

        # Prepare backup directory
        if custom_dir:
            backup_dir = custom_dir
        else:
            backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'beta_cohort_1')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"db_backup_{timestamp}.sqlite3"
        backup_file_path = os.path.join(backup_dir, backup_filename)

        # 1. Create snapshot
        self.stdout.write(f"[1/3] Copying database snapshot from {os.path.basename(target_file)} to: {backup_filename}...")
        shutil.copyfile(target_file, backup_file_path)

        # 2. Compute SHA-256 and size
        with open(backup_file_path, 'rb') as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        file_size_kb = os.path.getsize(backup_file_path) / 1024

        self.stdout.write(self.style.SUCCESS(
            f"      ✓ Snapshot saved ({file_size_kb:.1f} KB)\n"
            f"      ✓ SHA-256: {sha256}"
        ))

        # 3. Verification
        if verify:
            self.stdout.write("[2/3] Verifying database integrity...")
            try:
                conn = sqlite3.connect(backup_file_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                check_result = cursor.fetchone()
                cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
                table_count = cursor.fetchone()[0]
                conn.close()

                if check_result and check_result[0] == "ok":
                    self.stdout.write(self.style.SUCCESS(
                        f"      ✓ Integrity check PASSED: 'ok' ({table_count} tables verified)"
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f"      ✗ Integrity check WARNING: {check_result}"
                    ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"      ✗ Verification failed: {e}"))
        else:
            self.stdout.write("[2/3] Verification skipped.")

        # 4. Rotation / Retention policy
        self.stdout.write(f"[3/3] Enforcing backup retention policy (max {rotate_count} backups)...")
        existing_backups = []
        for fname in os.listdir(backup_dir):
            if fname.startswith("db_backup_") and fname.endswith(".sqlite3"):
                full_p = os.path.join(backup_dir, fname)
                existing_backups.append((os.path.getmtime(full_p), full_p, fname))

        existing_backups.sort(key=lambda x: x[0])  # Oldest first

        if len(existing_backups) > rotate_count:
            prune_count = len(existing_backups) - rotate_count
            to_prune = existing_backups[:prune_count]
            for _, fpath, fname in to_prune:
                try:
                    os.remove(fpath)
                    self.stdout.write(self.style.NOTICE(f"      - Pruned older snapshot: {fname}"))
                except OSError as e:
                    self.stdout.write(self.style.WARNING(f"      ! Could not remove {fname}: {e}"))
            self.stdout.write(self.style.SUCCESS(f"      ✓ Retention enforced: pruned {prune_count} older backup(s)."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"      ✓ Retention healthy: {len(existing_backups)} of {rotate_count} slots used."
            ))

        self.stdout.write(self.style.SUCCESS("\n[SUCCESS] Backup process completed successfully!"))
