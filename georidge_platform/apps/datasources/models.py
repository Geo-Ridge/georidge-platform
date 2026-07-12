from django.db import models
from georidge_platform.apps.accounts.models import Tenant


class ConnectionProfile(models.Model):
    class ConnectionType(models.TextChoices):
        POSTGIS = "postgis", "PostGIS"
        GEOPACKAGE = "geopackage", "GeoPackage"
        SPATIALITE = "spatialite", "SpatiaLite"
        WMS = "wms", "WMS"
        WFS = "wfs", "WFS"
        XYZ = "xyz", "XYZ Tiles"
        RASTER = "raster", "Raster"

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="connection_profiles",
    )
    name = models.CharField(max_length=255)
    connection_type = models.CharField(max_length=20, choices=ConnectionType.choices)
    host = models.CharField(max_length=255, blank=True)
    port = models.IntegerField(null=True, blank=True)
    database = models.CharField(max_length=255, blank=True)
    schema = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
