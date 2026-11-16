import secrets
from django.core.management.base import BaseCommand
from django.utils import timezone
from analytics.models import BetaInvitation


class Command(BaseCommand):
    help = "Generates and initializes 15 controlled invitations for Beta Cohort 1."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=15,
            help='Number of invitations to generate for Cohort 1 (default: 15)'
        )
        parser.add_argument(
            '--cohort',
            type=str,
            default='Cohort 1',
            help='Cohort name identifier (default: Cohort 1)'
        )

    def handle(self, *args, **options):
        count = options['count']
        cohort = options['cohort']

        self.stdout.write(f"\n=======================================================")
        self.stdout.write(f"  SKILLSPHERE BETA INVITATION MANAGER — {cohort.upper()} ")
        self.stdout.write(f"=======================================================\n")

        existing_count = BetaInvitation.objects.filter(cohort_name=cohort).count()
        needed = max(0, count - existing_count)

        if needed == 0:
            self.stdout.write(self.style.SUCCESS(
                f"[OK] {existing_count} invitations already exist for {cohort}."
            ))
        else:
            self.stdout.write(f"Generating {needed} new invitation tokens for {cohort}...")
            created = 0
            for i in range(1, count + 1):
                code = f"BETA-C1-{secrets.token_hex(4).upper()}"
                email = f"cohort1_student_{i:02d}@skillsphere.beta"
                obj, was_created = BetaInvitation.objects.get_or_create(
                    code=code,
                    defaults={
                        'email': email,
                        'cohort_name': cohort,
                        'status': 'pending',
                        'notes': f'Controlled Beta Cohort 1 Student #{i:02d}'
                    }
                )
                if was_created:
                    created += 1

            self.stdout.write(self.style.SUCCESS(f"[SUCCESS] Created {created} invitation tokens.\n"))

        invitations = BetaInvitation.objects.filter(cohort_name=cohort).order_by('id')
        self.stdout.write(f"Total Active Invitations for {cohort}: {invitations.count()}\n")
        self.stdout.write(f"{'Code':<20} | {'Status':<10} | {'Assigned Email':<35} | {'Invite Link'}")
        self.stdout.write("-" * 95)
        for inv in invitations[:20]:
            invite_url = f"/accounts/invite/{inv.code}/"
            self.stdout.write(f"{inv.code:<20} | {inv.status:<10} | {inv.email:<35} | {invite_url}")

        self.stdout.write("\nAll invite codes initialized and ready for distribution.\n")
