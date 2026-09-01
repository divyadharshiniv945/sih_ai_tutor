from pathlib import Path
import pymupdf


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PDF_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "college-physics-2e_-_WEB.pdf"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "equations"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

# Start with one page while testing
PAGE_NUMBER = 51


# ============================================================
# OPEN PDF
# ============================================================

doc = pymupdf.open(PDF_PATH)

page = doc[PAGE_NUMBER]

print("=" * 70)
print("EQUATION REGION DETECTION")
print("=" * 70)

print(f"Page: {PAGE_NUMBER}")
print()


# ============================================================
# GET TEXT BLOCKS
# ============================================================

blocks = page.get_text("dict")["blocks"]

candidate_count = 0


# ============================================================
# ANALYZE BLOCKS
# ============================================================

for block_number, block in enumerate(blocks):

    # Ignore image blocks
    if block["type"] != 0:
        continue

    lines = block.get("lines", [])

    for line_number, line in enumerate(lines):

        spans = line.get("spans", [])

        if not spans:
            continue

        text = ""

        x0 = float("inf")
        y0 = float("inf")
        x1 = 0
        y1 = 0

        for span in spans:

            span_text = span["text"]

            text += span_text

            x0 = min(x0, span["bbox"][0])
            y0 = min(y0, span["bbox"][1])

            x1 = max(x1, span["bbox"][2])
            y1 = max(y1, span["bbox"][3])


        text = text.strip()

        if not text:
            continue


        # ====================================================
        # MATHEMATICAL SYMBOLS
        # ====================================================

        math_symbols = [
            "=",
            "−",
            "-",
            "+",
            "×",
            "÷",
            "√",
            "∫",
            "Σ",
            "π",
            "θ",
            "α",
            "β",
            "γ",
            "Δ",
            "≈",
            "≤",
            "≥",
            "∞",
            "²",
            "³"
        ]


        symbol_count = 0

        for symbol in math_symbols:

            symbol_count += text.count(symbol)


        # ====================================================
        # SIMPLE EQUATION SIGNALS
        # ====================================================

        has_equal = "=" in text

        has_math_symbol = symbol_count >= 1

        contains_digit = any(
            character.isdigit()
            for character in text
        )


        # ====================================================
        # SCORE
        # ====================================================

        score = 0

        if has_equal:
            score += 3

        if has_math_symbol:
            score += 2

        if contains_digit:
            score += 1


        # ====================================================
        # CANDIDATE
        # ====================================================

        if score >= 3:

            candidate_count += 1

            print("-" * 70)

            print(f"Candidate {candidate_count}")

            print(f"Text: {text}")

            print(
                f"Bounding box: "
                f"x={x0:.1f} → {x1:.1f}, "
                f"y={y0:.1f} → {y1:.1f}"
            )

            print(f"Score: {score}")


            # =================================================
            # CROP EQUATION REGION
            # =================================================

            rect = pymupdf.Rect(
                x0 - 10,
                y0 - 10,
                x1 + 10,
                y1 + 10
            )


            # Keep rectangle inside page
            rect &= page.rect


            # Render crop
            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2),
                clip=rect,
                alpha=False
            )


            output_path = (
                OUTPUT_DIR
                / f"page_{PAGE_NUMBER}_candidate_{candidate_count}.png"
            )


            pix.save(output_path)


            print(f"Saved: {output_path}")


# ============================================================
# FINISHED
# ============================================================

print()
print("=" * 70)
print("DETECTION COMPLETE")
print("=" * 70)

print(f"Candidates found: {candidate_count}")

doc.close()