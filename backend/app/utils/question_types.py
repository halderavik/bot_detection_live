"""Question types the tracker registers that are not free text (never text-scored)."""

# "personal" (contact and identity boxes, see utils/privacy.py) is listed so those
# answers are never text-scored, compared for duplicates, or counted as unchecked.
CLOSED_QUESTION_TYPES = {"grid", "matrix", "single", "single_choice", "multi", "multiple_choice", "multi_choice", "rating", "scale", "choice", "personal"}
