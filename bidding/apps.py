from django.apps import AppConfig


class BiddingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bidding"
    def ready(self):
        import bidding.signals  # Import signals.py when app starts
