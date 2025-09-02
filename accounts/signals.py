from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

@receiver(post_migrate)
def create_groups_and_permissions(sender, **kwargs):
    # Get the actual model class from the app registry
    CustomUser = apps.get_model('accounts', 'CustomUser')

    if not CustomUser:
        print("CustomUser model not available yet.")
        return

    try:
        content_type = ContentType.objects.get_for_model(CustomUser)
    except Exception as e:
        print("ContentType not available yet:", e)
        return

    # Create groups
    admin_group, _ = Group.objects.get_or_create(name='Admin')
    viewer_group, _ = Group.objects.get_or_create(name='Viewer')

    # Permissions
    all_perms = Permission.objects.filter(content_type=content_type)
    view_perms = all_perms.filter(codename__startswith='view')

    admin_group.permissions.set(all_perms)
    viewer_group.permissions.set(view_perms)
