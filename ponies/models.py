from django.db import models
from django.db.models import Q
from django.utils.html import format_html

# ----------------------
# Pony Model
# ----------------------
class Pony(models.Model):

    GENDER_CHOICES = [
        ('Mare', 'Mare'),
        ('Stallion', 'Stallion'),
        ('Gelding', 'Gelding'),
    ]

    WFFS_CHOICES = [
        ('Negative', 'Negative'),
        ('Positive', 'Positive'),
        ('Carrier', 'Carrier'),
        ('Unknown', 'Unknown'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # Basic info
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    year_of_birth = models.IntegerField(blank=True, null=True)
    height_cm = models.IntegerField(blank=True, null=True)
    color = models.CharField(max_length=100, blank=True)
    studbook = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='ponies/images/', blank=True, null=True)
    pedigree_image = models.ImageField(
        upload_to='ponies/pedigree_images/',
        blank=True,
        null=True,
        help_text="Upload the pedigree image here"
    )

    # Pedigree
    sire = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sire_offspring')
    dam = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dam_offspring')
    sire_name_fallback = models.CharField(max_length=255, blank=True, null=True)
    dam_name_fallback = models.CharField(max_length=255, blank=True, null=True)

    # Ownership
    breeder = models.CharField(max_length=255, blank=True)
    owner = models.CharField(max_length=255, blank=True)
    stallion_holder = models.CharField(max_length=255, blank=True, null=True)

    # Identification
    fei_id = models.CharField(max_length=50, blank=True)
    ueln = models.CharField(max_length=50, blank=True)
    microchip = models.CharField(max_length=50, blank=True, null=True)

    # Stallion info
    is_approved_stallion = models.BooleanField(default=False)
    is_at_stud = models.BooleanField(default=False)
    approved_for = models.CharField(max_length=255, blank=True)
    stud_fee = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # Genetics & competition
    wffs_status = models.CharField(max_length=20, choices=WFFS_CHOICES, blank=True)
    competition_record = models.TextField(blank=True)

    # Status & timestamps
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def offspring(self):
        return Pony.objects.filter(Q(sire=self) | Q(dam=self))

    @property
    def all_images_for_slider(self):
        images = []
        if self.image:
            images.append(self.image.url)
        for img in self.images.all():
            if self.image and img.image.url == self.image.url:
                continue
            images.append(img.image.url)
        return images

    @property
    def pedigree_image_preview(self):
        if self.pedigree_image:
            return format_html('<img src="{}" style="max-height:200px;" />', self.pedigree_image.url)
        return "No image"


# ----------------------
# Pony Image
# ----------------------
class PonyImage(models.Model):
    pony = models.ForeignKey(Pony, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="pony_images/")
    caption = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.pony.name} Image"


# ----------------------
# Competition Result
# ----------------------
class CompetitionResult(models.Model):
    pony = models.ForeignKey(Pony, on_delete=models.CASCADE, related_name="competition_records")
    date = models.DateField()
    show = models.CharField(max_length=255)
    event = models.CharField(max_length=255)
    competition = models.CharField(max_length=255)
    obs_height = models.CharField(max_length=50, blank=True, null=True)
    athlete = models.CharField(max_length=255)
    position = models.CharField(max_length=50)
    score = models.CharField(max_length=50)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.pony} - {self.event} ({self.date})"


# ----------------------
# Competition Upload
# ----------------------
class CompetitionUpload(models.Model):
    file = models.FileField(upload_to='uploads/competition/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name