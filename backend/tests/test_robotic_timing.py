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


def _received(event, seconds):
    event.created_at = START + timedelta(seconds=seconds)
    return event


@pytest.mark.timeline
def test_page_times_longer_than_the_server_saw_are_caught():
    engine = BotDetectionEngine()

    def check(events):
        context = engine._session_context(events, "Mozilla/5.0 (Windows NT 10.0)")
        context["session_started"] = START
        return dict(engine._decisive_signals(events, context))

    # Claims 3 pages of 60 s, but the server received everything within 20 s.
    faked = [_received(_ev("form_submit", n * 60000, element="qos-page:60000"), n * 10) for n in range(3)]
    assert "made up" in check(faked)["timeline_mismatch"]
    # Honest: the server saw about as long as the pages claim (sends arrive a little late).
    honest = [_received(_ev("form_submit", n * 60000, element="qos-page:60000"), (n + 1) * 60 + 2) for n in range(3)]
    assert "timeline_mismatch" not in check(honest)
    # Events never stored (no arrival time) are not judged.
    loose = [_ev("form_submit", n * 60000, element="qos-page:60000") for n in range(3)]
    assert "timeline_mismatch" not in dict(engine._decisive_signals(loose, engine._session_context(loose, "Mozilla/5.0 (Windows NT 10.0)")))


def test_behaviour_evidence_adds_up_across_checks():
    from app.utils.helpers import calculate_confidence_score as score

    quiet = {"keystroke_analysis": 0.0, "mouse_analysis": 0.0, "timing_analysis": 0.0, "device_analysis": 0.0, "network_analysis": 0.0}
    assert score(quiet) == 0.0
    assert score({**quiet, "keystroke_analysis": 0.3, "mouse_analysis": 0.3}) < 0.3  # phone with few key presses
    assert score({**quiet, "keystroke_analysis": 1.0}) < 0.7  # one check alone is a lead, not a verdict
    assert score({**quiet, "keystroke_analysis": 1.0, "mouse_analysis": 1.0}) >= 0.7  # two agreeing checks are


@pytest.mark.asyncio
async def test_events_sent_twice_count_once():
    engine = BotDetectionEngine()
    once = [_ev("mouse_click", n * 400, element=f"r{n}", x=10 * n, y=5) for n in range(4)]
    twice = once + [_ev("mouse_click", n * 400, element=f"r{n}", x=10 * n, y=5) for n in range(4)]
    assert len(engine._without_repeats(twice)) == 4
    a = await engine.analyze_session(once, "Mozilla/5.0 (Windows NT 10.0)")
    b = await engine.analyze_session(twice, "Mozilla/5.0 (Windows NT 10.0)")
    assert a.flagged_patterns["event_distribution"] == b.flagged_patterns["event_distribution"] == {"mouse_click": 4}


def test_stored_events_leave_out_page_details_kept_elsewhere():
    from app.controllers.detection_controller import _event_payload

    event = {"event_type": "mouse_click", "timestamp": "2026-11-27T12:00:00Z", "x": 4, "y": 9, "trusted": True,
             "page_url": "https://s.example/survey?email=a@b.c", "user_agent": "UA", "survey_id": "S",
             "respondent_id": "R", "platform_id": "decipher", "screen_width": 1920, "element_id": "r1"}
    assert _event_payload(event) == {"x": 4, "y": 9, "trusted": True}


@pytest.mark.asyncio
async def test_two_reasons_for_one_signal_lift_like_one():
    events = [_ev("page_load", 0, webdriver=True), _ev("mouse_move", 100, x=1, y=1)]
    one = await BotDetectionEngine().analyze_session(events, "Mozilla/5.0 HeadlessChrome/130.0")
    assert one.flagged_patterns["decisive_codes"] == ["automation"] and one.confidence_score == 0.85
