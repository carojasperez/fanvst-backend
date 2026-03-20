from django.apps import AppConfig


class WalletConfig(AppConfig):
    name = 'wallet'
    verbose_name = 'Artist Wallet'

    def ready(self):
        import wallet.signals  # noqa: F401
