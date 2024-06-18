from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Set up roles, permissions, and demo users'

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

        # Create demo users
        demo_users = {
            'superadmin': {'username': 'superadmin', 'email': 'superadmin@example.com', 'password': '12345678', 'is_superuser': True, 'is_staff': True},
            'admin': {'username': 'admin', 'email': 'admin@example.com', 'password': '12345678', 'groups': ['Admin']},
            'editor': {'username': 'editor', 'email': 'editor@example.com', 'password': '12345678', 'groups': ['Editor']},
            'staff': {'username': 'staff', 'email': 'staff@example.com', 'password': '12345678', 'groups': ['Staff']},
        }

        for user_key, user_data in demo_users.items():
            user, created = User.objects.get_or_create(username=user_data['username'], defaults={'email': user_data['email']})
            if created:
                user.set_password(user_data['password'])
                user.is_superuser = user_data.get('is_superuser', False)
                user.is_staff = user_data.get('is_staff', False)
                user.save()
                if 'groups' in user_data:
                    for group_name in user_data['groups']:
                        group = Group.objects.get(name=group_name)
                        user.groups.add(group)
        
        self.stdout.write(self.style.SUCCESS('Successfully set up roles, permissions, and demo users'))
