"""
Django management command for manual token refresh
Allows administrators to trigger token refresh outside of scheduled tasks
"""
from django.core.management.base import BaseCommand, CommandError
from apps.tiktok_accounts.services.tiktok_token_refresh_service import TikTokTokenRefreshService


class Command(BaseCommand):
    help = 'Manually trigger TikTok token refresh for expiring accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform dry run without actual refresh',
        )
        parser.add_argument(
            '--account-id',
            type=int,
            help='Refresh specific account by ID',
        )

    def handle(self, *args, **options):
        """Execute token refresh based on provided options"""
        service = TikTokTokenRefreshService()

        if options['account_id']:
            # Refresh specific account
            self.stdout.write(
                self.style.NOTICE(f"Refreshing account {options['account_id']}...")
            )
            try:
                service.refresh_specific_account(options['account_id'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully refreshed account {options['account_id']}"
                    )
                )
            except Exception as e:
                raise CommandError(f"Failed to refresh account: {str(e)}")

        else:
            # Refresh all expiring tokens
            dry_run = options['dry_run']
            mode = "[DRY RUN]" if dry_run else ""
            self.stdout.write(
                self.style.NOTICE(f"{mode} Starting token refresh for expiring accounts...")
            )

            results = service.refresh_expiring_tokens(dry_run=dry_run)

            # Display results
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nRefresh completed:"
                    f"\n  Total: {results['total']}"
                    f"\n  Refreshed: {results['refreshed']}"
                    f"\n  Failed: {results['failed']}"
                )
            )

            if results['errors']:
                self.stdout.write(self.style.WARNING("\nErrors:"))
                for error in results['errors']:
                    self.stdout.write(self.style.ERROR(f"  - {error}"))
