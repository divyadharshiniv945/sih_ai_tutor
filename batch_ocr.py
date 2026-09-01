from pathlib import Path
import json
from concurrent.futures import ProcessPoolExecutor, as_completed

from pix2text import Pix2Text


# ============================================================
# 1. PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# 2. INPUT PAGES
# ============================================================

INPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "pages"
)


# ============================================================
# 3. OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "pix2text"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 4. SETTINGS
# ============================================================

# Start with 2 workers.
# If your PC has enough CPU/RAM, try 3 or 4 later.
MAX_WORKERS = 2


# ============================================================
# 5. FIND ALL PAGES
# ============================================================

images = sorted(
    INPUT_DIR.glob("page_*.png"),
    key=lambda x: int(
        x.stem.split("_")[1]
    )
)


print("=" * 70)
print("PARALLEL BATCH PIX2TEXT OCR")
print("=" * 70)

print()
print("Input:", INPUT_DIR)
print("Output:", OUTPUT_DIR)
print("Pages found:", len(images))
print("Workers:", MAX_WORKERS)


if not images:

    print()
    print("No page images found ❌")
    raise SystemExit


# ============================================================
# 6. CHECK WHICH PAGES ARE ALREADY DONE
# ============================================================

pending_images = []
skipped = 0

print()
print("Checking existing OCR results...")


for image_path in images:

    page_number = int(
        image_path.stem.split("_")[1]
    )

    output_path = (
        OUTPUT_DIR
        / f"page_{page_number}_ocr.json"
    )

    # --------------------------------------------------------
    # Already successfully processed?
    # --------------------------------------------------------

    if output_path.exists():

        try:

            with open(
                output_path,
                "r",
                encoding="utf-8"
            ) as file:

                existing_data = json.load(file)

            if (
                existing_data.get("status")
                == "ocr_completed"
            ):

                skipped += 1
                continue

        except Exception:

            # Broken JSON → process again
            pass

    pending_images.append(image_path)


print()
print("Already completed:", skipped)
print("Remaining:", len(pending_images))


if not pending_images:

    print()
    print("All pages are already processed ✅")
    raise SystemExit


# ============================================================
# 7. WORKER FUNCTION
# ============================================================

def process_page(image_path):

    # --------------------------------------------------------
    # IMPORTANT:
    # Each worker creates its own Pix2Text instance.
    # --------------------------------------------------------

    p2t = Pix2Text()

    page_number = int(
        image_path.stem.split("_")[1]
    )

    output_path = (
        OUTPUT_DIR
        / f"page_{page_number}_ocr.json"
    )

    try:

        # ----------------------------------------------------
        # PIX2TEXT OCR
        # ----------------------------------------------------

        result = p2t.recognize(
            str(image_path),
            return_text=True
        )


        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        output_data = {

            "page":
                page_number,

            "source_image":
                str(image_path),

            "content":
                result,

            "verified":
                False,

            "status":
                "ocr_completed"
        }


        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

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


        return (
            page_number,
            True,
            None
        )


    except Exception as error:

        # ----------------------------------------------------
        # SAVE FAILED PAGE
        # ----------------------------------------------------

        output_data = {

            "page":
                page_number,

            "source_image":
                str(image_path),

            "content":
                None,

            "verified":
                False,

            "status":
                "needs_review",

            "error":
                str(error)
        }


        try:

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

        except Exception:
            pass


        return (
            page_number,
            False,
            str(error)
        )


# ============================================================
# 8. RUN PARALLEL OCR
# ============================================================

successful = 0
failed = 0

print()
print("=" * 70)
print("STARTING OCR")
print("=" * 70)


if __name__ == "__main__":

    with ProcessPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                process_page,
                image_path
            ): image_path
            for image_path in pending_images
        }


        completed = 0


        for future in as_completed(futures):

            completed += 1

            image_path = futures[future]

            try:

                page_number, success, error = (
                    future.result()
                )


                if success:

                    successful += 1

                    print(
                        f"[{completed}/{len(pending_images)}] "
                        f"Page {page_number}: OCR OK ✅"
                    )

                else:

                    failed += 1

                    print(
                        f"[{completed}/{len(pending_images)}] "
                        f"Page {page_number}: "
                        f"FAILED ⚠️"
                    )

                    print(
                        "    Error:",
                        error
                    )


            except Exception as error:

                failed += 1

                print(
                    f"[{completed}/{len(pending_images)}] "
                    f"Worker failed ⚠️"
                )

                print(
                    "    Error:",
                    error
                )


# ============================================================
# 9. FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("PIX2TEXT BATCH COMPLETE")
print("=" * 70)

print()
print("Total pages:", len(images))
print("Previously completed:", skipped)
print("Newly processed:", successful)
print("Needs review:", failed)

print()
print("Output directory:")
print(OUTPUT_DIR)

print("=" * 70)