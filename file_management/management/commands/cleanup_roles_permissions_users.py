from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User

class Command(BaseCommand):
    help = 'Clean up roles, permissions, and demo users'

    def handle(self, *args, **options):
        # List of demo users to delete
        demo_users = ['superadmin', 'admin', 'editor', 'staff']
        
        # List of roles to delete
        roles = ['Admin', 'Editor', 'Staff']
        
        # List of permissions to delete
        permissions = [
            'can_upload_file',
            'can_create_folder',
            'can_delete',
            'can_trash',
            'can_restore',
            'can_view_user',
            'can_view_trash',
            'can_view_logs',
            'can_download',
        ]

        # Delete demo users
        User.objects.filter(username__in=demo_users).delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted demo users'))

        # Delete roles
        Group.objects.filter(name__in=roles).delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted roles'))

        # Delete permissions
        Permission.objects.filter(codename__in=permissions).delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted permissions'))
