"""
create_default_user.py — Creates a default admin account on first deploy.
Run automatically during build or call manually:
  python manage.py create_default_user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = 'Create default admin user for first deployment'

    def handle(self, *args, **options):
        import os
        email    = os.environ.get('DEFAULT_ADMIN_EMAIL',    'admin@sfda.gov.sa')
        password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'SFDAadmin2025!')
        username = email.split('@')[0]

        if User.objects.filter(email=email).exists():
            self.stdout.write(f'ℹ️  Admin user already exists: {email}')
        else:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            Token.objects.get_or_create(user=user)
            self.stdout.write(self.style.SUCCESS(
                f'✅ Created admin user: {email} / {password}\n'
                f'   ⚠️  Change this password immediately after first login!'
            ))
