import random
import pandas as pd

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import inlineformset_factory
from django.contrib import messages
from django.http import JsonResponse

from .models import Pony, PonyImage, CompetitionResult
from .forms import PonyForm, ContactForm


# ================================
# Image Formset
# ================================
PonyImageFormSet = inlineformset_factory(
    Pony,
    PonyImage,
    fields=("image", "caption"),
    extra=1,
    can_delete=True
)


# ================================
# HOMEPAGE (FIXED + CLEAN)
# ================================
def index(request):
    # Only the two featured ponies
    featured_ids = [1403, 2757]
    ponies = Pony.objects.filter(id__in=featured_ids).select_related('sire','dam','dam__sire')
    return render(request, 'ponies/index.html', {'ponies': ponies})
# ================================
# OPTIONAL USER DASHBOARD
# ================================
@login_required(login_url='account_login')
def myindex(request):
    qs = list(Pony.objects.filter(status='approved'))

    if len(qs) > 9:
        qs = random.sample(qs, 9)

    return render(request, 'ponies/myindex.html', {
        'ponies': qs
    })


# ================================
# SEARCH (FIXED PAGINATION BUG)
# ================================
def pony_search(request):
    ponies = (
        Pony.objects
        .filter(status='approved')
        .select_related('sire', 'dam', 'dam__sire')
        .order_by('name')
    )

    filters = {
        key: request.GET.get(key, '').strip()
        for key in [
            'name','gender','year','height','studbook','color',
            'ueln','fei_id','microchip','breeder','owner',
            'sire','dam','dam_sire','approved','approved_for'
        ]
    }

    # Apply filters
    if filters['name']:
        ponies = ponies.filter(name__icontains=filters['name'])

    if filters['gender']:
        ponies = ponies.filter(gender=filters['gender'])

    if filters['year']:
        ponies = ponies.filter(year_of_birth=filters['year'])

    if filters['height']:
        ponies = ponies.filter(height_cm=filters['height'])

    if filters['studbook']:
        ponies = ponies.filter(studbook__icontains=filters['studbook'])

    if filters['color']:
        ponies = ponies.filter(color__icontains=filters['color'])

    if filters['ueln']:
        ponies = ponies.filter(ueln__icontains=filters['ueln'])

    if filters['fei_id']:
        ponies = ponies.filter(fei_id__icontains=filters['fei_id'])

    if filters['microchip']:
        ponies = ponies.filter(microchip__icontains=filters['microchip'])

    if filters['breeder']:
        ponies = ponies.filter(breeder__icontains=filters['breeder'])

    if filters['owner']:
        ponies = ponies.filter(owner__icontains=filters['owner'])

    if filters['sire']:
        ponies = ponies.filter(sire__name__icontains=filters['sire'])

    if filters['dam']:
        ponies = ponies.filter(dam__name__icontains=filters['dam'])

    if filters['dam_sire']:
        ponies = ponies.filter(dam__sire__name__icontains=filters['dam_sire'])

    if filters['approved'] == "yes":
        ponies = ponies.filter(is_approved_stallion=True)

    elif filters['approved'] == "no":
        ponies = ponies.filter(is_approved_stallion=False)

    if filters['approved_for']:
        ponies = ponies.filter(approved_for__icontains=filters['approved_for'])

    # Pagination
    paginator = Paginator(ponies, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'ponies/search.html', {
        'page_obj': page_obj,
        'filters': filters,
        'query_string': request.GET.urlencode()  # IMPORTANT FIX
    })


# ================================
# PONY DETAIL (WITH PAGINATION)
# ================================
def pony_detail(request, pk):
    pony = get_object_or_404(Pony, pk=pk)

    competition_qs = pony.competition_records.all().order_by('-date')
    offspring_qs = pony.offspring.all().order_by('year_of_birth')

    comp_page_obj = Paginator(competition_qs, 5).get_page(request.GET.get('comp_page'))
    off_page_obj = Paginator(offspring_qs, 5).get_page(request.GET.get('off_page'))

    # Pedigree
    gen0 = [pony]
    gen1 = [pony.sire, pony.dam]

    gen2 = [
        pony.sire.sire if pony.sire and pony.sire.sire else None,
        pony.sire.dam if pony.sire and pony.sire.dam else None,
        pony.dam.sire if pony.dam and pony.dam.sire else None,
        pony.dam.dam if pony.dam and pony.dam.dam else None,
    ]

    gen3 = []
    for parent in gen2:
        if parent:
            gen3.extend([parent.sire, parent.dam])
        else:
            gen3.extend([None, None])

    return render(request, 'ponies/pony_detail.html', {
        'pony': pony,
        'generations': [gen0, gen1, gen2, gen3],
        'comp_page_obj': comp_page_obj,
        'off_page_obj': off_page_obj,
    })


# ================================
# ADD PONY
# ================================
@login_required(login_url='account_login')
def add_pony(request):
    if request.method == 'POST':
        form = PonyForm(request.POST, request.FILES)
        formset = PonyImageFormSet(request.POST, request.FILES, prefix="images")

        if form.is_valid() and formset.is_valid():
            pony = form.save(commit=False)

            for parent_field, gender, name_field in [
                ('sire', 'Stallion', 'sire_name'),
                ('dam', 'Mare', 'dam_name')
            ]:
                parent_name = form.cleaned_data.get(name_field)
                if parent_name:
                    parent = Pony.objects.filter(name__iexact=parent_name).first()
                    if not parent:
                        parent = Pony.objects.create(
                            name=parent_name,
                            gender=gender,
                            status='pending'
                        )
                    setattr(pony, parent_field, parent)

            pony.save()

            images = formset.save(commit=False)
            for img in images:
                img.pony = pony
                img.save()

            return redirect('ponies:index')

    else:
        form = PonyForm()
        formset = PonyImageFormSet(prefix="images")

    return render(request, 'ponies/add_pony.html', {
        'form': form,
        'formset': formset
    })



# ================================
# AUTOCOMPLETE
# ================================
def pony_autocomplete(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        ponies = Pony.objects.filter(name__icontains=query)[:10]
        results = [{'id': p.id, 'text': p.name} for p in ponies]

    return JsonResponse({'results': results})


# ================================
# APPROVAL SYSTEM
# ================================
@staff_member_required
def approve_dashboard(request):
    ponies = Pony.objects.filter(status='pending').order_by('name')
    return render(request, 'ponies/approve_dashboard.html', {'pending_ponies': ponies})


@staff_member_required
def approve_pony(request, pony_id):
    pony = get_object_or_404(Pony, id=pony_id)
    pony.status = 'approved'
    pony.save()
    return redirect('ponies:approve_dashboard')


@staff_member_required
def reject_pony(request, pony_id):
    pony = get_object_or_404(Pony, id=pony_id)
    pony.status = 'rejected'
    pony.save()
    return redirect('ponies:approve_dashboard')


# ================================
# CONTACT
# ================================
from django.core.mail import send_mail
from django.conf import settings


def contact(request):
    success = False
    error = None

    if request.method == "POST":
        form = ContactForm(request.POST)

        if form.is_valid():
            if form.cleaned_data.get('honeypot'):
                error = "Spam detected."
            else:
                name = form.cleaned_data.get('name')
                email = form.cleaned_data.get('email')
                message = form.cleaned_data.get('note')

                try:
                    send_mail(
                        subject=f"Contact from {name}",
                        message=f"Name: {name}\nEmail: {email}\n\n{message}",
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[settings.EMAIL_HOST_USER],
                        fail_silently=False,
                    )
                    success = True
                    form = ContactForm()

                except Exception as e:
                    error = str(e)  # IMPORTANT: show real error

    else:
        form = ContactForm()

    return render(request, 'ponies/contact.html', {
        'form': form,
        'success': success,
        'error': error
    })
# ================================
# Stallions at Stud
# ================================
def stallions_at_stud(request):
    qs = Pony.objects.filter(gender='Stallion', is_at_stud=True, status='approved')
    filters = {key: request.GET.get(key,'') for key in ['name','color','year','height','studbook','approved_for']}
    if filters['name']:
        qs = qs.filter(name__icontains=filters['name'])
    if filters['color']:
        qs = qs.filter(color__icontains=filters['color'])
    if filters['year']:
        qs = qs.filter(year_of_birth=filters['year'])
    if filters['height']:
        qs = qs.filter(height_cm=filters['height'])
    if filters['studbook']:
        qs = qs.filter(studbook__icontains=filters['studbook'])
    if filters['approved_for']:
        qs = qs.filter(approved_for__icontains=filters['approved_for'])
    paginator = Paginator(qs.order_by('name'),12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request,'ponies/stallions_at_stud.html',{'page_obj': page_obj,'filters': filters})
# ================================
# PONY IMPORT
# ================================
@staff_member_required
def import_ponies(request):
    title = "Import Ponies"

    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]

        try:
            # Read file
            if file.name.endswith(".xlsx"):
                df = pd.read_excel(file, engine="openpyxl")
            elif file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                messages.error(request, "Unsupported file format")
                return redirect(request.path)

            created = 0
            updated = 0
            skipped = 0

            for _, row in df.iterrows():
                try:
                    name = str(row.get("name", "")).strip()
                    ueln = str(row.get("ueln", "")).strip()

                    if not name:
                        skipped += 1
                        continue

                    # ---- PARENTS ----
                    sire = None
                    dam = None

                    sire_name = str(row.get("sire", "")).strip()
                    dam_name = str(row.get("dam", "")).strip()

                    if sire_name:
                        sire, _ = Pony.objects.get_or_create(
                            name=sire_name,
                            defaults={"gender": "Stallion", "status": "pending"}
                        )

                    if dam_name:
                        dam, _ = Pony.objects.get_or_create(
                            name=dam_name,
                            defaults={"gender": "Mare", "status": "pending"}
                        )

                    # ---- MAIN PONY ----
                    pony, created_flag = Pony.objects.update_or_create(
                        ueln=ueln if ueln else None,
                        defaults={
                            "name": name,
                            "gender": row.get("gender"),
                            "year_of_birth": row.get("year_of_birth"),
                            "owner": row.get("owner"),
                            "breeder": row.get("breeder"),
                            "height_cm": row.get("height_cm"),
                            "color": row.get("color"),
                            "studbook": row.get("studbook"),
                            "sire": sire,
                            "dam": dam,
                            "status": "approved",
                        }
                    )

                    if created_flag:
                        created += 1
                    else:
                        updated += 1

                except Exception:
                    skipped += 1
                    continue

            messages.success(
                request,
                f"Import complete — Created: {created}, Updated: {updated}, Skipped: {skipped}"
            )

        except Exception as e:
            messages.error(request, f"Import failed: {e}")

        return redirect(request.path)

    return render(request, "ponies/upload_page.html", {"title": title})
# ================================
# COMPETITION IMPORT
# ================================
@staff_member_required
def import_competition(request):
    title = "Import Competition Results"

    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "No file uploaded")
            return redirect(request.path)

        try:
            if file.name.endswith(".xlsx"):
                df = pd.read_excel(file, engine="openpyxl")
            elif file.name.endswith(".xls"):
                df = pd.read_excel(file)
            elif file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                messages.error(request, "Unsupported file format")
                return redirect(request.path)

            imported_count = 0
            for _, row in df.iterrows():
                pony_id = row.get("pony_id")
                if pd.isna(pony_id):
                    continue
                try:
                    pony = Pony.objects.get(id=int(pony_id))
                except Pony.DoesNotExist:
                    continue

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
                imported_count += 1

            messages.success(request, f"{imported_count} competition results imported successfully")
        except Exception as e:
            messages.error(request, f"Error importing competition results: {e}")

        return redirect(request.path)

    return render(request, "ponies/import_page.html", {"title": title})
# ================================
# Approval Dashboard
# ================================
@staff_member_required
def approve_dashboard(request):
    pending_ponies = Pony.objects.filter(status='pending').order_by('name')
    return render(request,'ponies/approve_dashboard.html',{'pending_ponies': pending_ponies})

@staff_member_required
def approve_pony(request, pony_id):
    pony = get_object_or_404(Pony, id=pony_id)
    pony.status = 'approved'
    pony.save()
    return redirect('ponies:approve_dashboard')

@staff_member_required
def reject_pony(request, pony_id):
    pony = get_object_or_404(Pony, id=pony_id)
    pony.status = 'rejected'
    pony.save()
    return redirect('ponies:approve_dashboard')

@staff_member_required
def approve_all_ponies(request):
    Pony.objects.filter(status='pending').update(status='approved')
    return redirect('ponies:approve_dashboard')