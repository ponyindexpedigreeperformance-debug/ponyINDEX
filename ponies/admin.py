from django.contrib import admin, messages
from django.urls import path
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.middleware.csrf import get_token
import pandas as pd
from django.forms.widgets import DateInput
from .models import Pony, PonyImage, CompetitionResult

# ----------------------
# Custom Date Widget
# ----------------------
class CustomDateInput(DateInput):
    input_type = 'text'
    format = '%d/%m/%Y'

# ----------------------
# Inlines
# ----------------------
class CompetitionResultInline(admin.TabularInline):
    model = CompetitionResult
    extra = 0
    fields = ('date', 'show', 'event', 'competition', 'obs_height', 'athlete', 'position', 'score')
    formfield_overrides = {
        CompetitionResult._meta.get_field('date'): {'widget': CustomDateInput()}
    }

class PonyImageInline(admin.TabularInline):
    model = PonyImage
    extra = 0
    fields = ('image', 'caption')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="height:100px;" />')
        return ""
    image_preview.short_description = "Preview"

# ----------------------
# Pony Admin
# ----------------------
@admin.register(Pony)
class PonyAdmin(admin.ModelAdmin):
    autocomplete_fields = ['sire', 'dam']
    list_display = ('name', 'gender', 'year_of_birth', 'owner')
    search_fields = ('name', 'owner', 'breeder')
    list_filter = ('gender', 'status', 'wffs_status')
    inlines = [PonyImageInline, CompetitionResultInline]

    readonly_fields = ('created_at', 'pedigree_image_preview',)
    change_form_template = "admin/change_form.html"

    fieldsets = (
        ("Basic Info", {
            "fields": ('name', 'gender', 'year_of_birth', 'height_cm', 'color', 'studbook', 'image',)
        }),
        ("Pedigree", {
            "fields": ('sire', 'dam', 'pedigree_image', 'pedigree_image_preview',)
        }),
        ("Identification", {
            "fields": ('fei_id', 'ueln', 'microchip',)
        }),
        ("Ownership", {
            "fields": ('breeder', 'owner',)
        }),
        ("Stallion Info", {
            "fields": (
                'is_approved_stallion', 'is_at_stud', 'approved_for',
                'stud_fee', 'wffs_status', 'stallion_holder',
                'email', 'phone', 'website',
            )
        }),
        ("Status & Timestamps", {
            "fields": ('status', 'created_at'),
            "classes": ('collapse',)
        }),
    )

    # Pedigree preview
    def pedigree_image_preview(self, obj):
        if obj.pedigree_image:
            return mark_safe(f'<img src="{obj.pedigree_image.url}" style="height:150px;" />')
        return ""
    pedigree_image_preview.short_description = "Pedigree Preview"

    # Custom URLs for import
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-ponies/', self.admin_site.admin_view(self.import_ponies), name='import-ponies'),
            path('<int:pony_id>/import-competition/', self.admin_site.admin_view(self.import_competition), name='import-competition'),
        ]
        return custom_urls + urls

    def _render_upload_form(self, request, title):
        csrf_token = get_token(request)
        html = f"""
            <h2>{title}</h2>
            <form method="post" enctype="multipart/form-data">
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                <input type="file" name="file" required>
                <button type="submit" class="default">Upload</button>
            </form>
        """
        return HttpResponse(mark_safe(html))

    def import_ponies(self, request):
        if request.method == "POST" and request.FILES.get("file"):
            file = request.FILES["file"]
            try:
                if file.name.endswith('.xlsx'):
                    df = pd.read_excel(file, engine='openpyxl')
                elif file.name.endswith('.xls'):
                    df = pd.read_excel(file)
                elif file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    messages.error(request, "Unsupported file format")
                    return HttpResponseRedirect("../")

                for _, row in df.iterrows():
                    Pony.objects.update_or_create(
                        fei_id=row.get("fei_id"),
                        defaults={
                            "name": row.get("name"),
                            "gender": row.get("gender"),
                            "year_of_birth": row.get("year_of_birth"),
                            "owner": row.get("owner"),
                            "breeder": row.get("breeder"),
                            "height_cm": row.get("height_cm"),
                            "color": row.get("color"),
                        }
                    )
                messages.success(request, "Ponies import successful!")
            except Exception as e:
                messages.error(request, f"Error: {e}")
            return HttpResponseRedirect("../")
        return self._render_upload_form(request, "Import Ponies")

    def import_competition(self, request, pony_id):
        if request.method == "POST" and request.FILES.get("file"):
            file = request.FILES["file"]
            try:
                if file.name.endswith('.xlsx'):
                    df = pd.read_excel(file, engine='openpyxl')
                elif file.name.endswith('.xls'):
                    df = pd.read_excel(file)
                elif file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    messages.error(request, "Unsupported file format")
                    return HttpResponseRedirect(f"../{pony_id}/change/")

                pony = Pony.objects.get(pk=pony_id)

                for _, row in df.iterrows():
                    CompetitionResult.objects.create(
                        pony=pony,
                        date=pd.to_datetime(row.get("date"), errors="coerce"),
                        show=row.get("show"),
                        event=row.get("event"),
                        competition=row.get("competition"),
                        obs_height=row.get("obs_height"),
                        athlete=row.get("athlete"),
                        position=row.get("position"),
                        score=row.get("score"),
                    )
                messages.success(request, "Competition import successful!")
            except Exception as e:
                messages.error(request, f"Error: {e}")
            return HttpResponseRedirect(f"../{pony_id}/change/")
        return self._render_upload_form(request, f"Import Competition Results for Pony {pony_id}")

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['additional_buttons'] = mark_safe(f'''
            <a class="button" href="{object_id}/import-competition/">Import Competition Results</a>
        ''')
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

# ----------------------
# Competition Result Admin
# ----------------------
@admin.register(CompetitionResult)
class CompetitionResultAdmin(admin.ModelAdmin):
    list_display = ('pony', 'date', 'show', 'event', 'competition', 'position', 'score')