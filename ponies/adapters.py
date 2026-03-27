from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.first_name = form.cleaned_data.get('first_name')
        user.last_name = form.cleaned_data.get('last_name')
        if commit:
            user.save()
        return user
    
@admin.register(Pony)
class PonyAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Pedigree', {
            'fields': ('sire', 'dam', 'pedigree_image', 'pedigree_image_preview')
        }),
        # ... rest unchanged
    )
    readonly_fields = ('pedigree_image_preview', 'created_at')