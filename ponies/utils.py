import os
from django.conf import settings
from weasyprint import HTML

def generate_pedigree_image(pony, generations_html):
    """
    Generate a PNG image of the pony's pedigree and save it to MEDIA_ROOT/pedigrees/
    """
    output_dir = os.path.join(settings.MEDIA_ROOT, "pedigrees")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{pony.id}.png")

    html_content = f"""
    <html>
    <head>
    <style>
        body {{ font-family: "Avenir Next Condensed", Arial, sans-serif; }}
        .pedigree-tree {{ display:grid; grid-template-columns: repeat(4, 1fr); gap:60px; justify-items:center; }}
        .pedigree-box {{ display:flex; flex-direction:column; justify-content:center; align-items:center; padding:4px 0; }}
        .main-pony a {{ font-weight:700; color:#000; }}
        .sire a {{ color:#58c9ba; }}
        .dam a {{ color:#000; }}
    </style>
    </head>
    <body>
        {generations_html}
    </body>
    </html>
    """

    HTML(string=html_content).write_png(output_path)
    pony.pedigree_image = f"pedigrees/{pony.id}.png"
    pony.save()