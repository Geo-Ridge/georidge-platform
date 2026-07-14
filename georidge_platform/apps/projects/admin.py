import os
import urllib.parse

from django import forms
from django.conf import settings
from django.contrib import admin
from django.forms import Select
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html, mark_safe
from georidge_platform.apps.accounts.models import Tenant
from georidge_platform.apps.viewer.models import BaseMap, LayerSearchConfig, ThemeProfile
from georidge_platform.apps.qgis_server.services import get_layer_fields, get_wms_layers, remap_map_path
from georidge_platform.apps.validation.services import validate_project
from .forms import ProjectUploadForm
from .models import Project
from .views import _handle_zip_upload


def _default_tenant():
    slug = settings.DEFAULT_TENANT_SLUG
    return Tenant.objects.filter(slug=slug).first()


class CollapsibleCheckboxWidget(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, renderer=None):
        inner = super().render(name, value, attrs, renderer)
        count = inner.count('type="checkbox"')
        return mark_safe(f'''<div class="collapsible-checkbox-list">
  <div class="collapsible-checkbox-items">
{inner}
  </div>
  <div class="collapsible-checkbox-toggle">
    <a href="#" onclick="event.preventDefault();var c=this.closest('.collapsible-checkbox-list');var i=c.querySelector('.collapsible-checkbox-items');var e=i.style.maxHeight;if(!e||e==='200px'){{i.style.maxHeight=i.scrollHeight+'px';this.textContent='Collapse'}}else{{i.style.maxHeight='200px';this.textContent='Show all fields ({count})'}};return false">Show all fields</a>
  </div>
</div>
<style>
.collapsible-checkbox-items {{
  max-height: 200px; overflow-y: auto; transition: max-height .2s ease;
  border: 1px solid #ddd; padding: 4px 8px; border-radius: 3px;
}}
.collapsible-checkbox-toggle {{ margin-top: 4px; }}
.collapsible-checkbox-toggle a {{ font-size: .8rem; cursor: pointer; }}
</style>
<script>
(function() {{
  var e = document.querySelectorAll('.collapsible-checkbox-items');
  e.forEach(function(el) {{
    var t = el.closest('.collapsible-checkbox-list')?.querySelector('.collapsible-checkbox-toggle a');
    if (t && el.querySelectorAll('input[type=checkbox]').length > 0)
      t.textContent = 'Show all fields (' + el.querySelectorAll('input[type=checkbox]').length + ')';
  }});
}})();
</script>''')


class LayerSearchConfigForm(forms.ModelForm):
    class Meta:
        model = LayerSearchConfig
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        proj = project
        if not proj and self.instance and self.instance.project_id:
            proj = self.instance.project

        if proj:
            try:
                layers = get_wms_layers(proj)
                layer_choices = [("", "--- Select layer ---")] + [(l["name"], f'{l["title"]} ({l["name"]})') for l in layers]
                if layer_choices:
                    self.fields["layer_name"] = forms.ChoiceField(
                        choices=layer_choices, label="Layer", required=False,
                    )
                    if not self.instance.pk:
                        self.initial["layer_name"] = ""
            except Exception:
                pass

        af = (self.instance and self.instance.available_fields) or []
        layer_name = (self.instance and self.instance.layer_name) or ""
        if not af and proj and layer_name:
            try:
                af = get_layer_fields(proj, layer_name)
            except Exception:
                pass

        if af:
            self.fields["searchable_fields"] = forms.MultipleChoiceField(
                choices=[(f, f) for f in af],
                initial=self.instance.searchable_fields or [],
                widget=CollapsibleCheckboxWidget,
                required=False,
                label="Searchable fields",
            )
        else:
            has_layer = bool(layer_name)
            if has_layer:
                help_text = (
                    "No fields auto-detected via WFS. "
                    "Type field names below, one per line. "
                    "Enable WFS in QGIS Server project properties for auto-detection."
                )
            else:
                help_text = "Save with a layer selected to configure fields."

            if not self.is_bound:
                initial_val = self.instance.searchable_fields or []
                if isinstance(initial_val, list):
                    self.initial["searchable_fields"] = "\n".join(initial_val)

            self.fields["searchable_fields"] = forms.CharField(
                widget=forms.Textarea(attrs={"rows": 6}),
                required=False,
                label="Searchable fields",
                help_text=help_text,
            )

    def clean_searchable_fields(self):
        data = self.cleaned_data.get("searchable_fields", [])
        if isinstance(data, str):
            return [line.strip() for line in data.split("\n") if line.strip()]
        return data or []

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.layer_name or not instance.project_id:
            return instance
        if instance.layer_name and instance.project_id:
            try:
                proj_data = get_wms_layers(instance.project)
                for ld in proj_data:
                    if ld["name"] == instance.layer_name:
                        instance.layer_title = ld["title"]
                        break
            except Exception:
                pass
            try:
                fields = get_layer_fields(instance.project, instance.layer_name)
                instance.available_fields = fields
            except Exception:
                pass
        if commit:
            existing = LayerSearchConfig.objects.filter(
                project=instance.project, layer_name=instance.layer_name,
            ).exclude(pk=instance.pk).first()
            if existing:
                for field in instance._meta.fields:
                    name = field.attname
                    if name not in ("id", "project_id"):
                        setattr(existing, name, getattr(instance, name))
                existing.save()
                return existing
            instance.save()
        return instance


class LayerSearchConfigFormSet(forms.BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        kwargs["project"] = self.instance
        return super()._construct_form(i, **kwargs)


class LayerSearchConfigInline(admin.StackedInline):
    model = LayerSearchConfig
    form = LayerSearchConfigForm
    formset = LayerSearchConfigFormSet
    extra = 1
    classes = ("collapse", "layer-search-config")
    fieldsets = (
        (None, {
            "fields": ("layer_name", "active"),
        }),
        ("Search Fields", {
            "fields": ("searchable_fields",),
            "description": "Select which fields to search against.",
        }),
        ("Options", {
            "classes": ("collapse",),
            "fields": ("label_template", "popup_fields", "max_results"),
        }),
    )

    class Media:
        css = {"all": ("admin/css/layer-search-config.css",)}


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [LayerSearchConfigInline]
    actions = ["sync_search_layers_action"]
    list_display = ("name", "owner", "status", "version", "theme", "view_link", "created_at", "updated_at")
    list_filter = ("status", "theme")
    search_fields = ("name",)
    filter_horizontal = ("base_maps",)
    change_list_template = "admin/projects/project/change_list.html"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            base = ("tenant",)
            return base + (
                "get_qgis_local_path", "get_qgis_server_path",
                "get_wms_status", "get_wfs_status",
                "get_wms_capabilities_link", "get_wfs_capabilities_link",
            )
        return ()

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("upload/", self.admin_site.admin_view(self.upload_view), name="projects_project_upload"),
        ]
        return custom_urls + urls

    def upload_view(self, request):
        if request.method == "POST":
            form = ProjectUploadForm(request.POST, request.FILES)
            if form.is_valid():
                project = form.save(commit=False)
                project.owner = request.user
                project.status = Project.Status.DRAFT
                project.file = None
                if not project.tenant:
                    project.tenant = _default_tenant()
                project.save()

                uploaded_file = request.FILES["file"]
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                try:
                    if ext == ".zip":
                        _handle_zip_upload(project, uploaded_file)
                    else:
                        project.file.save(uploaded_file.name, uploaded_file)
                except ValueError as e:
                    project.delete()
                    form.add_error("file", str(e))
                    self.message_user(request, "Please correct the errors below.", level="error")
                else:
                    report = validate_project(project.file.path, project=project)
                    if report.valid:
                        project.status = Project.Status.READY
                        project.save(update_fields=["status"])
                        self.message_user(
                            request,
                            f"Project \"{project.name}\" uploaded and validated successfully — {report.layer_count} layer(s)."
                        )
                    else:
                        project.status = Project.Status.FAILED
                        project.save(update_fields=["status"])
                        self.message_user(
                            request,
                            f"Project \"{project.name}\" uploaded but validation failed: {'; '.join(report.errors)}",
                            level="error"
                        )
                    return HttpResponseRedirect(reverse("admin:projects_project_change", args=[project.pk]))
            else:
                self.message_user(request, "Please correct the errors below.", level="error")
        else:
            form = ProjectUploadForm()

        context = {
            "title": "Upload QGIS Project",
            "form": form,
            "opts": self.model._meta,
            "media": self.media,
        }
        return render(request, "admin/projects/project/upload_form.html", context)

    fieldsets = (
        (None, {
            "fields": ("name", "description", "owner", "status", "theme"),
        }),
        ("Project file & versioning", {
            "classes": ("collapse",),
            "fields": ("file", "version", "published_by", "published_at", "published_version"),
        }),
        ("Extent", {
            "classes": ("collapse",),
            "fields": ("extent_min_x", "extent_min_y", "extent_max_x", "extent_max_y"),
        }),
        ("Base Maps", {
            "classes": ("collapse",),
            "fields": ("base_maps",),
            "description": "Choose which base maps are available in the viewer. Leave empty to use all active base maps for the tenant.",
        }),
        ("QGIS Server", {
            "classes": ("collapse",),
            "fields": (
                "get_qgis_local_path", "get_qgis_server_path",
                "get_wms_status", "get_wms_capabilities_link",
                "get_wfs_status", "get_wfs_capabilities_link",
            ),
        }),
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "base_maps":
            kwargs["queryset"] = BaseMap.objects.filter(is_active=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "theme":
            kwargs["queryset"] = ThemeProfile.objects.all()
            kwargs["widget"] = Select
            kwargs["help_text"] = "Choose a theme for the viewer. Override with ?theme_override=<id> in the URL."
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.tenant:
            from django.conf import settings
            from georidge_platform.apps.accounts.models import Tenant
            slug = getattr(settings, "DEFAULT_TENANT_SLUG", "default")
            obj.tenant, _ = Tenant.objects.get_or_create(slug=slug, defaults={"name": slug.capitalize()})
        super().save_model(request, obj, form, change)

    @admin.action(description="Sync search layers from QGIS Server")
    def sync_search_layers_action(self, request, queryset):
        from georidge_platform.apps.viewer.services import sync_search_layers
        for project in queryset:
            try:
                sync_search_layers(project)
            except Exception as e:
                self.message_user(request, f"Sync failed for {project.name}: {e}", level="error")
        self.message_user(request, f"Synced search layers for {queryset.count()} project(s).")

    def view_link(self, obj):
        if not obj.tenant:
            from django.conf import settings
            slug = getattr(settings, "DEFAULT_TENANT_SLUG", "default")
        else:
            slug = obj.tenant.slug
        url = reverse("viewer:view", args=[obj.pk])
        return format_html('<a href="/{}{}" target="_blank">View Map</a>', slug, url)
    view_link.short_description = "View"

    # ── QGIS Server readonly fields ──────────────────────────────────────

    def _qgis_base_url(self, obj):
        if not obj.file:
            return None
        map_path = remap_map_path(obj.file.path.replace("\\", "/"))
        base = settings.QGIS_SERVER_URL.rstrip("/")
        return base, map_path

    def get_qgis_local_path(self, obj):
        if not obj.file:
            return "No file uploaded"
        return obj.file.path
    get_qgis_local_path.short_description = "Local path"

    def get_qgis_server_path(self, obj):
        if not obj.file:
            return "No file uploaded"
        return remap_map_path(obj.file.path.replace("\\", "/"))
    get_qgis_server_path.short_description = "QGIS Server path"

    _QGIS_STATUS_CSS = mark_safe(
        '<style>'
        '.qgis-status{font-weight:600;white-space:nowrap}'
        '.qgis-status--online{color:#2e7d32}'
        '.qgis-status--offline{color:#c62828}'
        '</style>'
    )

    def get_wms_status(self, obj):
        if not obj.file:
            return "—"
        try:
            from georidge_platform.apps.qgis_server.services import validate_on_server
            result = validate_on_server(obj)
            if result["valid"]:
                layers = get_wms_layers(obj)
                queryable = sum(1 for l in layers if l.get("queryable"))
                return self._QGIS_STATUS_CSS + format_html(
                    '<span class="qgis-status qgis-status--online">● Online</span> — '
                    '<strong>{}</strong> layer(s), <strong>{}</strong> queryable',
                    result["layer_count"], queryable,
                )
            return self._QGIS_STATUS_CSS + format_html(
                '<span class="qgis-status qgis-status--offline">● Offline</span> — {}',
                result["errors"][0] if result["errors"] else "Unknown error",
            )
        except Exception as e:
            return self._QGIS_STATUS_CSS + format_html(
                '<span class="qgis-status qgis-status--offline">● Offline</span> — {}', str(e),
            )
    get_wms_status.short_description = "WMS"

    def get_wfs_status(self, obj):
        if not obj.file:
            return "—"
        try:
            base, map_path = self._qgis_base_url(obj)
            import urllib.request as _req
            import urllib.error as _err
            url = f"{base}?MAP={map_path}&SERVICE=WFS&REQUEST=GetCapabilities"
            req = _req.Request(url, method="GET")
            with _req.urlopen(req, timeout=10) as resp:
                resp.read()
            return format_html('<span class="qgis-status qgis-status--online">● Online</span>')
        except _err.HTTPError:
            return format_html('<span class="qgis-status qgis-status--offline">● Offline</span> — WFS not enabled')
        except Exception as e:
            return format_html('<span class="qgis-status qgis-status--offline">● Offline</span> — {}', str(e))
    get_wfs_status.short_description = "WFS"

    def get_wms_capabilities_link(self, obj):
        if not obj.file:
            return "—"
        base, map_path = self._qgis_base_url(obj)
        url = f"{base}?MAP={urllib.parse.quote(map_path)}&SERVICE=WMS&REQUEST=GetCapabilities"
        return format_html('<a href="{}" target="_blank">WMS Capabilities</a>', url)
    get_wms_capabilities_link.short_description = "Capabilities"

    def get_wfs_capabilities_link(self, obj):
        if not obj.file:
            return "—"
        base, map_path = self._qgis_base_url(obj)
        url = f"{base}?MAP={urllib.parse.quote(map_path)}&SERVICE=WFS&REQUEST=GetCapabilities"
        return format_html('<a href="{}" target="_blank">WFS Capabilities</a>', url)
    get_wfs_capabilities_link.short_description = "Capabilities"


