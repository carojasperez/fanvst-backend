"""
Señales del sistema de wallets.

- Crea ArtistWallet automáticamente cuando Profile.is_artist se activa.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from adminsite.userinfo.models import Profile


@receiver(post_save, sender=Profile)
def create_wallet_for_artist(sender, instance, **kwargs):
    """
    Si el perfil tiene is_artist=True y el usuario aún no tiene wallet,
    la crea automáticamente con la moneda por defecto (USD).
    """
    if not instance.is_artist:
        return

    from wallet.models import ArtistWallet
    ArtistWallet.objects.get_or_create(
        artist=instance.user,
        defaults={'currency': 'USD'},
    )
