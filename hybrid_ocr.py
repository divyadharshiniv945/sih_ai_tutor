from pathlib import Path
import json
import re
import shutil

import pymupdf
from pix2text import Pix2Text


# ============================================================
# 1. PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# 2. INPUT PDF
# ============================================================

PDF_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "college-physics-2e_-_WEB.pdf"
)


# ============================================================
# 3. OLD PIX2TEXT OUTPUT
#
# These are the pages you already processed.
# ============================================================

OLD_PIX2TEXT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "pix2text"
)


# ============================================================
# 4. NEW HYBRID OUTPUT
# ============================================================

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "hybrid_ocr"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OLD_PIX2TEXT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 5. CHECK PDF
# ============================================================

if not PDF_PATH.exists():

    print("PDF NOT FOUND ❌")
    print(PDF_PATH)

    raise SystemExit


# ============================================================
# 6. OPEN PDF
# ============================================================

doc = pymupdf.open(
    PDF_PATH
)

total_pages = len(doc)


print("=" * 70)
print("HYBRID OCR")
print("=" * 70)

print()
print("PDF:", PDF_PATH)
print("Total pages:", total_pages)

print()
print("Old Pix2Text folder:")
print(OLD_PIX2TEXT_DIR)

print()
print("New output folder:")
print(OUTPUT_DIR)


# ============================================================
# 7. LOAD PIX2TEXT
# ============================================================

print()
print("Loading Pix2Text...")

p2t = Pix2Text()

print("Pix2Text ready ✅")


# ============================================================
# 8. MATH DETECTION
# ============================================================

def looks_like_math(text):

    if not text:
        return False


    # --------------------------------------------------------
    # Strong mathematical indicators
    # --------------------------------------------------------

    strong_patterns = [

        r"\\frac",

        r"\\sqrt",

        r"\\times",

        r"\\approx",

        r"\\sum",

        r"\\int",

        r"\\mathrm",

        r"\\begin\{array\}",

        r"\\begin\{equation",

        r"\\left",

        r"\\right",

    ]


    for pattern in strong_patterns:

        if re.search(
            pattern,
            text
        ):

            return True


    # --------------------------------------------------------
    # Mathematical symbols
    # --------------------------------------------------------

    math_symbols = [

        "=",
        "≈",
        "≤",
        "≥",
        "±",
        "×",
        "÷",
        "∫",
        "Σ",
        "√",

    ]


    symbol_count = sum(
        text.count(symbol)
        for symbol in math_symbols
    )


    if symbol_count >= 3:

        return True


    # --------------------------------------------------------
    # Many numbers + operators
    # --------------------------------------------------------

    number_count = len(
        re.findall(
            r"\d+",
            text
        )
    )

    operator_count = len(
        re.findall(
            r"[=+\-*/]",
            text
        )
    )


    if (
        number_count >= 8
        and operator_count >= 4
    ):

        return True


    return False


# ============================================================
# 9. COUNTERS
# ============================================================

skipped_old = 0
skipped_new = 0

text_only = 0
pix2text_used = 0
blank_pages = 0
failed = 0


# ============================================================
# 10. PROCESS ALL PAGES
# ============================================================

for index in range(
    total_pages
):

    page_number = index + 1


    print()
    print(
        f"[{page_number}/{total_pages}]",
        end=" "
    )


    # ========================================================
    # PATHS
    # ========================================================

    old_output = (
        OLD_PIX2TEXT_DIR
        / f"page_{page_number}_ocr.json"
    )

    new_output = (
        OUTPUT_DIR
        / f"page_{page_number}_ocr.json"
    )


    # ========================================================
    # 10A. FIRST:
    # CHECK OLD PIX2TEXT OUTPUT
    #
    # This is the important part for your existing work.
    # ========================================================

    if old_output.exists():

        try:

            with open(
                old_output,
                "r",
                encoding="utf-8"
            ) as file:

                old_data = json.load(file)


            if (
                old_data.get("status")
                == "ocr_completed"
            ):

                # ------------------------------------------------
                # Copy the already completed JSON into the new
                # hybrid folder.
                #
                # Your original Pix2Text file is NOT modified.
                # ------------------------------------------------

                if not new_output.exists():

                    shutil.copy2(
                        old_output,
                        new_output
                    )


                print(
                    "ALREADY PIX2TEXT → SKIP ⏭️"
                )

                skipped_old += 1

                continue


        except Exception as error:

            print(
                "OLD JSON INVALID → processing again"
            )

            print(
                "Error:",
                error
            )


    # ========================================================
    # 10B. CHECK NEW HYBRID OUTPUT
    # ========================================================

    if new_output.exists():

        try:

            with open(
                new_output,
                "r",
                encoding="utf-8"
            ) as file:

                existing_data = json.load(file)


            if existing_data.get(
                "status"
            ) in (

                "text_extracted",

                "ocr_completed",

                "blank_page",

            ):

                print(
                    "ALREADY HYBRID → SKIP ⏭️"
                )

                skipped_new += 1

                continue


        except Exception:

            print(
                "Existing hybrid JSON invalid → retrying"
            )


    # ========================================================
    # 11. GET PAGE
    # ========================================================

    try:

        page = doc[index]


        # ====================================================
        # 12. FAST PDF TEXT EXTRACTION
        # ====================================================

        text = page.get_text(
            "text"
        )

        text = text.strip()


        # ====================================================
        # 13. BLANK PAGE
        # ====================================================

        if not text:

            output_data = {

                "page":
                    page_number,

                "source_pdf":
                    str(PDF_PATH),

                "content":
                    "",

                "method":
                    "none",

                "verified":
                    False,

                "status":
                    "blank_page"

            }


            with open(
                new_output,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    output_data,
                    file,
                    indent=4,
                    ensure_ascii=False
                )


            print(
                "BLANK PAGE"
            )

            blank_pages += 1

            continue


        # ====================================================
        # 14. DETECT POSSIBLE MATH
        # ====================================================

        math_page = looks_like_math(
            text
        )


        # ====================================================
        # 15. NORMAL TEXT PAGE
        # ====================================================

        if not math_page:

            output_data = {

                "page":
                    page_number,

                "source_pdf":
                    str(PDF_PATH),

                "content":
                    text,

                "method":
                    "pymupdf",

                "verified":
                    False,

                "status":
                    "text_extracted"

            }


            with open(
                new_output,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    output_data,
                    file,
                    indent=4,
                    ensure_ascii=False
                )


            print(
                "TEXT ONLY ⚡"
            )

            text_only += 1

            continue


        # ====================================================
        # 16. MATH PAGE → PIX2TEXT
        # ====================================================

        print(
            "MATH → PIX2TEXT..."
        )


        # ----------------------------------------------------
        # Temporary image
        # ----------------------------------------------------

        temp_image = (
            OUTPUT_DIR
            / f"_temp_page_{page_number}.png"
        )


        # ----------------------------------------------------
        # Render PDF page
        # ----------------------------------------------------

        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(
                1.5,
                1.5
            )
        )


        pixmap.save(
            str(temp_image)
        )


        # ----------------------------------------------------
        # Pix2Text
        # ----------------------------------------------------

        result = p2t.recognize(
            str(temp_image),
            return_text=True
        )


        # ====================================================
        # 17. SAVE PIX2TEXT RESULT
        # ====================================================

        output_data = {

            "page":
                page_number,

            "source_pdf":
                str(PDF_PATH),

            "pdf_text":
                text,

            "content":
                result,

            "method":
                "pix2text",

            "verified":
                False,

            "status":
                "ocr_completed"

        }


        with open(
            new_output,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                output_data,
                file,
                indent=4,
                ensure_ascii=False
            )


        # ====================================================
        # 18. DELETE TEMP IMAGE
        # ====================================================

        try:

            temp_image.unlink()

        except Exception:

            pass


        pix2text_used += 1

        print(
            "PIX2TEXT OK ✅"
        )


    except Exception as error:

        # ====================================================
        # 19. FAILURE
        # ====================================================

        failed += 1


        output_data = {

            "page":
                page_number,

            "source_pdf":
                str(PDF_PATH),

            "content":
                None,

            "method":
                "failed",

            "verified":
                False,

            "status":
                "needs_review",

            "error":
                str(error)

        }


        with open(
            new_output,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                output_data,
                file,
                indent=4,
                ensure_ascii=False
            )


        print(
            "FAILED ⚠️"
        )

        print(
            "Error:",
            error
        )

        continue


# ============================================================
# 20. CLOSE PDF
# ============================================================

doc.close()


# ============================================================
# 21. SUMMARY
# ============================================================

print()
print("=" * 70)
print("HYBRID OCR COMPLETE")
print("=" * 70)

print()
print("Total pages:", total_pages)

print(
    "Already processed by old Pix2Text:",
    skipped_old
)

print(
    "Already processed by hybrid:",
    skipped_new
)

print(
    "Text-only pages:",
    text_only
)

print(
    "Pix2Text pages:",
    pix2text_used
)

print(
    "Blank pages:",
    blank_pages
)

print(
    "Needs review:",
    failed
)

print()
print("Output:")
print(OUTPUT_DIR)

print("=" * 70)