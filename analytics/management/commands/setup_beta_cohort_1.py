import hashlib
import secrets
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from analytics.models import BetaInvitation


class Command(BaseCommand):
    help = "Revokes exposed tokens and securely generates new 128+ bit hashed invitations for Beta Cohort 1."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=15,
            help='Number of secure invitations to generate for Cohort 1 (default: 15)'
        )
        parser.add_argument(
            '--cohort',
            type=str,
            default='Cohort 1',
            help='Cohort name identifier (default: Cohort 1)'
        )
        parser.add_argument(
            '--revoke-previous',
            action='store_true',
            default=True,
            help='Revoke any previously exposed unused tokens (default: True)'
        )

    def handle(self, *args, **options):
        count = options['count']
        cohort = options['cohort']
        revoke_previous = options['revoke_previous']

        self.stdout.write(f"\n=======================================================")
        self.stdout.write(f"  SKILLSPHERE BETA INVITATION MANAGER — {cohort.upper()} ")
        self.stdout.write(f"=======================================================\n")

        # 1. Revoke exposed previous tokens
        if revoke_previous:
            revoked_count = BetaInvitation.objects.filter(
                cohort_name=cohort,
                status__in=['pending', 'created', 'sent']
            ).update(status='revoked')
            if revoked_count > 0:
                self.stdout.write(self.style.WARNING(
                    f"[SECURITY NOTICE] Revoked {revoked_count} previously exposed unused tokens for {cohort}."
                ))

        # 2. Generate cryptographically secure invitations (160+ bits entropy, SHA-256 hashed)
        self.stdout.write(f"\nGenerating {count} fresh cryptographically secure invitations...")
        self.stdout.write(f"(Tokens have 160+ bits of entropy, stored as SHA-256 hashes, with 7-day TTL)\n")

        issued_records = []
        now = timezone.now()
        expires_at = now + timedelta(days=7)

        for i in range(1, count + 1):
            # 24 url-safe bytes = 192 bits of entropy
            raw_random = secrets.token_urlsafe(24)
            raw_token = f"c1_{raw_random}"
            token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
            token_prefix = raw_token[:10]
            display_code = f"BETA-C1-{secrets.token_hex(4).upper()}"
            bound_email = f"student_{i:02d}@skillsphere.app"

            invitation = BetaInvitation.objects.create(
                email=bound_email,
                code=display_code,
                token_hash=token_hash,
                token_prefix=token_prefix,
                cohort_name=cohort,
                status='created',
                expires_at=expires_at,
                notes=f'Controlled Beta Cohort 1 Student #{i:02d}'
            )

            issued_records.append({
                'num': i,
                'email': bound_email,
                'raw_token': raw_token,
                'display_code': display_code,
                'token_prefix': token_prefix,
                'token_hash': token_hash,
                'expires_at': expires_at,
            })

        self.stdout.write(self.style.SUCCESS(f"[SUCCESS] Issued {len(issued_records)} secure invitations.\n"))

        self.stdout.write("----------------------------------------------------------------------------------------------------------")
        self.stdout.write(" # | BOUND EMAIL               | RAW TOKEN (SHOW ONCE TO OPERATOR)       | PREFIX     | EXPIRES (7-DAY TTL)")
        self.stdout.write("----------------------------------------------------------------------------------------------------------")
        for rec in issued_records:
            self.stdout.write(
                f"{rec['num']:2d} | {rec['email']:<25} | {rec['raw_token']:<41} | {rec['token_prefix']:<10} | {rec['expires_at'].strftime('%Y-%m-%d %H:%M')}"
            )
        self.stdout.write("----------------------------------------------------------------------------------------------------------\n")
        self.stdout.write(self.style.NOTICE(
            "IMPORTANT: Raw tokens are NOT stored in the database. Only their SHA-256 hashes are persisted.\n"
            "Distribute the private URLs to students securely: https://skillsphere.app/accounts/invite/<RAW_TOKEN>/\n"
        ))
