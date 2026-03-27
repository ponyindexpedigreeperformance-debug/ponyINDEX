
from django import forms
from django.core.mail import send_mail
from django.conf import settings

from .models import Pony, PonyImage

# ----------------------
# Pony Form
# ----------------------
class PonyForm(forms.ModelForm):
    sire_name = forms.CharField(
        required=False,
        label="Sire",
        widget=forms.TextInput(attrs={'placeholder': 'Type sire name...'})
    )
    dam_name = forms.CharField(
        required=False,
        label="Dam",
        widget=forms.TextInput(attrs={'placeholder': 'Type dam name...'})
    )

    class Meta:
        model = Pony
        fields = [
            'name','gender','year_of_birth','height_cm','color','studbook',
            'fei_id','ueln','microchip',
            'breeder','owner','stallion_holder','email','phone','website',
            'is_approved_stallion','is_at_stud','approved_for','wffs_status','stud_fee',
            'image','pedigree_image'
        ]
        widgets = {
            "sire": forms.Select(attrs={"class": "pony-search"}),
            "dam": forms.Select(attrs={"class": "pony-search"}),
        }


# ----------------------
# Pony Image Form
# ----------------------
class PonyImageForm(forms.ModelForm):
    class Meta:
        model = PonyImage
        fields = ("image", "caption")


# ----------------------
# Contact Form
# ----------------------
class ContactForm(forms.Form):
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    note = forms.CharField(widget=forms.Textarea)
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    def send_email(self):
        """
        Sends an email with the contact message in a proper format.
        """
        subject = f"PonyINDEX Contact Message from {self.cleaned_data['name']}"
        message = (
            f"Name: {self.cleaned_data['name']}\n"
            f"Email: {self.cleaned_data['email']}\n\n"
            f"Message:\n{self.cleaned_data['note']}"
        )
        sender = settings.DEFAULT_FROM_EMAIL
        recipient_list = [settings.DEFAULT_FROM_EMAIL]
        send_mail(subject, message, sender, recipient_list)
