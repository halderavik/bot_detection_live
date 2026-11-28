"""The robotic_timing signal: machine-exact typing or ruler-straight, constant-speed mouse paths."""

import math
import random
from datetime import datetime, timedelta, timezone

import pytest

from app.models import BehaviorData
from app.services.bot_detection_engine import BotDetectionEngine

START = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)


def _ev(kind, ms, element="q1", **data):
    return BehaviorData(session_id="s", event_type=kind, timestamp=START + timedelta(milliseconds=ms),
                        element_id=element, event_data=data)


def _typing(gaps_by_field, key="char"):
    events, t = [], 0
    for field, gaps in gaps_by_field.items():
        t += 5000
        for gap in gaps:
            t += gap
            events.append(_ev("keystroke", t, field, key=key))
    return events


def _signals(events):
    engine = BotDetectionEngine()
    return engine._robotic_timing(engine._session_context(sorted(events, key=lambda e: e.timestamp), "Mozilla/5.0 (Windows NT 10.0)"))


def test_machine_exact_typing_in_three_answers_is_caught():
    events = _typing({f"q{n}": [30] * 25 for n in range(3)})
    assert "machine-exact timing" in _signals(events)


def test_human_typing_and_key_repeat_are_not():
    rnd = random.Random(1)
    human = _typing({f"q{n}": [max(45, int(rnd.gauss(170, 70))) for _ in range(40)] for n in range(3)})
    assert _signals(human) is None
    # Holding Backspace repeats at a fixed rate; only printable keys count.
    repeat = _typing({f"q{n}": [33] * 30 for n in range(3)}, key="Backspace")
    assert _signals(repeat) is None
    # Two exact stretches are not enough, nor is one exact field among human ones.
    assert _signals(_typing({"q0": [30] * 25, "q1": [30] * 25})) is None
    mixed = _typing({"q0": [30] * 25, "q1": [30] * 25, "q2": [max(45, int(rnd.gauss(170, 70))) for _ in range(30)]})
    assert _signals(mixed) is None


def test_straight_constant_speed_mouse_is_caught_and_curved_paths_are_not():
    straight, t = [], 0
    for line in range(4):
        x0, y0, dx, dy = 100 + 50 * line, 200, 17, 9
        for i in range(12):
            t += 100
            straight.append(_ev("mouse_move", t, x=int(x0 + dx * i), y=int(y0 + dy * i)))
    assert "ruler-straight" in _signals(straight)

    rnd, curved, t = random.Random(2), [], 0
    for line in range(4):
        for i in range(12):
            f = (i + 1) / 12
            bend = math.sin(f * math.pi) * 60
            t += rnd.randint(100, 260)
            curved.append(_ev("mouse_move", t, x=int(100 + 600 * f + bend + rnd.uniform(-4, 4)), y=int(200 + 300 * f - bend * 0.4 + rnd.uniform(-4, 4))))
    assert _signals(curved) is None


@pytest.mark.asyncio
async def test_signal_makes_the_session_a_bot_and_is_a_known_rule_code():
    from app.services.decipher_tracking import BOT_SIGNALS
    from app.services.quality_variables import REASON_NUMBERS

    events = _typing({f"q{n}": [30] * 25 for n in range(3)})
    events += [_ev("form_submit", 200000 + n, element_id=f"qos-page:{n}") for n in range(3)]
    result = await BotDetectionEngine().analyze_session(events, "Mozilla/5.0 (Windows NT 10.0)")
    assert "robotic_timing" in result.flagged_patterns["decisive_codes"] and result.is_bot
    assert "robotic_timing" in BOT_SIGNALS and REASON_NUMBERS["robotic_timing"] == 7


def test_a_grid_page_counts_once():
    """The grid copy of a page's submit is not a second page (nor a second untyped answer)."""
    engine = BotDetectionEngine()
    one_page = [_ev("mouse_click", n * 300, element="r%d" % n) for n in range(4)]
    one_page += [_ev("form_submit", 5000, element="qos-page:5000", untyped_answers=1),
                 _ev("form_submit", 5000, element="qos-grid:3,4,1,5", untyped_answers=1)]
    found = engine._decisive_signals(one_page, engine._session_context(one_page, "Mozilla/5.0 (Windows NT 10.0)"))
    codes = [code for code, _ in found]
    assert "no_input" not in codes  # one page only; no_input needs two
    assert [text for code, text in found if code == "untyped_answers"] == [
        "1 open-ended answer(s) appeared without any typing, pasting, or dictation"]
    two_pages = one_page + [_ev("form_submit", 9000, element="qos-page:4000")]
    assert "no_input" in [code for code, _ in engine._decisive_signals(two_pages, engine._session_context(two_pages, "Mozilla/5.0 (Windows NT 10.0)"))]
