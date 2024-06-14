from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Set up roles and permissions'

    def handle(self, *args, **options):
        permissions = [
            'can_upload_file',
            'can_create_folder',
            'can_delete',
            'can_ban_user',
            'can_approve_user',
            'can_delete_user',
            'can_view',
            'can_download',
            'can_create_user',
        ]

        content_type = ContentType.objects.get_for_model(User)

        # Create permissions
        for perm in permissions:
            Permission.objects.get_or_create(codename=perm, name=f'Can {perm.replace("_", " ")}', content_type=content_type)

        roles_permissions = {
            'Admin': [
                'can_upload_file',
                'can_create_folder',
                'can_delete',
                'can_ban_user',
                'can_approve_user',
                'can_delete_user',
                'can_view',
                'can_download',
                'can_create_user',
            ],
            'Editor': [
                'can_upload_file',
                'can_create_folder',
                'can_delete',
                'can_view',
                'can_download',
            ],
            'Staff': [
                'can_view',
                'can_download',
            ],
        }

        for role, perms in roles_permissions.items():
            group, created = Group.objects.get_or_create(name=role)
            for perm in perms:
                permission = Permission.objects.get(codename=perm)
                group.permissions.add(permission)

        self.stdout.write(self.style.SUCCESS('Successfully set up roles and permissions'))
