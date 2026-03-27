from django.core.management.base import BaseCommand
from ponies.models import Pony
import pandas as pd

class Command(BaseCommand):
    help = "Import ponies from Excel"

    def handle(self, *args, **kwargs):
        df = pd.read_excel('path/to/your/file.xlsx')

        for _, row in df.iterrows():
            sire = Pony.objects.filter(name=row['SIRE']).first()
            dam = Pony.objects.filter(name=row['DAM']).first()

            Pony.objects.create(
                name=row['NAME'],
                gender=row['GENDER'],
                year_of_birth=row['YEAR_OF_BIRTH'],
                height_cm=row['HEIGHT_CM'],
                color=row['COLOR'],
                studbook=row['STUDBOOK'],
                sire=sire,
                dam=dam,
                breeder=row['BREEDER'],
                owner=row['OWNER'],
                fei_id=row['FEI_ID'],
                ueln=row['UELN'],
                microchip=row['MICROCHIP'],
                is_approved_stallion=row['IS_APPROVED_STALLION'],
                is_at_stud=row['IS_AT_STUD'],
                approval=row['APPROVAL'],
                semen_type=row['SEMEN_TYPE'],
                breeding_fee=row['BREEDING_FEE'],
                breeding_location=row['BREEDING_LOCATION'],
                breeding_contact=row['BREEDING_CONTACT'],
                wffs_status=row['WFFS_STATUS'],
                status=row['STATUS'],
            )
        self.stdout.write(self.style.SUCCESS("Import complete!"))