"""
Respondent pressure test: plays many respondents through the same API calls the live
tracker (backend/app/assets/live_quality_tracker.js) makes from a Decipher survey,
then reads Live Quality results and the CSV export and scores them against what each
respondent type should get.

usage: python simulate.py <out_dir> [survey_id]
env:   BASE (default production API), CONCURRENCY (default 6)
"""
import asyncio, csv, io, json, math, os, random, sys, time, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

BASE = os.environ.get("BASE", "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1")
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SURVEY = sys.argv[2] if len(sys.argv) > 2 else "PRESSURE_RESP_" + datetime.now().strftime("%Y%m%d_%H%M")
CONC = int(os.environ.get("CONCURRENCY", "6"))
PAGE_URL = "https://selfserve.decipherinc.com/survey/selfserve/563/261185"
rnd = random.Random(20261127)

STATS = {"requests": 0, "429": 0, "errors": [], "latency": []}

# ---------------------------------------------------------------- survey layout
OPEN = [
    ("oe_brand", "Why do you choose your favourite coffee brand?"),
    ("oe_visit", "Describe your last visit to a coffee shop."),
    ("oe_more", "What would make you buy coffee more often?"),
]
GRID_ROWS = 6
# pages: 1 intro radio, 2 grid A, 3 open end 1, 4 open end 2, 5 grid B, 6 open end 3, then final page
PAGES = ["intro", "gridA", "oe0", "oe1", "gridB", "oe2"]

GOOD = [
    ["I like that it tastes smooth and never bitter, and the shop near my office sells it fresh.",
     "Mostly price and taste. Their medium roast is the one my partner and I both enjoy in the morning.",
     "It reminds me of the coffee my dad made. I tried others but kept coming back to the same beans.",
     "Fair trade matters to me and the flavour is consistent, so I don't have to think about it.",
     "Honestly it's about convenience, the grocery store always has it on sale and it's decent quality.",
     "Strong flavour without being burnt. The dark roast works well with a splash of oat milk.",
     "My barista recommended it two years ago and I've stuck with it ever since because it's reliable.",
     "I care about the farm sourcing story and the bag is resealable which keeps it fresh longer.",
     "Good value for the amount you get, and the caramel notes are really nice in a cold brew.",
     "It's local to my city and I like supporting a small roaster rather than a big chain.",
     "The decaf is the only one that doesn't taste like cardboard, so I buy their regular too.",
     "Chocolatey taste and low acidity, which is easier on my stomach than lighter roasts.",
     "Fresh roast dates printed on the bag, I trust them more than brands that hide it.",
     "I mostly pick it because the espresso blend makes a good crema in my home machine.",
     "Tried it at a friend's place and liked it, the price is fair compared to cafes."],
    ["Went to the cafe on Queen street on Saturday, ordered a flat white and a croissant, it was busy but quick.",
     "Last Tuesday I met a colleague at Starbucks, we sat by the window for an hour and talked about a project.",
     "Grabbed an iced latte on the way to the gym. The line was long and they got my name wrong again.",
     "I worked from a small coffee shop downtown, the wifi was slow but the americano was great.",
     "Took my kids for hot chocolate and I had a cappuccino. Staff were friendly and it was clean.",
     "Stopped at the drive-through on Monday morning, ordered a medium double double, done in five minutes.",
     "Visited a new third wave place with a friend, tried a pour over from Ethiopia, a bit fruity for me.",
     "Ordered on the app and picked it up, the mocha was lukewarm which was disappointing this time.",
     "Met my sister for brunch at a cafe, we shared a pastry and I had two refills of drip coffee.",
     "Quick espresso at the airport before my flight, overpriced but I needed the caffeine.",
     "Studied for exams at the campus cafe for three hours with a large chai latte.",
     "It was raining so I ducked into a cafe and had a cortado while waiting for the bus.",
     "Went with coworkers after lunch, I ordered a cold brew, they were out of oat milk.",
     "Sunday morning I went alone with a book, had a latte and a muffin, very relaxing.",
     "Drove through on my way to work, the barista was cheerful and the coffee was hot."],
    ["Lower prices or a loyalty card that actually gives a free drink after a few visits.",
     "If there was a decent cafe closer to my home I would definitely go more often.",
     "Probably more decaf options in the afternoon because I can't sleep if I have caffeine late.",
     "A subscription that delivers fresh beans every two weeks at a discount would work for me.",
     "Better seating and longer opening hours, most places near me close at six.",
     "Healthier milk alternatives without the extra charge, I'm tired of paying more for oat milk.",
     "Seasonal flavours that aren't overly sweet, something like a lightly spiced latte.",
     "Faster mobile ordering, I skip coffee when the queue is out the door.",
     "Honestly a smaller size at a lower price, the medium is too much for me.",
     "More sustainable packaging, I'd feel better buying the pods if they were compostable.",
     "If my office had a good machine I'd drink it every day instead of tea.",
     "Promotions on weekends or a buy one get one for bringing a friend.",
     "Recyclable cups and a discount for bringing my own mug.",
     "A wider choice of single origin beans in the supermarket.",
     "Nothing major, maybe free refills on drip coffee when sitting in."],
]
BAD = [["asdkjh qwe zzxv", "good", "Paris is the capital of France and the Eiffel tower is tall."],
       ["nothing", "ok", "dfgdfg dfg"], ["idk", "jjjjjjjj", "good good good"],
       ["My favourite football team won the league this year.", "n/a", "qwerty uiop asdf"]]
PASTED = ["Coffee brand selection is influenced by a combination of factors including flavor profile, roast level, ethical sourcing "
          "certifications, price point, and overall brand reputation within the specialty coffee market.",
          "My most recent coffee shop experience was characterized by efficient service, a welcoming ambiance, and a well-crafted "
          "beverage that met my expectations in terms of temperature, taste, and presentation.",
          "Increased purchase frequency could be driven by loyalty programs, personalized promotions, expanded product offerings, "
          "and enhanced convenience through mobile ordering and delivery services."]
FARM_ANSWERS = ["The roaster near my place sells a smooth medium roast that my whole family enjoys in the morning.",
                "Ordered a hazelnut latte at the mall cafe last Friday, sat outside and read for half an hour.",
                "A punch card that gives every sixth drink free would get me in the door twice as often."]

DESKTOP_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
]
MOBILE_UAS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
]
HEADLESS_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/130.0.0.0 Safari/537.36"

# ---------------------------------------------------------------- respondent types
# expected: flags the respondent must get; verdict: bot/human/pending; status checked/in_progress
TYPES = [
    # name, count, expected verdict, expected flags, description
    ("human_desktop", 12, "human", set(), "Real person on a desktop: curved mouse paths, natural typing, varied grid answers, 20-60 s per page"),
    ("human_mobile", 4, "human", set(), "Real person on a phone: touch taps, no mouse, typed answers"),
    ("human_keyboard", 1, "human", set(), "Real person using only the keyboard (no mouse)"),
    ("low_quality_text", 4, "human", {"Low-quality open ends"}, "Person typing gibberish, generic or off-topic answers"),
    ("paster", 3, "human", {"Pasted answers"}, "Person pasting long, AI-style answers into the open ends"),
    ("straight_liner", 3, "human", {"Straight-lining"}, "Person giving the same answer to every grid row"),
    ("speeder", 3, "human", {"Speeder", "Low-quality open ends"}, "Person clicking through every page in about 2 seconds, with one-word open ends"),
    ("near_straight", 2, "human", set(), "Person giving the same answer to 5 of 6 grid rows (the rule says all rows)"),
    ("bot_webdriver", 2, "bot", {"Bot-like behaviour"}, "Automation browser that reports navigator.webdriver"),
    ("bot_headless", 2, "bot", {"Bot-like behaviour"}, "Headless Chrome user agent"),
    ("bot_honeypot", 2, "bot", {"Bot-like behaviour"}, "Script that fills the hidden honeypot field"),
    ("bot_scripted", 2, "bot", {"Bot-like behaviour"}, "Clicks and key presses generated by script (isTrusted false)"),
    ("bot_no_input", 2, "bot", {"Bot-like behaviour", "Pasted answers"}, "Desktop pages answered with no mouse or keyboard at all; open ends set by script"),
    ("bot_untyped", 2, "bot", {"Bot-like behaviour", "Pasted answers"}, "Open ends filled by script with no input events"),
    ("bot_rhythm", 1, "bot", {"Bot-like behaviour"}, "Machine-regular typing (every 30 ms) and dead-straight mouse lines"),
    ("device_farm", 5, "human", {"Duplicate", "High fraud risk"}, "Five sessions from one device with copied answers (expected flags from the 2nd on)"),
    ("dropout", 2, "pending", set(), "Left after page 2: never reaches the final check"),
    ("bot_faketime", 2, "bot", {"Bot-like behaviour"}, "Behaves like a person but reports 20-45 s pages it never spent (finishes in seconds)"),
]


def _ai_checked(info):
    """yes / skipped (the AI check failed and the answer passed by default) / short."""
    details = info.get("analysis_details") or {}
    if details.get("error"):
        return "short" if "short" in str(details.get("error")) else "failed"
    failed = [k for k in ("gibberish", "copy_paste", "relevance", "generic", "quality")
              if "Analysis failed" in str((details.get(k) or {}).get("reason") or (details.get(k) or {}).get("reasoning") or "")]
    return "yes" if not failed else ("skipped" if len(failed) == 5 else "partly (" + ",".join(failed) + " skipped)")


def iso(t):
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class Respondent:
    def __init__(self, kind, n, farm_device=None):
        self.kind, self.n = kind, n
        self.uuid = str(uuid.uuid4())
        mobile = kind == "human_mobile"
        if kind == "bot_headless":
            ua = HEADLESS_UA
        elif mobile:
            ua = MOBILE_UAS[n % len(MOBILE_UAS)]
        else:
            ua = DESKTOP_UAS[n % len(DESKTOP_UAS)]
        self.ua = ua
        self.mobile = mobile
        if farm_device:
            self.device = farm_device
        else:
            w, h = ((390, 844) if mobile else rnd.choice([(1920, 1080), (1536, 864), (1440, 900), (2560, 1440), (1366, 768)]))
            self.device = {
                "screen_width": w, "screen_height": h,
                "viewport_width": w if mobile else w - rnd.randint(0, 40), "viewport_height": h - rnd.randint(80, 160),
                "timezone": rnd.choice(["America/Toronto", "America/Vancouver", "America/New_York", "Europe/London"]),
                "languages": rnd.choice(["en-CA,en", "en-US,en", "en-GB,en", "fr-CA,fr,en"]),
                "platform": "iPhone" if "iPhone" in ua else ("Linux armv8l" if mobile else rnd.choice(["Win32", "MacIntel"])),
                "cores": rnd.choice([4, 6, 8, 12, 16]), "memory": rnd.choice([4, 8, 16]),
                "canvas": "%08x" % rnd.getrandbits(32), "webgl": "%08x" % rnd.getrandbits(32),
            }
        self.events = []
        self.sent_text = []  # one dict per open-end answer, with the API's analysis
        self.session = None
        self.result = None
        self.t = None

    # ------------------------------------------------------------ event builders
    def ctx(self, element_id=None, element_type=None):
        d = self.device
        return {"page_url": PAGE_URL, "user_agent": self.ua, "screen_width": d["screen_width"], "screen_height": d["screen_height"],
                "viewport_width": d["viewport_width"], "viewport_height": d["viewport_height"], "survey_id": SURVEY,
                "respondent_id": self.uuid, "platform_id": "decipher", "element_id": element_id, "element_type": element_type}

    def ev(self, kind, extra=None, element_id=None, element_type=None):
        e = self.ctx(element_id, element_type)
        e["event_type"] = kind
        e["timestamp"] = iso(self.t)
        if extra:
            e.update(extra)
        self.events.append(e)

    def advance(self, ms):
        self.t += timedelta(milliseconds=ms)

    def mouse_path(self, steps, straight=False):
        x, y = rnd.randint(100, 600), rnd.randint(100, 500)
        tx, ty = rnd.randint(200, 1200), rnd.randint(150, 700)
        for i in range(steps):
            f = (i + 1) / steps
            if straight:
                nx, ny = x + (tx - x) * f, y + (ty - y) * f
            else:
                bend = math.sin(f * math.pi) * rnd.uniform(30, 90)
                nx = x + (tx - x) * f + bend + rnd.uniform(-4, 4)
                ny = y + (ty - y) * f - bend * 0.4 + rnd.uniform(-4, 4)
            self.advance(100 if straight else rnd.randint(100, 260))
            self.ev("mouse_move", {"x": int(nx), "y": int(ny)})

    def click(self, element_id, trusted=True, pointer="mouse"):
        self.advance(rnd.randint(150, 600))
        self.ev("mouse_click", {"button": 0, "x": rnd.randint(200, 900), "y": rnd.randint(200, 700), "trusted": trusted,
                                "pointer": pointer}, element_id, "input")

    def type_text(self, element_id, text, rhythm=None, trusted=True):
        self.ev("focus", {}, element_id, "textarea")
        for ch in text:
            self.advance(rhythm if rhythm else max(45, int(rnd.gauss(170, 70))))
            if ch == " " and not rhythm and rnd.random() < 0.15:
                self.advance(rnd.randint(300, 1500))  # thinking pause
            self.ev("keystroke", {"key": "char", "trusted": trusted}, element_id, "textarea")
        self.advance(rnd.randint(200, 800))
        self.ev("blur", {}, element_id, "textarea")


async def call(c, method, path, **kw):
    for attempt in range(8):
        t0 = time.perf_counter()
        r = await c.request(method, BASE + path, **kw)
        STATS["requests"] += 1
        STATS["latency"].append((path.split("?")[0].split("/")[-1] or path, time.perf_counter() - t0))
        if r.status_code == 429:
            STATS["429"] += 1
            await asyncio.sleep(min(60, 5 * (attempt + 1)))
            continue
        if r.status_code >= 400:
            STATS["errors"].append(f"{method} {path.split('?')[0]} -> {r.status_code} {r.text[:200]}")
        return r
    return r


async def play(c, R: Respondent, sem, start_after=0.0):
    await asyncio.sleep(start_after)  # spaced starts: 30 new sessions a minute per address
    async with sem:
        kind = R.kind
        human = not kind.startswith("bot_") and kind != "device_farm"
        speeder = kind == "speeder"
        n_pages = 2 if kind == "dropout" else len(PAGES)
        # Timeline: the survey happened over the last few minutes (the API takes client timestamps).
        # Real time: the respondent spends the page times it reports (the server checks).
        if kind == "device_farm":
            page_ms = [8000] * n_pages  # equal lengths, so farm sessions finish in start order
        elif kind == "bot_faketime":
            page_ms = [rnd.randint(20000, 45000) for _ in range(n_pages)]
        else:
            page_ms = [rnd.randint(1500, 2600) if speeder else rnd.randint(6000, 20000) for _ in range(n_pages)]
        R.t = datetime.now(timezone.utc)
        headers = {"User-Agent": R.ua, "Content-Type": "application/json"}

        r = await call(c, "POST", f"/detection/sessions?survey_id={SURVEY}&respondent_id={R.uuid}&platform_id=decipher", headers=headers)
        if r.status_code != 200:
            R.result = {"error": f"session {r.status_code}"}
            return
        R.session = sid = r.json()["session_id"]

        signals = {k: R.device[k] for k in ("timezone", "languages", "platform", "cores", "memory", "canvas", "webgl")}
        signals["webdriver"] = kind == "bot_webdriver"
        signals["touch_points"] = 5 if R.mobile else 0
        R.ev("page_load", signals)

        async def flush():
            if R.events:
                batch, R.events = R.events, []
                await call(c, "POST", f"/detection/sessions/{sid}/events", json=batch, headers=headers)

        grid_q = None
        bad = BAD[R.n % len(BAD)]
        for p in range(n_pages):
            page = PAGES[p]
            start = R.t
            if p:
                R.ev("page_load", signals)
            open_index = int(page[2]) if page.startswith("oe") else None
            qid = None
            if open_index is not None:
                el, question = OPEN[open_index]
                q = await call(c, "POST", "/text-analysis/questions", headers=headers, json={
                    "session_id": sid, "question_text": question, "question_type": "open_ended", "element_id": el,
                    "page_url": PAGE_URL, "page_title": "Coffee study"})
                qid = q.json().get("question_id")
            if page.startswith("grid"):
                q = await call(c, "POST", "/text-analysis/questions", headers=headers, json={
                    "session_id": sid, "question_text": "How much do you agree with each statement about coffee?",
                    "question_type": "grid", "page_url": PAGE_URL, "page_title": "Coffee study"})
                grid_q = q.json().get("question_id")

            # ---- behaviour on the page
            mouse = not R.mobile and kind not in ("human_keyboard", "bot_no_input", "bot_untyped")
            if kind == "bot_scripted":
                mouse = False
            if mouse and not speeder:
                R.mouse_path(rnd.randint(12, 25), straight=kind == "bot_rhythm")
                if human:
                    R.advance(200); R.ev("scroll", {"scroll_y": rnd.randint(100, 600), "scroll_x": 0})
            elif mouse:
                R.mouse_path(4)
            text = None
            pasted = typed = inputs = 0
            if open_index is not None:
                el = OPEN[open_index][0]
                if kind == "low_quality_text":
                    text = bad[open_index]
                elif kind == "paster":
                    text = PASTED[open_index]
                elif kind == "device_farm":
                    text = FARM_ANSWERS[open_index]
                elif kind in ("bot_untyped", "bot_no_input"):
                    text = GOOD[open_index][(R.n * 7 + 3) % len(GOOD[open_index])]
                elif speeder:
                    text = ["ok fine", "good", "cheaper"][open_index]
                else:
                    text = GOOD[open_index][(R.n + {"human_mobile": 5, "human_keyboard": 9, "straight_liner": 11,
                                                    "bot_webdriver": 2, "bot_headless": 4, "bot_honeypot": 6,
                                                    "bot_scripted": 8, "bot_rhythm": 10}.get(kind, 0)) % len(GOOD[open_index])]
                if kind == "paster":
                    if mouse:
                        R.click(el)
                    R.ev("keystroke", {"key": "Control", "trusted": True}, el, "textarea")
                    R.ev("keystroke", {"key": "char", "trusted": True}, el, "textarea")
                    pasted, typed, inputs = len(text), 0, 1
                elif kind in ("bot_untyped", "bot_no_input"):
                    pasted, typed, inputs = 0, 0, 0
                elif kind == "bot_scripted":
                    R.type_text(el, text, rhythm=None, trusted=False)
                    typed, inputs = len(text), len(text)
                else:
                    if mouse or R.mobile:
                        R.click(el, pointer="touch" if R.mobile else "mouse")
                    R.type_text(el, text, rhythm=30 if kind == "bot_rhythm" else (60 if speeder else None))
                    typed, inputs = len(text), len(text)
            # Closed answers
            values = []
            if page == "intro" or page.startswith("grid"):
                rows = 1 if page == "intro" else GRID_ROWS
                for row in range(rows):
                    if kind == "straight_liner":
                        v = 3
                    elif kind == "near_straight" and rows > 1:
                        v = 4 if row == 2 else 3
                    elif kind.startswith("bot_") or kind == "device_farm":
                        v = rnd.randint(1, 5)
                    else:
                        v = rnd.choice([2, 3, 4, 4, 5, 1, 3])
                        while values.count(str(v)) >= 3:  # people vary; never more than 3 alike here
                            v = rnd.randint(1, 5)
                    values.append(str(v))
                    if kind == "bot_scripted":
                        R.click(f"r{row}", trusted=False)
                    elif mouse:
                        R.mouse_path(rnd.randint(2, 4), straight=kind == "bot_rhythm")
                        R.click(f"r{row}")
                    elif R.mobile:
                        R.click(f"r{row}", pointer="touch")
                    elif kind == "human_keyboard":
                        R.advance(rnd.randint(400, 1200)); R.ev("keystroke", {"key": "ArrowDown", "trusted": True}, f"r{row}", "input")
                        R.advance(rnd.randint(200, 600)); R.ev("keystroke", {"key": "Tab", "trusted": True}, f"r{row}", "input")
            # Next button
            if kind == "bot_scripted":
                R.click("btn_continue", trusted=False)
            elif mouse:
                R.mouse_path(3); R.click("btn_continue")
            elif R.mobile:
                R.click("btn_continue", pointer="touch")
            elif kind == "human_keyboard":
                R.advance(300); R.ev("keystroke", {"key": "Enter", "trusted": True}, "btn_continue", "button")
            # Put the page end at its planned time.
            end = start + timedelta(milliseconds=page_ms[p])
            if R.t < end:
                R.t = end
            elapsed = int((R.t - start).total_seconds() * 1000)
            if kind != "bot_faketime":
                wait = (R.t - datetime.now(timezone.utc)).total_seconds()
                if wait > 0:
                    await asyncio.sleep(wait)
            else:
                R.t = max(R.t, datetime.now(timezone.utc))

            submit = R.ctx("qos-page:%d" % elapsed)
            submit.update({"event_type": "form_submit", "timestamp": iso(R.t)})
            if kind == "bot_honeypot":
                submit["honeypot"] = True
            if kind == "bot_untyped" and text and len(text) >= 20:
                submit["untyped_answers"] = 1
            R.events.append(submit)
            if page.startswith("grid") and len(values) >= 3:
                g = dict(submit); g["element_id"] = "qos-grid:" + ",".join(values)
                R.events.append(g)

            # Answers go out on blur/submit.
            if qid and text:
                body = {"session_id": sid, "question_id": qid, "response_text": text, "response_time_ms": elapsed,
                        "typed_chars": typed, "pasted_chars": pasted, "input_events": inputs}
                tr = await call(c, "POST", "/text-analysis/responses", headers=headers, json=body)
                info = tr.json() if tr.status_code == 200 else {"error": tr.status_code}
                R.sent_text.append({"question": OPEN[open_index][1], "answer": text, "typed": typed, "pasted": pasted,
                                    "inputs": inputs, "status": tr.status_code, "ai_checked": _ai_checked(info), **{k: info.get(k) for k in ("quality_score", "is_flagged", "flag_reasons")}})
            if page.startswith("grid") and grid_q:
                for v in values:
                    await call(c, "POST", "/text-analysis/responses", headers=headers, json={
                        "session_id": sid, "question_id": grid_q, "response_text": v, "response_time_ms": elapsed})
            await flush()

        if kind == "dropout":
            R.result = {"dropped_after_pages": n_pages}
            return
        # Final page: composite check (what fills QOS_FLAG / LQ_ variables).
        R.ev("page_load", signals)
        await flush()
        cr = await call(c, "POST", f"/detection/sessions/{sid}/composite-analyze", headers=headers)
        R.result = cr.json() if cr.status_code == 200 else {"error": cr.status_code, "text": cr.text[:300]}


async def burst_test(c):
    """35 new sessions from one address within a minute: the limit is 30 per minute per IP."""
    codes = []
    async def one(i):
        r = await c.post(f"{BASE}/detection/sessions?survey_id=PRESSURE_BURST&respondent_id=burst-{i:03d}&platform_id=decipher")
        codes.append(r.status_code)
    await asyncio.gather(*(one(i) for i in range(35)))
    return {"sent": 35, "ok": codes.count(200), "limited_429": codes.count(429), "other": [x for x in codes if x not in (200, 429)]}


async def main():
    respondents, farm = [], None
    for kind, count, *_ in TYPES:
        for n in range(count):
            if kind == "device_farm":
                if farm is None:
                    farm = Respondent(kind, n).device
                respondents.append(Respondent(kind, n, farm_device=farm))
            else:
                respondents.append(Respondent(kind, n))
    # Device farm members share one user agent too.
    for R in respondents:
        if R.kind == "device_farm":
            R.ua = DESKTOP_UAS[0]
    order = [R for R in respondents if R.kind != "device_farm"]
    rnd.shuffle(order)
    farm_members = [R for R in respondents if R.kind == "device_farm"]

    t0 = time.time()
    limits = httpx.Limits(max_connections=CONC * 2)
    async with httpx.AsyncClient(timeout=120, limits=limits) as c:
        print(f"survey {SURVEY}: {len(respondents)} respondents, {CONC} at a time -> {BASE}", flush=True)
        sem = asyncio.Semaphore(CONC)
        done = 0
        async def run(R, start_after=0.0):
            nonlocal done
            try:
                await play(c, R, sem, start_after)
            except Exception as e:  # keep going; report it
                R.result = {"error": repr(e)}
            done += 1
            if done % 5 == 0:
                print(f"  {done}/{len(respondents)} done ({time.time() - t0:.0f}s, 429s so far {STATS['429']})", flush=True)
        # Everyone at once with spaced starts; the farm's sessions start 15 s apart.
        await asyncio.gather(*(run(R, i * 2.2) for i, R in enumerate(order)),
                             *(run(R, 20 + i * 15) for i, R in enumerate(farm_members)))
        play_secs = time.time() - t0

        print("reading Live Quality results and CSV export...", flush=True)
        t1 = time.time(); res = await c.get(f"{BASE}/quality/results", params={"survey_id": SURVEY}); results_secs = time.time() - t1
        res.raise_for_status(); results = res.json()
        t1 = time.time(); exp = await c.get(f"{BASE}/quality/export", params={"survey_id": SURVEY}); export_secs = time.time() - t1
        exp.raise_for_status()
        rep = await c.get(f"{BASE}/quality/report", params={"survey_id": SURVEY})
        print("rate-limit burst test (separate survey PRESSURE_BURST)...", flush=True)
        burst = await burst_test(c)

    (OUT / f"quality-{SURVEY}.csv").write_bytes(exp.content)
    (OUT / "results.json").write_text(json.dumps(results, indent=1, default=str))
    (OUT / "report.json").write_text(json.dumps(rep.json() if rep.status_code == 200 else {"status": rep.status_code}, indent=1, default=str)[:2_000_000])

    # ---------------------------------------------------------------- score
    rows = {r["respondent_id"]: r for r in results.get("respondents", [])}
    exported = {r["respondent_id"]: r for r in csv.DictReader(io.StringIO(exp.content.decode("utf-8-sig")))}
    meta = {t[0]: t for t in TYPES}
    score_rows, answers = [], []
    farm_seen = 0
    for R in respondents:
        _, _, verdict, flags, desc = meta[R.kind]
        expected = set(flags)
        if R.kind == "device_farm":
            farm_seen += 1
            if farm_seen < 2:
                expected = set()  # the first session on a device is not a repeat
        row = rows.get(R.uuid, {})
        got = set(row.get("flags") or [])
        got_verdict = row.get("verdict")
        missing = sorted(expected - got)
        # The AI may also call pasted text copied (a low-quality reason); either is right.
        allowed = {"Low-quality open ends"} if R.kind == "paster" else set()
        extra = sorted(got - expected - allowed)
        ok_verdict = got_verdict == verdict
        if R.kind == "dropout":
            ok_verdict = got_verdict == "pending" and row.get("status") in ("in_progress", "dropped")
        passed = ok_verdict and not missing and not extra
        comp = R.result or {}
        score_rows.append({
            "uuid": R.uuid, "session_id": R.session, "respondent_type": R.kind, "what_it_does": desc,
            "expected_verdict": verdict, "verdict": got_verdict, "status": row.get("status"),
            "expected_flags": "; ".join(sorted(expected)), "flags": "; ".join(row.get("flags") or []),
            "missing_flags": "; ".join(missing), "unexpected_flags": "; ".join(extra), "pass": "PASS" if passed else "FAIL",
            "bot_score": row.get("confidence"), "bot_signals": "; ".join(row.get("bot_signals") or []),
            "fraud_score": row.get("fraud_score"), "seconds": row.get("seconds"), "pages": row.get("pages"),
            "text_quality": row.get("text_quality") if "text_quality" in row else (exported.get(R.uuid) or {}).get("text_quality"),
            "in_csv_export": "yes" if R.uuid in exported else "no",
            "final_check_flag": ("bot" if comp.get("is_bot") else "human") if "is_bot" in comp else comp.get("error", ""),
            "final_check_score": comp.get("composite_score"),
            "survey_variables": json.dumps(comp.get("survey_variables") or {}),
        })
        for a in R.sent_text:
            answers.append({"uuid": R.uuid, "respondent_type": R.kind, "question": a["question"], "answer": a["answer"],
                            "typed_chars": a["typed"], "pasted_chars": a["pasted"], "input_events": a["inputs"], "http": a["status"],
                            "quality_score": a.get("quality_score"), "flagged": a.get("is_flagged"),
                            "reasons": "; ".join(sorted((a.get("flag_reasons") or {}).keys())), "ai_checked": a["ai_checked"]})

    def write(name, rows_):
        with open(OUT / name, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows_[0].keys())); w.writeheader(); w.writerows(rows_)
    write("respondents_scored.csv", score_rows)
    write("open_end_answers.csv", answers)

    lat = {}
    for name, s in STATS["latency"]:
        lat.setdefault(name, []).append(s)
    summary = {
        "survey_id": SURVEY, "base": BASE, "respondents": len(respondents),
        "passed": sum(r["pass"] == "PASS" for r in score_rows), "failed": [f'{r["respondent_type"]} {r["uuid"]}: missing [{r["missing_flags"]}] extra [{r["unexpected_flags"]}] verdict {r["verdict"]}/{r["expected_verdict"]}' for r in score_rows if r["pass"] != "PASS"],
        "by_type": {k: f'{sum(1 for r in score_rows if r["respondent_type"] == k and r["pass"] == "PASS")}/{sum(1 for r in score_rows if r["respondent_type"] == k)}' for k in meta},
        "requests": STATS["requests"], "rate_limited_429": STATS["429"], "http_errors": STATS["errors"][:30],
        "play_seconds": round(play_secs, 1), "results_seconds": round(results_secs, 2), "export_seconds": round(export_secs, 2),
        "latency_p50_p95": {k: (round(sorted(v)[len(v) // 2], 3), round(sorted(v)[int(len(v) * 0.95)], 3), len(v)) for k, v in lat.items()},
        "totals": results.get("totals"), "flag_counts": results.get("flag_counts"), "text": results.get("text"),
        "csv_rows": len(exported), "csv_columns": list(next(iter(exported.values())).keys()) if exported else [],
        "open_ends": {"ai_checked": {v: sum(1 for a in answers if a["ai_checked"] == v) for v in sorted({a["ai_checked"] for a in answers})}, "sent": len(answers), "scored": sum(1 for a in answers if a["quality_score"] is not None), "flagged": sum(1 for a in answers if a["flagged"])},
        "burst": burst,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps(summary, indent=1, default=str))


asyncio.run(main())
