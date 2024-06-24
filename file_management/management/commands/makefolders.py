import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Create media, trash, and logs directories with appropriate permissions'

    def handle(self, *args, **kwargs):
        directories = ['media', 'trash', 'logs']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                os.chmod(directory, 0o777)  # Set permissions to 777
                self.stdout.write(self.style.SUCCESS(f'Successfully created directory: {directory} with permissions 777'))
            else:
                os.chmod(directory, 0o777)  # Ensure permissions are set to 777
                self.stdout.write(self.style.WARNING(f'Directory already exists: {directory}, set permissions to 777'))
