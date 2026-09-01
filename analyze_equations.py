# It is doing an investigation of the data 
import pymupdf
from pathlib import Path


# --------------------------------------------------
# PDF PATH
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

PDF_PATH = (BASE_DIR/ "data"/ "raw"/ "college-physics-2e_-_WEB.pdf")


# --------------------------------------------------
# OPEN PDF
# --------------------------------------------------

doc = pymupdf.open(PDF_PATH)

print("=" * 70)
print("EQUATION ANALYSIS")
print("=" * 70)

print(f"Total pages: {len(doc)}")


# --------------------------------------------------
# TEST ONLY A FEW PAGES
# --------------------------------------------------

pages_to_check = [10, 20, 30, 40, 50]


for page_number in pages_to_check:

    if page_number >= len(doc):
        continue

    page = doc[page_number]

    print()
    print("=" * 70)
    print(f"PAGE {page_number + 1}")
    print("=" * 70)

    # --------------------------------------------------
    # 1. TEXT
    # --------------------------------------------------

    text = page.get_text("text")

    print()
    print("TEXT PREVIEW:")
    print("-" * 50)

    print(text[:1000])

    # --------------------------------------------------
    # 2. TEXT BLOCKS
    # --------------------------------------------------

    blocks = page.get_text("blocks")

    print()
    print(f"TEXT BLOCKS: {len(blocks)}")

    # --------------------------------------------------
    # 3. IMAGES
    # --------------------------------------------------

    images = page.get_images(full=True)

    print()
    print(f"IMAGES: {len(images)}")

    # --------------------------------------------------
    # 4. DRAWING OBJECTS
    # --------------------------------------------------

    drawings = page.get_drawings()

    print()
    print(f"DRAWING OBJECTS: {len(drawings)}")


# --------------------------------------------------
# CLOSE
# --------------------------------------------------

doc.close()

print()
print("=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)