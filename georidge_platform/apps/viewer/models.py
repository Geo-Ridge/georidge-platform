import logging
import urllib.request

from django.core.files.base import ContentFile
from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
from georidge_platform.apps.accounts.models import Tenant

logger = logging.getLogger(__name__)


class BaseMap(models.Model):
    class Type(models.TextChoices):
        XYZ = "xyz", "XYZ"

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.XYZ)
    url = models.CharField(max_length=1024, help_text="Tile URL template, e.g. https://tile.openstreetmap.org/{z}/{x}/{y}.png")
    attribution = models.CharField(max_length=1024, blank=True, default="")
    thumbnail = models.ImageField(upload_to="basemaps/thumbnails/", blank=True)
    min_zoom = models.IntegerField(default=0)
    max_zoom = models.IntegerField(default=19)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="base_maps",
        help_text="Leave blank for global (available to all tenants).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def generate_thumbnail(self):
        url = self.url.replace("{z}", "4").replace("{x}", "8").replace("{y}", "5").replace("{s}", "a")
        try:
            req = urllib.request.Request(url, method="GET", headers={"User-Agent": "GeoRidge/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                ct = resp.headers.get_content_type()
                ext_map = {"image/png": "png", "image/jpeg": "jpg", "image/gif": "gif", "image/webp": "webp"}
                suffix = ext_map.get(ct, "png")
                name = f"{self.pk}_{self.name}_{suffix}" if self.pk else f"new_{suffix}"
                self.thumbnail.save(name, ContentFile(data), save=False)
        except Exception as e:
            logger.warning("Could not generate thumbnail for %s (%s): %s", self.name, url, e)

    def save(self, *args, **kwargs):
        generating = not self.thumbnail
        super().save(*args, **kwargs)
        if generating:
            self.generate_thumbnail()
            if self.thumbnail:
                super().save(update_fields=["thumbnail"])


class LayerSearchConfig(models.Model):
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="search_configs",
    )
    layer_name = models.CharField(max_length=255, null=True, blank=True, default=None, help_text="WMS layer name from QGIS")
    layer_title = models.CharField(max_length=255, blank=True, default="", help_text="Display name from QGIS")
    searchable_fields = models.JSONField(default=list, blank=True, help_text="Currently selected field names")
    available_fields = models.JSONField(default=list, blank=True, help_text="Complete field list from last sync")
    label_template = models.CharField(max_length=512, blank=True, default="{id}", help_text="Template for result labels, e.g. '{owner} - {address}'")
    max_results = models.IntegerField(default=5, help_text="Maximum results per layer")
    active = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "layer_name"]
        unique_together = [("project", "layer_name")]
        verbose_name = "Layer search config"
        verbose_name_plural = "Layer search configs"

    def __str__(self):
        return f"{self.layer_title or self.layer_name} ({self.project.name})"


class ThemeProfile(models.Model):
    class LayoutPreset(models.TextChoices):
        MAPGUIDE = "mapguide", "MapGuide"
        MAPSTORE = "mapstore", "MapStore"
        QWC2 = "qwc2", "QWC2"
        MAP_ONLY = "map-only", "Map Only"

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="themes",
        help_text="Tenant this theme belongs to. Leave blank for global themes available to all tenants.",
    )
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Group whose projects can use this theme. Leave blank for global.",
    )
    logo = models.ImageField(upload_to="themes/logos/", blank=True)

    # 13 core CSS colour variables
    primary_color = models.CharField(max_length=7, default="#0d6efd")
    secondary_color = models.CharField(max_length=7, default="#6c757d")
    background_color = models.CharField(max_length=7, default="#ffffff")
    surface_color = models.CharField(max_length=7, default="#f8f9fa")
    text_color = models.CharField(max_length=7, default="#212529")
    text_muted_color = models.CharField(max_length=7, default="#6c757d")
    border_color = models.CharField(max_length=7, default="#dee2e6")
    toolbar_bg = models.CharField(max_length=7, default="#f8f9fa")
    toolbar_border = models.CharField(max_length=7, default="#dee2e6")
    panel_bg = models.CharField(max_length=7, default="#ffffff")
    panel_border = models.CharField(max_length=7, default="#dee2e6")
    statusbar_bg = models.CharField(max_length=7, default="#f8f9fa")
    statusbar_border = models.CharField(max_length=7, default="#dee2e6")
    accent_color = models.CharField(max_length=7, default="#0d6efd")
    danger_color = models.CharField(max_length=7, default="#dc3545")
    success_color = models.CharField(max_length=7, default="#198754")
    warning_color = models.CharField(max_length=7, default="#ffc107")

    # Tool visibility
    show_legend = models.BooleanField(default=True)
    show_toolbar = models.BooleanField(default=True)
    show_statusbar = models.BooleanField(default=True)
    show_banner = models.BooleanField(default=True)

    # Banner
    banner_title = models.CharField(max_length=255, blank=True, default="",
        help_text="Main banner text. Falls back to project name if blank.")
    banner_subtitle = models.CharField(max_length=255, blank=True, default="",
        help_text="Smaller text displayed below the title.")
    banner_bg = models.CharField(max_length=7, default="#004282")
    banner_text_color = models.CharField(max_length=7, default="#ffffff")
    banner_height = models.PositiveIntegerField(default=60, help_text="Banner height in pixels.")
    banner_image = models.ImageField(upload_to="themes/banners/", blank=True,
        help_text="Background image positioned at the right edge of the banner (e.g., corner graphic).")

    # Icons
    icon_set = models.CharField(max_length=64, default="default",
        help_text="Name of the icon set directory under viewer/static/viewer/icons/.")

    # Layout
    layout_preset = models.CharField(
        max_length=20,
        choices=LayoutPreset.choices,
        default=LayoutPreset.MAPGUIDE,
        help_text="MapGuide: classic dock panel. MapStore: sidebar + floating panels. QWC2: navbar + slide-out panel. Map Only: bare map.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def to_css_vars(self) -> dict[str, str]:
        return {
            "primary": self.primary_color,
            "secondary": self.secondary_color,
            "background": self.background_color,
            "surface": self.surface_color,
            "text": self.text_color,
            "text-muted": self.text_muted_color,
            "border": self.border_color,
            "toolbar-bg": self.toolbar_bg,
            "toolbar-border": self.toolbar_border,
            "panel-bg": self.panel_bg,
            "panel-border": self.panel_border,
            "statusbar-bg": self.statusbar_bg,
            "statusbar-border": self.statusbar_border,
            "accent": self.accent_color,
            "danger": self.danger_color,
            "success": self.success_color,
            "warning": self.warning_color,
            "banner-bg": self.banner_bg,
            "banner-text-color": self.banner_text_color,
            "banner-height": f"{self.banner_height}px",
        }
