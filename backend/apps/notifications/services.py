def notify_user(user, notif_type, message, link=""):
    from apps.notifications.models import Notification

    if user is None:
        return None
    return Notification.objects.create(user=user, type=notif_type, message=message, link=link)


def notify_role(role, notif_type, message, link=""):
    from apps.authentication.models import User

    users = User.objects.filter(role=role, is_active=True)
    for user in users:
        notify_user(user, notif_type, message, link=link)
