"""
Comando para cargar data demo en la BD local de Fanvst.
Uso: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import models
from django.utils.text import slugify
from decimal import Decimal
import random

from fanvst.models import (
    Genre, ArtistProfile, ArtistFollow,
    Campaign, CampaignContribution,
    FanTier, FanProfile,
)


GENRES = [
    ("Reggaeton", "reggaeton"),
    ("Cumbia", "cumbia"),
    ("Rock Latino", "rock-latino"),
    ("Trap", "trap"),
    ("Salsa", "salsa"),
    ("Pop", "pop"),
    ("Hip-Hop", "hip-hop"),
    ("Electrónica", "electronica"),
]

ARTISTS = [
    {
        "username": "demo_artist_1",
        "handle": "lasantacecilia",
        "stage_name": "La Santa Cecilia",
        "bio": "Banda de rock alternativo con raíces en la música popular latinoamericana. Desde Los Ángeles para el mundo.",
        "artist_type": "band",
        "location": "Los Ángeles, USA",
        "verified": True,
        "genres": ["Rock Latino", "Pop"],
    },
    {
        "username": "demo_artist_2",
        "handle": "natanaelcano",
        "stage_name": "Natanael Cano",
        "bio": "Pionero del corrido tumbado, fusionando la música regional mexicana con el trap moderno.",
        "artist_type": "solo",
        "location": "Hermosillo, México",
        "verified": True,
        "genres": ["Trap", "Reggaeton"],
    },
    {
        "username": "demo_artist_3",
        "handle": "bombaestereo",
        "stage_name": "Bomba Estéreo",
        "bio": "Dúo colombiano que mezcla cumbia, electrónica y rock. Sonido único que representa a Latinoamérica.",
        "artist_type": "duo",
        "location": "Bogotá, Colombia",
        "verified": True,
        "genres": ["Cumbia", "Electrónica"],
    },
    {
        "username": "demo_artist_4",
        "handle": "denguedengue",
        "stage_name": "Dengue Dengue Dengue",
        "bio": "Colectivo de música electrónica peruana que mezcla ritmos amazónicos con producción contemporánea.",
        "artist_type": "collective",
        "location": "Lima, Perú",
        "verified": False,
        "genres": ["Electrónica", "Cumbia"],
    },
    {
        "username": "demo_artist_5",
        "handle": "monlaferte",
        "stage_name": "Mon Laferte",
        "bio": "Artista chilena que fusiona bolero, rock y pop con una voz inconfundible y letras profundamente personales.",
        "artist_type": "solo",
        "location": "Ciudad de México",
        "verified": True,
        "genres": ["Pop", "Rock Latino"],
    },
    {
        "username": "demo_artist_6",
        "handle": "calle13oficial",
        "stage_name": "Calle 13",
        "bio": "El dúo boricua más importante del siglo XXI. Crítica social, humor y ritmo que define una generación.",
        "artist_type": "duo",
        "location": "San Juan, Puerto Rico",
        "verified": True,
        "genres": ["Reggaeton", "Hip-Hop"],
    },
    {
        "username": "demo_artist_7",
        "handle": "balunmusic",
        "stage_name": "Balún",
        "bio": "Proyecto indie de Puerto Rico que combina texturas electrónicas con letras introspectivas en español.",
        "artist_type": "band",
        "location": "Santurce, Puerto Rico",
        "verified": False,
        "genres": ["Pop", "Electrónica"],
    },
    {
        "username": "demo_artist_8",
        "handle": "meridianbrothers",
        "stage_name": "Meridian Brothers",
        "bio": "Proyecto colombiano de vanguardia liderado por Eblis Álvarez. Música inclasificable y experimental.",
        "artist_type": "band",
        "location": "Bogotá, Colombia",
        "verified": False,
        "genres": ["Cumbia", "Rock Latino"],
    },
]

CAMPAIGNS = [
    {
        "artist_idx": 0,
        "title": "Nuestro próximo álbum independiente",
        "description": "Queremos grabar nuestro tercer álbum de forma completamente independiente. Cada peso va directo a la producción, mezcla y masterización.",
        "goal": Decimal("15000.00"),
        "currency": "USD",
        "raised_pct": 0.67,
    },
    {
        "artist_idx": 1,
        "title": "Tour LATAM 2026",
        "description": "Vamos a llevar el corrido tumbado a 10 ciudades de Latinoamérica. Tu apoyo nos ayuda con la producción del show.",
        "goal": Decimal("25000.00"),
        "currency": "USD",
        "raised_pct": 0.43,
    },
    {
        "artist_idx": 2,
        "title": "Documental: Somos Bomba",
        "description": "Un recorrido por 15 años de música, viajes y resistencia cultural. Producción audiovisual independiente.",
        "goal": Decimal("8000.00"),
        "currency": "USD",
        "raised_pct": 0.89,
    },
    {
        "artist_idx": 4,
        "title": "EP acústico íntimo",
        "description": "Quiero grabar 5 canciones completamente acústicas, solo mi voz y la guitarra. Sin productores, sin filtros.",
        "goal": Decimal("5000.00"),
        "currency": "USD",
        "raised_pct": 0.31,
    },
    {
        "artist_idx": 5,
        "title": "Reedición vinilo 20 años",
        "description": "Celebramos dos décadas con una reedición limitada en vinilo de nuestro álbum debut. Solo 500 copias.",
        "goal": Decimal("12000.00"),
        "currency": "USD",
        "raised_pct": 0.55,
    },
]


class Command(BaseCommand):
    help = "Carga datos demo en la BD local para visualizar la maqueta."

    def handle(self, *args, **options):
        self.stdout.write("🌱 Iniciando seed de datos demo...\n")

        # ── Grupos requeridos por el signal de User ───────────────────────────
        Group.objects.get_or_create(name='general')
        self.stdout.write("  ✓ grupo 'general' listo\n")

        # ── Géneros ──────────────────────────────────────────────────────────
        genre_objs = {}
        for name, slug in GENRES:
            g, created = Genre.objects.get_or_create(slug=slug, defaults={"name": name})
            genre_objs[name] = g
            self.stdout.write(f"  {'✓ creado' if created else '· existe'} género: {name}")

        # ── Fans demo (para follows y contribuciones) ────────────────────────
        fans = []
        for i in range(1, 6):
            u, _ = User.objects.get_or_create(
                username=f"demo_fan_{i}",
                defaults={"email": f"fan{i}@demo.fanvst.com", "first_name": f"Fan{i}"}
            )
            if _:
                u.set_unusable_password()
                u.save()
            fans.append(u)
        self.stdout.write(f"\n  ✓ {len(fans)} fans demo listos")

        # ── Artistas ─────────────────────────────────────────────────────────
        artist_profiles = []
        for data in ARTISTS:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": f"{data['username']}@demo.fanvst.com",
                    "first_name": data["stage_name"].split()[0],
                }
            )
            if created:
                user.set_unusable_password()
                user.save()

            profile, p_created = ArtistProfile.objects.get_or_create(
                user=user,
                defaults={
                    "handle": data.get("handle"),
                    "stage_name": data["stage_name"],
                    "bio": data["bio"],
                    "artist_type": data["artist_type"],
                    "location_display": data["location"],
                    "verified": data["verified"],
                }
            )

            if not p_created:
                # Actualizar campos si ya existía
                profile.handle = data.get("handle")
                profile.stage_name = data["stage_name"]
                profile.bio = data["bio"]
                profile.artist_type = data["artist_type"]
                profile.location_display = data["location"]
                profile.verified = data["verified"]
                profile.save()

            # Asignar géneros
            for gname in data["genres"]:
                if gname in genre_objs:
                    profile.genres.add(genre_objs[gname])

            # Crear follows aleatorios
            random.shuffle(fans)
            n_followers = random.randint(2, len(fans))
            for fan in fans[:n_followers]:
                ArtistFollow.objects.get_or_create(fan=fan, artist=profile)

            artist_profiles.append(profile)
            self.stdout.write(
                f"  {'✓ creado' if p_created else '· actualizado'} artista: {data['stage_name']} "
                f"({profile.followers_count} followers)"
            )

        # ── Campañas ─────────────────────────────────────────────────────────
        self.stdout.write("\n  Creando campañas:")
        for cdata in CAMPAIGNS:
            artist = artist_profiles[cdata["artist_idx"]]
            slug = slugify(cdata["title"])[:48]

            campaign, c_created = Campaign.objects.get_or_create(
                artist=artist,
                title=cdata["title"],
                defaults={
                    "description": cdata["description"],
                    "goal_amount": cdata["goal"],
                    "currency": cdata["currency"],
                    "status": "active",
                    "slug": slug,
                }
            )

            if not c_created:
                campaign.status = "active"
                campaign.save()

            # Crear contribuciones para simular raised_amount
            target_raised = cdata["goal"] * Decimal(str(cdata["raised_pct"]))
            existing = campaign.contributions.filter(confirmed=True).aggregate(
                total=models.Sum("amount")
            )["total"] or Decimal("0")

            remaining = target_raised - existing
            if remaining > 0 and fans:
                per_fan = remaining / len(fans)
                for fan in fans:
                    CampaignContribution.objects.get_or_create(
                        fan=fan,
                        campaign=campaign,
                        defaults={"amount": per_fan.quantize(Decimal("0.01")), "confirmed": True}
                    )

            self.stdout.write(
                f"  {'✓ creada' if c_created else '· existe'} campaña: {cdata['title'][:40]} "
                f"(${campaign.raised_amount:.0f} / ${cdata['goal']:.0f})"
            )

        # ── Tiers de fan ─────────────────────────────────────────────────────
        self.stdout.write("\n  Creando fan tiers:")
        for profile in artist_profiles[:4]:
            FanTier.objects.get_or_create(
                artist=profile,
                name="Fan",
                defaults={
                    "description": "Acceso a contenido exclusivo y actualizaciones antes que nadie.",
                    "price": Decimal("3.00"),
                    "currency": "USD",
                    "is_active": True,
                    "sort_order": 1,
                }
            )
            FanTier.objects.get_or_create(
                artist=profile,
                name="Super Fan",
                defaults={
                    "description": "Todo lo anterior más acceso a livestreams y meet & greet virtual.",
                    "price": Decimal("9.00"),
                    "currency": "USD",
                    "is_active": True,
                    "sort_order": 2,
                }
            )
            self.stdout.write(f"  ✓ tiers para {profile.stage_name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Seed completado: {len(GENRES)} géneros, "
                f"{len(ARTISTS)} artistas, {len(CAMPAIGNS)} campañas."
            )
        )
