"""
Quality rules: what counts as a bot, a speeder, a poor answer, or fraud for one survey.

Every survey starts on the defaults. Rules apply whenever live quality results load,
so edits take effect at once on the dashboard, the CSV export, and the LQ_ variables
added to a data file. What happens inside the survey (ending it on a bot signal, the
privacy notice) is chosen when tracking is added to the Decipher XML.
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey_quality_rules import SurveyQualityRules
from app.services.decipher_tracking import BOT_SIGNALS

# Reasons the text check can give for a poor open-ended answer.
TEXT_REASONS: Dict[str, str] = {
    "gibberish": "Gibberish",
    "generic": 'Generic ("good", "nothing")',
    "irrelevant": "Off-topic",
    "copy_paste": "Copied or repeated text",
    "low_quality": "Low effort",
}


class QualityRules(BaseModel):
    """One survey's quality rules. Field defaults are the recommended settings."""

    # Bot detection
    bot_threshold: float = Field(0.7, ge=0.3, le=0.99)
    bot_signals: List[str] = Field(default_factory=lambda: list(BOT_SIGNALS))

    # Speed and attention
    speeder_page_seconds: float = Field(3.5, ge=0.5, le=60)
    speeder_median_share: float = Field(0.5, ge=0, le=0.9)
    straightline_min_rows: int = Field(3, ge=2, le=30)

    # Open ends
    text_reasons: List[str] = Field(default_factory=lambda: list(TEXT_REASONS))
    flag_pasted: bool = True

    # Fraud
    fraud_threshold: float = Field(0.7, ge=0.3, le=0.99)
    flag_duplicates: bool = True
    flag_datacenter: bool = True

    @field_validator("bot_signals")
    @classmethod
    def _known_signals(cls, value: List[str]) -> List[str]:
        unknown = sorted(set(value) - set(BOT_SIGNALS))
        if unknown:
            raise ValueError(f"Unknown bot signals: {', '.join(unknown)}")
        return [code for code in BOT_SIGNALS if code in value]

    @field_validator("text_reasons")
    @classmethod
    def _known_reasons(cls, value: List[str]) -> List[str]:
        unknown = sorted(set(value) - set(TEXT_REASONS))
        if unknown:
            raise ValueError(f"Unknown text reasons: {', '.join(unknown)}")
        return [code for code in TEXT_REASONS if code in value]


def defaults() -> QualityRules:
    """Return the recommended rules."""
    return QualityRules()


def _parse(stored: Any) -> QualityRules:
    """Rules from a stored dict; unknown fields are ignored and bad values fall back to defaults."""
    if not isinstance(stored, dict):
        return QualityRules()
    known = {key: value for key, value in stored.items() if key in QualityRules.model_fields}
    try:
        return QualityRules(**known)
    except ValueError:
        return QualityRules()


async def get_rules(db: AsyncSession, survey_id: str) -> QualityRules:
    """Return a survey's rules (defaults when it has none saved).

    Args:
        db: Database session.
        survey_id: Tracking survey id.

    Returns:
        The survey's rules.
    """
    if not survey_id:
        return QualityRules()
    row = await db.get(SurveyQualityRules, survey_id)
    return _parse(row.rules) if row is not None else QualityRules()


async def save_rules(db: AsyncSession, survey_id: str, rules: "QualityRules | None") -> QualityRules:
    """Store a survey's rules; ``None`` restores the defaults.

    Args:
        db: Database session.
        survey_id: Tracking survey id.
        rules: New rules, or None.

    Returns:
        The rules now in force.
    """
    row = await db.get(SurveyQualityRules, survey_id)
    if rules is None:
        if row is not None:
            await db.delete(row)
    elif row is None:
        db.add(SurveyQualityRules(survey_id=survey_id, rules=rules.model_dump()))
    else:
        row.rules = rules.model_dump()
    await db.commit()
    return rules if rules is not None else QualityRules()


def changed_fields(rules: QualityRules) -> List[str]:
    """Names of the rules that differ from the defaults."""
    base = defaults().model_dump()
    return [name for name, value in rules.model_dump().items() if base[name] != value]


def rules_state(rules: QualityRules) -> Dict[str, Any]:
    """Rules in force, the defaults, what changed, and labels for the editor."""
    return {
        "rules": rules.model_dump(),
        "defaults": defaults().model_dump(),
        "changed": changed_fields(rules),
        "bot_signals": dict(BOT_SIGNALS),
        "text_reasons": dict(TEXT_REASONS),
    }
