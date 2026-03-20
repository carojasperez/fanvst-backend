from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = 'notifications'
    verbose_name = 'Staff Notifications'

    def ready(self):
        import notifications.signals  # noqa: F401
