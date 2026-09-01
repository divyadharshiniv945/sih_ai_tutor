# clean_equations.py
from pathlib import Path
import json
import re


# ============================================================
# 1. PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# 2. INPUT
# ============================================================

INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "equations"
    / "page_51_structured.json"
)


# ============================================================
# 3. OUTPUT
# ============================================================

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "equations"
    / "page_51_cleaned.json"
)


# ============================================================
# 4. READ JSON
# ============================================================

with open(INPUT_PATH, "r", encoding="utf-8") as file:
    data = json.load(file)


# ============================================================
# 5. CLEAN LATEX
# ============================================================

def clean_latex(latex):

    cleaned = latex

    # Remove unnecessary spaces inside numbers
    cleaned = re.sub(
        r"(\d)\s+(\d)",
        r"\1\2",
        cleaned
    )

    # Fix common OCR issue:
    # \times1 0 -> \times 10
    cleaned = re.sub(
        r"\\times\s*1\s*0",
        r"\\times 10",
        cleaned
    )

    # Fix decimal numbers:
    # 1 . 3 3 -> 1.33
    cleaned = re.sub(
        r"(\d)\s*\.\s*(\d)",
        r"\1.\2",
        cleaned
    )

    # Repeat for numbers such as:
    # 1 . 3 3
    previous = None

    while previous != cleaned:

        previous = cleaned

        cleaned = re.sub(
            r"(\d)\s+(\d)",
            r"\1\2",
            cleaned
        )

    # Clean excessive spaces
    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned
    )

    return cleaned.strip()


# ============================================================
# 6. CLEAN EACH EQUATION
# ============================================================

cleaned_equations = []


for equation in data["equations"]:

    raw_latex = equation["raw_latex"]

    clean = clean_latex(raw_latex)

    cleaned_equations.append(
        {
            "raw_latex": raw_latex,
            "clean_latex": clean,
            "verified": False
        }
    )


# ============================================================
# 7. CREATE OUTPUT
# ============================================================

output_data = {
    "page": data["page"],
    "source_image": data["source_image"],
    "text": data["text"],
    "equations": cleaned_equations
}


# ============================================================
# 8. SAVE
# ============================================================

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output_data,
        file,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# 9. DISPLAY
# ============================================================

print("=" * 70)
print("EQUATION CLEANING")
print("=" * 70)

for number, equation in enumerate(cleaned_equations, start=1):

    print()
    print(f"Equation {number}")
    print("-" * 70)

    print("RAW:")
    print(equation["raw_latex"])

    print()
    print("CLEAN:")
    print(equation["clean_latex"])


print()
print("=" * 70)
print("SAVED")
print("=" * 70)

print(OUTPUT_PATH)