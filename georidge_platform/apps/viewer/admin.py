import io
import json
import os
import shutil
import zipfile

from django import forms
from django.contrib import admin, messages
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.html import format_html

from .models import BaseMap, ThemeProfile
from .services import export_theme_zip


ICONS_DIR = os.path.join(os.path.dirname(__file__), "static", "viewer", "icons")

def _get_icon_set_choices():
    choices = []
    if os.path.isdir(ICONS_DIR):
        for entry in sorted(os.listdir(ICONS_DIR)):
            if os.path.isdir(os.path.join(ICONS_DIR, entry)):
                choices.append((entry, entry))
    return choices


@admin.register(ThemeProfile)
class ThemeProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "is_default", "group", "icon_set", "show_banner", "show_toolbar", "show_legend",
                    "show_statusbar", "layout_preset", "updated_at")
    list_filter = ("is_default", "layout_preset", "group")
    search_fields = ("name", "description")
    change_list_template = "admin/viewer/themeprofile/change_list.html"
    change_form_template = "admin/viewer/themeprofile/change_form.html"
    fieldsets = [
        ("General", {
            "fields": ("name", "description", "is_default", "group"),
        }),
        ("Core Colors", {
            "fields": (
                ("primary_color", "secondary_color"),
                ("background_color", "surface_color"),
                ("text_color", "text_muted_color"),
                ("border_color",),
            ),
        }),
        ("UI Element Colors", {
            "fields": (
                ("toolbar_bg", "toolbar_border"),
                ("panel_bg", "panel_border"),
                ("statusbar_bg", "statusbar_border"),
            ),
        }),
        ("Semantic Colors", {
            "fields": (
                ("accent_color", "danger_color"),
                ("success_color", "warning_color"),
            ),
        }),
        ("Banner", {
            "fields": (
                ("show_banner", "banner_title", "banner_subtitle"),
                ("banner_bg", "banner_text_color", "banner_height"),
                "logo", "banner_image",
            ),
        }),
        ("Icons", {
            "fields": ("icon_set",),
        }),
        ("Visibility & Layout", {
            "fields": (
                ("show_toolbar", "show_legend", "show_statusbar"),
                "layout_preset",
            ),
        }),
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:pk>/export/", self.admin_site.admin_view(self.export_view), name="viewer_themeprofile_export"),
            path("import/", self.admin_site.admin_view(self.import_view), name="viewer_themeprofile_import"),
        ]
        return custom + urls

    def export_view(self, request, pk):
        if not request.user.is_staff:
            return redirect("/admin/")
        theme = self.get_object(request, pk)
        if theme is None:
            from django.http import Http404
            raise Http404
        return export_theme_zip(theme)

    def import_view(self, request):
        if not request.user.is_staff:
            return redirect("/admin/")

        if request.method != "POST":
            return render(request, "admin/viewer/themeprofile/import_form.html", {
                "title": "Import Theme ZIP",
                "opts": self.model._meta,
            })

        uploaded = request.FILES.get("theme_zip")
        if not uploaded:
            messages.error(request, "No file uploaded.")
            return redirect("admin:viewer_themeprofile_changelist")

        try:
            zf = zipfile.ZipFile(uploaded, "r")
        except zipfile.BadZipFile:
            messages.error(request, "Invalid ZIP file.")
            return redirect("admin:viewer_themeprofile_changelist")

        try:
            with zf:
                if "theme.json" not in zf.namelist():
                    messages.error(request, "Invalid theme package: theme.json not found")
                    return redirect("admin:viewer_themeprofile_changelist")

                try:
                    data = json.loads(zf.read("theme.json"))
                except (json.JSONDecodeError, ValueError):
                    messages.error(request, "Invalid theme package: theme.json is not valid JSON")
                    return redirect("admin:viewer_themeprofile_changelist")

                icon_files = [n for n in zf.namelist() if n.startswith("icons/") and n != "icons/"]
                if not icon_files:
                    messages.error(request, "Invalid theme package: icons directory not found")
                    return redirect("admin:viewer_themeprofile_changelist")

                theme_name = data.get("name", "")
                if ThemeProfile.objects.filter(name=theme_name).exists():
                    messages.error(request, f"Theme '{theme_name}' already exists. Rename the theme in theme.json and try again.")
                    return redirect("admin:viewer_themeprofile_changelist")

                icon_set = data.get("icon_set", "")
                icon_dest = os.path.join(ICONS_DIR, icon_set)
                if os.path.isdir(icon_dest):
                    messages.error(request, f"Icon set '{icon_set}' already exists. Change the icon_set name in theme.json and try again.")
                    return redirect("admin:viewer_themeprofile_changelist")

                for entry in icon_files:
                    if entry.endswith("/"):
                        continue
                    dest = os.path.join(os.path.dirname(__file__), entry.replace("/", os.sep))
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with zf.open(entry) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)

                theme = ThemeProfile(
                    name=theme_name,
                    description=data.get("description", ""),
                    is_default=False,
                    primary_color=data.get("primary_color", "#0d6efd"),
                    secondary_color=data.get("secondary_color", "#6c757d"),
                    background_color=data.get("background_color", "#ffffff"),
                    surface_color=data.get("surface_color", "#f8f9fa"),
                    text_color=data.get("text_color", "#212529"),
                    text_muted_color=data.get("text_muted_color", "#6c757d"),
                    border_color=data.get("border_color", "#dee2e6"),
                    toolbar_bg=data.get("toolbar_bg", "#f8f9fa"),
                    toolbar_border=data.get("toolbar_border", "#dee2e6"),
                    panel_bg=data.get("panel_bg", "#ffffff"),
                    panel_border=data.get("panel_border", "#dee2e6"),
                    statusbar_bg=data.get("statusbar_bg", "#f8f9fa"),
                    statusbar_border=data.get("statusbar_border", "#dee2e6"),
                    accent_color=data.get("accent_color", "#0d6efd"),
                    danger_color=data.get("danger_color", "#dc3545"),
                    success_color=data.get("success_color", "#198754"),
                    warning_color=data.get("warning_color", "#ffc107"),
                    show_legend=data.get("show_legend", True),
                    show_toolbar=data.get("show_toolbar", True),
                    show_statusbar=data.get("show_statusbar", True),
                    show_banner=data.get("show_banner", True),
                    banner_title=data.get("banner_title", ""),
                    banner_subtitle=data.get("banner_subtitle", ""),
                    banner_bg=data.get("banner_bg", "#004282"),
                    banner_text_color=data.get("banner_text_color", "#ffffff"),
                    banner_height=data.get("banner_height", 60),
                    icon_set=icon_set,
                    layout_preset=data.get("layout_preset", "mapguide"),
                )
                theme.save()

                if data.get("has_logo"):
                    for entry in zf.namelist():
                        if entry.startswith("logo.") or entry.startswith("logo" + os.sep):
                            with zf.open(entry) as f:
                                ext = os.path.splitext(entry)[1] or ".png"
                                theme.logo.save(f"logo{ext}", io.BytesIO(f.read()), save=False)
                            break

                if data.get("has_banner_image"):
                    for entry in zf.namelist():
                        if entry.startswith("banner.") or entry.startswith("banner" + os.sep):
                            with zf.open(entry) as f:
                                ext = os.path.splitext(entry)[1] or ".jpg"
                                theme.banner_image.save(f"banner{ext}", io.BytesIO(f.read()), save=False)
                            break

                if theme.logo or theme.banner_image:
                    theme.save()

        except Exception as e:
            messages.error(request, f"Import failed: {e}")
            return redirect("admin:viewer_themeprofile_changelist")

        messages.success(request, f"Theme '{theme_name}' imported successfully")
        return redirect(f"admin:viewer_themeprofile_change", theme.pk)

    def import_theme_action(self, request, queryset):
        return redirect("admin:viewer_themeprofile_import")
    import_theme_action.short_description = "Import Theme ZIP"

    actions = [import_theme_action]

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "icon_set":
            field = forms.ChoiceField(
                choices=_get_icon_set_choices(),
                required=db_field.blank is False,
                label=db_field.verbose_name,
                help_text=db_field.help_text,
            )
        return field


@admin.register(BaseMap)
class BaseMapAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "tenant", "is_active", "sort_order", "thumbnail_preview", "created_at")
    list_filter = ("is_active", "type", "tenant")
    search_fields = ("name", "url")

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="48" height="48" style="object-fit:cover;border-radius:4px;" />', obj.thumbnail.url)
        return format_html('<img src="{}" width="48" height="48" style="object-fit:cover;border-radius:4px;opacity:0.5;" />',
                           staticfiles_storage.url("viewer/icons/globe-fallback.svg"))
    thumbnail_preview.short_description = "Thumbnail"
