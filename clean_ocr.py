from pathlib import Path
import json
import re


# ============================================================
# 1. PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# 2. INPUT DIRECTORY
# ============================================================

INPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "pix2text"
)


# ============================================================
# 3. OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "cleaned"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 4. FIND OCR JSON FILES
# ============================================================

files = sorted(
    INPUT_DIR.glob("page_*_ocr.json"),
    key=lambda x: int(
        x.stem.split("_")[1]
    )
)


print("=" * 70)
print("BATCH OCR CLEANING")
print("=" * 70)

print()
print("Input:", INPUT_DIR)
print("Output:", OUTPUT_DIR)
print("OCR files found:", len(files))


if not files:

    print()
    print("No OCR JSON files found ❌")
    raise SystemExit


# ============================================================
# 5. CLEAN OCR TEXT
# ============================================================

def clean_ocr_text(text):

    if text is None:
        return ""

    cleaned = str(text)

    # --------------------------------------------------------
    # Normalize line endings
    # --------------------------------------------------------

    cleaned = cleaned.replace(
        "\r\n",
        "\n"
    )

    cleaned = cleaned.replace(
        "\r",
        "\n"
    )

    # --------------------------------------------------------
    # Remove null characters
    # --------------------------------------------------------

    cleaned = cleaned.replace(
        "\x00",
        ""
    )

    # --------------------------------------------------------
    # Remove excessive spaces
    # --------------------------------------------------------

    cleaned = re.sub(
        r"[ \t]+",
        " ",
        cleaned
    )

    # --------------------------------------------------------
    # Remove excessive blank lines
    # --------------------------------------------------------

    cleaned = re.sub(
        r"\n\s*\n\s*\n+",
        "\n\n",
        cleaned
    )

    # --------------------------------------------------------
    # Remove spaces at beginning/end of lines
    # --------------------------------------------------------

    cleaned = "\n".join(
        line.strip()
        for line in cleaned.splitlines()
    )

    return cleaned.strip()


# ============================================================
# 6. PROCESS ALL OCR FILES
# ============================================================

successful = 0
failed = 0
skipped = 0


for index, input_path in enumerate(
    files,
    start=1
):

    page_number = int(
        input_path.stem.split("_")[1]
    )

    print()
    print(
        f"[{index}/{len(files)}] "
        f"Page {page_number}"
    )


    # ========================================================
    # OUTPUT PATH
    # ========================================================

    output_path = (
        OUTPUT_DIR
        / f"page_{page_number}_cleaned.json"
    )


    # ========================================================
    # RESUME SUPPORT
    # ========================================================

    if output_path.exists():

        try:

            with open(
                output_path,
                "r",
                encoding="utf-8"
            ) as file:

                existing = json.load(file)


            if (
                existing.get("status")
                == "cleaned"
            ):

                print(
                    "    Already cleaned - skipping ⏭️"
                )

                skipped += 1

                continue


        except Exception:

            print(
                "    Existing file invalid - retrying..."
            )


    # ========================================================
    # READ OCR JSON
    # ========================================================

    try:

        with open(
            input_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)


        # ====================================================
        # GET OCR CONTENT
        # ====================================================

        content = data.get(
            "content"
        )


        # ====================================================
        # CLEAN CONTENT
        # ====================================================

        cleaned_content = clean_ocr_text(
            content
        )


        # ====================================================
        # CREATE CLEANED JSON
        # ====================================================

        output_data = {

            "page":
                data.get(
                    "page",
                    page_number
                ),

            "source_image":
                data.get(
                    "source_image"
                ),

            "original_content":
                content,

            "content":
                cleaned_content,

            "verified":
                False,

            "status":
                "cleaned"
        }


        # ====================================================
        # SAVE
        # ====================================================

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                output_data,
                file,
                indent=4,
                ensure_ascii=False
            )


        successful += 1

        print(
            "    Cleaned: OK ✅"
        )


    except Exception as error:

        # ====================================================
        # ONE BAD PAGE MUST NOT STOP THE BATCH
        # ====================================================

        failed += 1

        output_data = {

            "page":
                page_number,

            "source_image":
                str(input_path),

            "original_content":
                None,

            "content":
                None,

            "verified":
                False,

            "status":
                "needs_review",

            "error":
                str(error)
        }


        with open(
            output_path,
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
            "    Cleaning: FAILED ⚠️"
        )

        print(
            "    Error:",
            error
        )

        continue


# ============================================================
# 7. FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("OCR CLEANING COMPLETE")
print("=" * 70)

print()
print("Total OCR files:", len(files))
print("Newly cleaned:", successful)
print("Skipped:", skipped)
print("Needs review:", failed)

print()
print("Output directory:")
print(OUTPUT_DIR)

print("=" * 70)