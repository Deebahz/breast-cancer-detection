from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import EmailOTP
import datetime

class Command(BaseCommand):
    help = 'Clean up expired OTP records from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Delete OTP records older than this many days (default: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Calculate cutoff time
        cutoff_time = timezone.now() - datetime.timedelta(days=days)
        
        # Find expired OTP records
        expired_otps = EmailOTP.objects.filter(created_at__lt=cutoff_time)
        
        count = expired_otps.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} OTP records older than {days} day(s)'
                )
            )
            if count > 0:
                self.stdout.write(
                    self.style.NOTICE(
                        f'Oldest record: {expired_otps.earliest("created_at").created_at}'
                    )
                )
                self.stdout.write(
                    self.style.NOTICE(
                        f'Newest record to be deleted: {expired_otps.latest("created_at").created_at}'
                    )
                )
        else:
            # Actually delete the records
            deleted_count, _ = expired_otps.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} OTP records older than {days} day(s)'
                )
            )
