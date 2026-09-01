from pathlib import Path
import json
import re
import traceback

import 


# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "equations"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "validated"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "all_pages_final_validation.json"
)


# ============================================================
# 2. INITIALIZE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

numerical_parser = numerical_parser_.NumericalParser()


# ============================================================
# 3. BASIC LATEX CLEANING
# ============================================================

def clean_expression(text):

    if text is None:
        return ""

    text = str(text).strip()

    # Remove surrounding braces when they are only wrappers
    while (
        len(text) >= 2
        and text[0] == "{"
        and text[-1] == "}"
    ):
        text = text[1:-1].strip()

    # OCR: \times
    text = text.replace(
        r"\times",
        "*"
    )

    # OCR: \approx
    text = text.replace(
        r"\approx",
        "~"
    )

    # Remove \, and spacing commands
    text = re.sub(
        r"\\[,;:! ]",
        " ",
        text
    )

    # Remove \mathrm
    text = re.sub(
        r"\\mathrm\s*\{([^{}]*)\}",
        r"\1",
        text
    )

    # Remove \text
    text = re.sub(
        r"\\text\s*\{([^{}]*)\}",
        r"\1",
        text
    )

    # Normalize spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# 4. SPLIT EQUATION CHAIN
# ============================================================

def split_relationships(expression):

    expression = expression.strip()

    # First split on equality / approximation.
    parts = re.split(
        r"\s*(=|\\approx|≈|~)\s*",
        expression
    )

    relationships = []

    if len(parts) < 3:
        return relationships

    for i in range(0, len(parts) - 2, 2):

        lhs = parts[i].strip()
        operator = parts[i + 1].strip()
        rhs = parts[i + 2].strip()

        if not lhs or not rhs:
            continue

        relationships.append(
            {
                "lhs": lhs,
                "operator": operator,
                "rhs": rhs
            }
        )

    return relationships


# ============================================================
# 5. EXTRACT NUMERICAL VALUE
# ============================================================

def parse_quantity(expression):

    expression = expression.strip()

    try:

        result = numerical_parser.parse(
            expression
        )

        # Your NumericalParser may return
        # a quantity directly or a dictionary.

        if hasattr(
            result,
            "dimensionality"
        ):
            return result

        if isinstance(result, dict):

            for key in (
                "quantity",
                "value",
                "result",
                "parsed"
            ):

                value = result.get(key)

                if hasattr(
                    value,
                    "dimensionality"
                ):
                    return value

        return None

    except Exception:

        return None


# ============================================================
# 6. VALIDATE NUMERICAL RELATIONSHIP
# ============================================================

def validate_numerical(
    lhs,
    operator,
    rhs
):

    lhs_value = parse_quantity(lhs)
    rhs_value = parse_quantity(rhs)

    if (
        lhs_value is None
        or rhs_value is None
    ):

        return {
            "validation_type":
                "numerical_and_dimensional",

            "status":
                "needs_review",

            "usable_for_tutor":
                False,

            "details": {
                "reason":
                    "Could not parse numerical quantities"
            }
        }

    try:

        # ----------------------------------------------------
        # Dimension check
        # ----------------------------------------------------

        if (
            lhs_value.dimensionality
            !=
            rhs_value.dimensionality
        ):

            return {
                "validation_type":
                    "numerical_and_dimensional",

                "status":
                    "needs_review",

                "usable_for_tutor":
                    False,

                "details": {
                    "calculated":
                        str(lhs_value),

                    "source_value":
                        str(rhs_value),

                    "dimensions_match":
                        False,

                    "numerical_match":
                        False,

                    "reason":
                        "Dimension mismatch"
                }
            }

        # ----------------------------------------------------
        # Convert RHS to LHS unit
        # ----------------------------------------------------

        rhs_converted = rhs_value.to(
            lhs_value.units
        )

        lhs_number = float(
            lhs_value.magnitude
        )

        rhs_number = float(
            rhs_converted.magnitude
        )

        # ----------------------------------------------------
        # Relative error
        # ----------------------------------------------------

        relative_error = (
            abs(lhs_number - rhs_number)
            /
            max(abs(lhs_number), 1e-12)
        )

        # Approximation can tolerate more error.
        if operator in (
            r"\approx",
            "≈",
            "~"
        ):

            tolerance = 0.05

        else:

            tolerance = 0.01

        numerical_match = (
            relative_error
            <= tolerance
        )

        return {
            "validation_type":
                "numerical_and_dimensional",

            "status":
                (
                    "validated"
                    if numerical_match
                    else "needs_review"
                ),

            "usable_for_tutor":
                numerical_match,

            "details": {

                "calculated":
                    str(lhs_value),

                "source_value":
                    str(rhs_converted),

                "relative_error":
                    relative_error,

                "percentage_error":
                    relative_error * 100,

                "tolerance":
                    tolerance,

                "dimensions_match":
                    True,

                "numerical_match":
                    numerical_match
            }
        }

    except Exception as error:

        return {
            "validation_type":
                "numerical_and_dimensional",

            "status":
                "needs_review",

            "usable_for_tutor":
                False,

            "details": {
                "reason":
                    str(error)
            }
        }


# ============================================================
# 7. VALIDATE SYMBOLIC RELATIONSHIP
# ============================================================

def validate_symbolic(
    lhs,
    operator,
    rhs
):

    # --------------------------------------------------------
    # Simple symbolic equations are retained.
    #
    # Example:
    #
    # V = A * H
    #
    # We don't numerically calculate these because
    # V, A and H may represent physical quantities.
    # --------------------------------------------------------

    normalized_lhs = clean_expression(
        lhs
    )

    normalized_rhs = clean_expression(
        rhs
    )

    if (
        not normalized_lhs
        or not normalized_rhs
    ):

        return {
            "validation_type":
                "symbolic",

            "status":
                "needs_review",

            "usable_for_tutor":
                False
        }

    return {
        "validation_type":
            "symbolic",

        "status":
            "validated",

        "usable_for_tutor":
            True,

        "details": {

            "relationship":
                f"{normalized_lhs} "
                f"{operator} "
                f"{normalized_rhs}"
        }
    }


# ============================================================
# 8. VALIDATE ONE EQUATION
# ============================================================

def validate_equation(
    equation
):

    clean_latex = equation.get(
        "clean_latex",
        ""
    )

    relationships = split_relationships(
        clean_latex
    )

    row_results = []

    for row_id, relationship in enumerate(
        relationships,
        start=1
    ):

        lhs = relationship["lhs"]
        operator = relationship["operator"]
        rhs = relationship["rhs"]

        # ----------------------------------------------------
        # Try numerical validation first
        # ----------------------------------------------------

        numerical_result = validate_numerical(
            lhs,
            operator,
            rhs
        )

        if (
            numerical_result["status"]
            == "validated"
        ):

            result = numerical_result

        else:

            # ------------------------------------------------
            # If it looks symbolic, retain it.
            # ------------------------------------------------

            contains_symbol = bool(
                re.search(
                    r"[A-Za-z]",
                    lhs
                )
                or
                re.search(
                    r"[A-Za-z]",
                    rhs
                )
            )

            contains_number = bool(
                re.search(
                    r"\d",
                    lhs
                )
                or
                re.search(
                    r"\d",
                    rhs
                )
            )

            if (
                contains_symbol
                and not contains_number
            ):

                result = validate_symbolic(
                    lhs,
                    operator,
                    rhs
                )

            else:

                result = numerical_result

        row_results.append(
            {
                "row_id": row_id,

                "relationship": relationship,

                **result
            }
        )

    # ========================================================
    # OVERALL STATUS
    # ========================================================

    if not row_results:

        overall_status = "needs_review"
        usable = False

    else:

        statuses = [
            row["status"]
            for row in row_results
        ]

        if all(
            status == "validated"
            for status in statuses
        ):

            overall_status = "validated"
            usable = True

        elif any(
            status == "validated"
            for status in statuses
        ):

            overall_status = (
                "partially_validated"
            )

            usable = True

        else:

            overall_status = "needs_review"
            usable = False

    return {
        "equation_id":
            equation.get(
                "equation_id"
            ),

        "raw_latex":
            equation.get(
                "raw_latex"
            ),

        "clean_latex":
            clean_latex,

        "validation_status":
            overall_status,

        "problems": [],

        "verified":
            overall_status == "validated",

        "row_validation":
            row_results,

        "overall_validation_status":
            overall_status,

        "usable_for_tutor":
            usable
    }


# ============================================================
# 9. VALIDATE ONE PAGE
# ============================================================

def validate_page(
    page_data
):

    validated_equations = []

    for equation in page_data.get(
        "equations",
        []
    ):

        try:

            result = validate_equation(
                equation
            )

        except Exception as error:

            # IMPORTANT:
            # One bad equation must NEVER
            # stop the entire 1671-page batch.

            result = {
                "equation_id":
                    equation.get(
                        "equation_id"
                    ),

                "raw_latex":
                    equation.get(
                        "raw_latex"
                    ),

                "clean_latex":
                    equation.get(
                        "clean_latex"
                    ),

                "validation_status":
                    "needs_review",

                "problems": [
                    str(error)
                ],

                "verified":
                    False,

                "row_validation": [],

                "overall_validation_status":
                    "needs_review",

                "usable_for_tutor":
                    False
            }

        validated_equations.append(
            result
        )

    return {
        "page":
            page_data.get("page"),

        "source_image":
            page_data.get(
                "source_image"
            ),

        "text":
            page_data.get("text"),

        "equations":
            validated_equations
    }


# ============================================================
# 10. BATCH PROCESS
# ============================================================

def main():

    input_files = sorted(
        INPUT_DIR.glob(
            "page_*_cleaned.json"
        )
    )

    print("=" * 70)
    print("BATCH EQUATION VALIDATION")
    print("=" * 70)

    print()
    print(
        f"Input files found: "
        f"{len(input_files)}"
    )

    all_pages = []

    total_equations = 0
    validated_equations = 0
    review_equations = 0

    for index, input_path in enumerate(
        input_files,
        start=1
    ):

        print()
        print(
            f"[{index}/{len(input_files)}] "
            f"Processing {input_path.name}"
        )

        try:

            with open(
                input_path,
                "r",
                encoding="utf-8"
            ) as file:

                page_data = json.load(file)

            result = validate_page(
                page_data
            )

            for equation in result[
                "equations"
            ]:

                total_equations += 1

                if (
                    equation[
                        "validation_status"
                    ]
                    == "validated"
                ):

                    validated_equations += 1

                else:

                    review_equations += 1

                print(
                    f"    Equation "
                    f"{equation['equation_id']}: "
                    f"{equation['validation_status']}"
                )

            all_pages.append(
                result
            )

        except Exception as error:

            # ------------------------------------------------
            # Page-level failure.
            # Continue processing the rest.
            # ------------------------------------------------

            print(
                f"    PAGE ERROR: {error}"
            )

            all_pages.append(
                {
                    "page":
                        page_data.get("page")
                        if "page_data"
                        in locals()
                        else None,

                    "source_image":
                        None,

                    "text":
                        None,

                    "equations": [],

                    "page_status":
                        "needs_review",

                    "error":
                        str(error)
                }
            )

            continue

    # ========================================================
    # SAVE
    # ========================================================

    output_data = {

        "project":
            "SIH Socratic Tutor",

        "total_pages":
            len(all_pages),

        "total_equations":
            total_equations,

        "validated_equations":
            validated_equations,

        "needs_review_equations":
            review_equations,

        "pages":
            all_pages
    }

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

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("BATCH VALIDATION COMPLETE")
    print("=" * 70)

    print()
    print(
        f"Pages processed: "
        f"{len(all_pages)}"
    )

    print(
        f"Equations processed: "
        f"{total_equations}"
    )

    print(
        f"Validated: "
        f"{validated_equations}"
    )

    print(
        f"Needs review: "
        f"{review_equations}"
    )

    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )

    print("=" * 70)


# ============================================================
# 11. RUN
# ============================================================

if __name__ == "__main__":
    main()