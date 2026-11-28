# Bot Detection Live

Bot and fraud detection for online surveys. A tracker added to the survey records how each respondent answers (typing, mouse and touch, timing, grids, open ends); the service judges each session as human or bot, checks open-end quality and fraud, writes the results back into the survey data, and shows them on a live dashboard.

This folder is self-contained: it has no dependency on Quant OS (Quant_Sys). It stays compatible with surveys Quant OS tracked (same `QOS_` variables; it recognises Quant OS tracking and replaces it instead of adding a second copy).

**Production**
- Dashboard: https://storage.googleapis.com/bot-detection-frontend-20251208/index.html (pages use addresses like `index.html#/quality`)
- Backend API: https://bot-backend-119522247395.northamerica-northeast2.run.app (docs at `/docs`, health at `/health`)
- Deployed 2026-11-26 from commits `cfc4499` (backend image) and `6244608` (dashboard); see [Deployment](#-deployment).
- Not yet deployed: the latest changes (final check following each survey's rules, `timeline_mismatch`, the combined behaviour score, fraud reweighting, the data-file merge fix, protection on signed upload) are in the code but not in production.
- Pressure test (production, 52 simulated respondents, 2026-11-27): 52/52 got the expected result and 150/150 open ends were checked. Files: `test_results/respondent_pressure_2026-11-27`.

## 🚀 Features

**For researchers**
- **Add tracking to a Decipher survey**: upload the survey XML, get it back with tracking, and upload it straight to Decipher (new survey, the one used last time, or an existing survey's path). Files Decipher would refuse are caught before anything is sent. See [Add tracking to a Decipher survey](#add-tracking-to-a-decipher-survey).
- **Live Quality**: one survey's live results under its own quality rules (bot threshold, decisive signals, speeders, straight-lining, open-end reasons, fraud), with charts, a respondent table, CSV export, and `LQ_` flags added to an SPSS, CSV or Excel data file. See [Live quality](#live-quality).
- **Results in the survey data**: 21 `QOS_` variables (verdict, scores, reasons) are written into each completed respondent's Decipher record, matched by Decipher's `uuid`.
- **Overview, Sessions and session details**: every survey's bot rate, starts and bots per day, the latest bots, and each session's verdict with the reasons behind it.
- **Open-end quality** (OpenAI GPT-4o-mini, one call per answer; an answer that cannot be checked is stored as not checked) and **Reports** (summary and detailed, CSV and PDF).

**Detection**
- Behaviour analysis (typing, mouse, timing, device; network is not implemented and carries no weight). The checks are combined so agreeing evidence adds up: score = 1 - product(1 - reliability x check score), with reliabilities keystroke 0.5, mouse 0.45, timing 0.35, device 0.4. Two strong checks reach the 0.7 bot threshold; one alone does not. Events the tracker sent twice are counted once, and a grid page counts as one page (the copy of the page submit carrying grid answers is not counted again).
- Seven decisive signals: automated browser, scripted input, no input, honeypot, open ends that appeared without typing, machine-exact typing or mouse timing (`robotic_timing`), and page times longer than the time the server saw (`timeline_mismatch`). One lifts the behaviour score to 0.85, two or more to 0.95.
- Bot or human is decided by behaviour alone, under the survey's quality rules (bot threshold and enabled signals); open-end quality and fraud are shown as their own flags and scores. The composite score (40% behaviour, 30% open-end quality, 30% fraud) is still calculated and reported. Fraud checks: IP reuse, device fingerprint (counts half when seen only on other networks, IPv4 /24 or IPv6 /48), copied answers (open ends of 20+ characters only; exact copies across the whole survey, near copies of 70%+ among the latest 2,000 answers), velocity, data-centre/VPN IPs (fraud score at least 0.75). The fraud score weights IP 0.25, device 0.25, copied answers 0.20, velocity 0.15; location is left out until there is an IP-to-country lookup, and the weights are renormalised over the rest.
- Grid analysis (straight-lining: the same answer on every row of a grid with at least 3 rows; patterns) and timing analysis (speeders, flatliners).
- **Bot rate** means the same on every page: sessions judged bots out of sessions checked, each session counted once.

**Operations**
- **Settings page** that really saves: Decipher, Qualtrics and OpenAI keys, tracker address, signing secret and bot threshold; saved values override the environment, are encrypted, and apply without a restart. Saving needs `ADMIN_TOKEN`. See [Settings page](#settings-page).
- Hierarchical API (survey, platform, respondent, session), webhooks for Qualtrics and Decipher, Prometheus metrics, client SDKs.

## 🏗️ Architecture

See [architecture.md](architecture.md) for details.

```
Survey (Decipher) -- tracker script --> Backend API (FastAPI, Cloud Run) --> PostgreSQL (Cloud SQL)
       ^                                   |      |
       +---- QOS_ results on last page ----+      +--> OpenAI (open-end scoring)
Dashboard (React, Cloud Storage) <---- REST API ---+
```

## 📁 Project Structure

```
bot_detection_live/
├── backend/                      # FastAPI service
│   ├── main.py                   # App, CORS, startup (creates tables, loads saved settings)
│   ├── app/
│   │   ├── assets/live_quality_tracker.js   # Tracker added to Decipher surveys
│   │   ├── controllers/          # API routes (detection, dashboard, reports, surveys,
│   │   │                         #  fraud, text analysis, tracking, quality, settings)
│   │   ├── models/               # SQLAlchemy models (sessions, events, results, fraud,
│   │   │                         #  tracked_surveys, survey_quality_rules, app_settings)
│   │   ├── services/             # Detection engine, reports, Decipher tracking/upload,
│   │   │                         #  live quality, quality rules, data-file merge, runtime settings
│   │   └── utils/
│   ├── tests/                    # pytest suite; fixtures/ has example Decipher surveys
│   ├── requirements.txt, requirements-test.txt
│   ├── .gcloudignore, .dockerignore   # keep .env, venvs and test data out of builds
│   └── Dockerfile
├── frontend/                     # React + Vite dashboard
│   └── src/
│       ├── App.jsx               # Routes (hash addresses in production)
│       ├── components/layout/AppShell.jsx   # Sidebar and phone menu
│       ├── components/ui/        # Shared page header, cards, buttons, badges, states
│       ├── components/quality/   # Live Quality parts, rules editor, data-file merge
│       ├── components/           # Overview, LiveQuality, SessionList, SessionDetails,
│       │                         #  SurveyTracking, Settings, Integrations, Reports, ...
│       └── services/apiService.js
├── client-sdk/                   # Python and JavaScript clients
├── API.md, API_V2.md             # API reference
├── architecture.md, database.md  # Design and schema
├── BOT_DETECTION_METHODOLOGY.md, bot_detection_flow.md
├── decipher_guide.md, decipher_simple_guide.md
├── SELECTIVE_DEPLOYMENT_GUIDE.md, rollback-procedures.md
└── planning.md, prd.md, task.md
```

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy (async), PostgreSQL (SQLite for tests and local previews), Pydantic, OpenAI, pandas/pyreadstat/openpyxl (data files), cryptography (encrypted settings)
- **Frontend**: React 18, Vite, Tailwind CSS, React Router, Recharts, Lucide icons
- **Infrastructure**: Google Cloud Run, Cloud SQL, Secret Manager, Cloud Build, Artifact Registry, Cloud Storage

## 🚀 Quick Start (local)

Prerequisites: Python 3.11+, Node.js 18+.

```bash
git clone https://github.com/halderavik/bot_detection_live.git
cd bot_detection_live

# Backend
cd backend
python -m venv .venv && .venv/Scripts/activate   # or: source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
cp .env.example .env                             # then edit
# Local database without Postgres:
DATABASE_URL=sqlite+aiosqlite:///./local.db SECRET_KEY=dev ADMIN_TOKEN=dev uvicorn main:app --port 8000

# Frontend (second terminal)
cd frontend
npm install
VITE_API_BASE_URL=http://localhost:8000/api/v1 npx vite --port 3000
```

Open http://localhost:3000 (local development uses normal paths such as `/quality`). Docker Compose (`docker-compose.yml`) is also available.

## Add tracking to a Decipher survey

Open **Add tracking** in the dashboard (`/tracking`; in production `index.html#/tracking`), choose the survey's XML file (exported from Decipher's XML editor, `.xml` or `.txt` holding the XML, up to 5 MB), pick the options, and click **Add tracking**. You get:

- a summary of what was added, with the survey id, question and page counts, and any warnings;
- **Download** for the tracked XML (`<name>_tracked.xml`): in Decipher, replace the survey's XML with it and save;
- **Upload to Decipher** (when `DECIPHER_API_KEY` is set): sends the tracked XML straight to Decipher (see below);
- **Open the survey dashboard**, the survey's page (`/surveys/<survey id>`) where its responses appear while people take it.

What goes into the file (nothing else changes):

- the tracker script (`backend/app/assets/live_quality_tracker.js`) as a `respview.client.js` style with `mode="after"`, so it runs on every page alongside the survey's own scripts. It sends behaviour (keys, mouse, scrolling, focus), open-end text, page timing, and grid answers to this API, and runs the composite check on the last page. It never blocks the survey: every call times out (the last page waits at most 3 s for the final check, 2.5 s for the in-survey check, 1.5 s for answers), and when the API is slow or unreachable the respondent carries on. The final check saves timing and grid results in one batch; in production it took a median 1.7 s under load and 1.1 s idle;
- the respondent id: the tracker reports each respondent under Decipher's own `uuid`, which Decipher writes into the script as it renders the page (`${uuid}`, the only Decipher expression in the script). The same value is the `uuid` variable in Decipher's SPSS, Excel and CSV exports, so a respondent's row in the Decipher data and its results here share one id. In a preview where Decipher does not render it, the tracker makes its own id;
- a hidden results page at the end with the quality variables below, which the tracker fills so each respondent's results are in the Decipher data (SPSS, Excel, CSV) too;
- **Show a privacy notice** (on by default): a short notice at the top of the first page (`QOS_privacy`). The wording can be changed; `$` and square brackets are refused because Decipher would read them as code;
- **End the survey on a clear bot signal** (off by default): a hidden `QOS_EARLY` question on the page you choose and a termination (`QOS_bot_term`) after it. Only the decisive signals you tick end the survey (automated browser, scripted clicks, no mouse or keyboard use, honeypot, open ends that appeared without typing, machine-exact timing, page times longer than the server saw); a score on its own never does. The check only goes on a page break every respondent reaches, never inside a loop or a conditional block; when there is no such page, it is left out and the summary says so.

**Quality variables in the data export.** The tracker fills these on the last page, from the composite check. Text questions come through as strings, number questions as numeric variables. They are filled for respondents who reach the end of the survey; terminates and drop-outs have them blank (their results are still here under the same `uuid`). A number is blank when its check had nothing to work on (for example `QOS_STRAIGHTLINE` in a survey with no grids).

| Variable | Type | Meaning |
|---|---|---|
| `QOS_RESPONDENT` | text | Respondent id here; Decipher's `uuid` |
| `QOS_SESSION` | text | Session id here (opens the respondent's details) |
| `QOS_FLAG` | text | `bot`, `human`, or `unknown` (service not reached); bot or human follows the survey's quality rules, as on Live Quality |
| `QOS_SCORE` | text | Composite score 0-1 (40% behaviour, 30% open-end quality, 30% fraud); shown for reference, the verdict comes from behaviour |
| `QOS_RISK` | text | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `QOS_STATUS` | 1-3 | 1 human, 2 suspect (a reason below, or medium risk or worse), 3 bot |
| `QOS_BEHAV` | 0-100 | Behaviour bot score; higher is worse |
| `QOS_OES` | 0-100 | Open-ended answer quality; **higher is better** |
| `QOS_FRAUD` | 0-100 | Fraud score (IP, device, duplicates, velocity; location is left out until there is an IP-to-country lookup); higher is worse |
| `QOS_DUP` | 0/1 | Duplicate: same device, repeated IP, or copied answers |
| `QOS_DUP_SCORE` | 0-100 | Highest of the device, IP and copied-answer risks. The copied-answer risk is 0 under 70% similarity, 60 from 70%, 80 from 85%, 100 from 95% (not the raw similarity) |
| `QOS_IP_RISK` | 0-100 | IP address reuse risk |
| `QOS_DEVICE_RISK` | 0-100 | Same device on other sessions of this survey (counts half when seen only on other networks) |
| `QOS_GEO_RISK` | 0-100 | Same respondent seen from different countries within an hour |
| `QOS_VELOCITY` | 0-100 | Many surveys started in a short time |
| `QOS_DATACENTER` | 0/1 | Data centre, VPN or proxy IP address |
| `QOS_SPEEDER` | count | Pages answered too fast: pages faster than the survey's speeder seconds-per-page rule |
| `QOS_STRAIGHTLINE` | count | Straight-lined grid questions |
| `QOS_FLAGCOUNT` | count | Number of reason codes |
| `QOS_REASON` | code | Main reason (the most severe), 0 for none |
| `QOS_REASONS` | text | Every reason code, comma-separated, for example `10,11,22` |
| `QOS_EARLY` | text | Only with **End the survey on a clear bot signal**: `bot` or `human` at the mid-survey check |

Reason codes (`backend/app/services/quality_variables.py`), most severe first: 1 automated or headless browser, 2 scripted clicks and key presses, 3 pages answered with no mouse or keyboard use, 4 honeypot filled in, 5 open ends that appeared without typing, 7 typing or mouse movement with machine-exact timing, 8 page times longer than the time the server saw, 6 bot-like behaviour score, 10 data centre / VPN / proxy IP, 11 same device reused, 12 same IP reused, 13 answers copied from another respondent, 14 many surveys in a short time, 15 same respondent seen from different countries within an hour, 20 low-quality open ends, 21 straight-lined grids, 22 speeding (pages average under the survey's seconds-per-page rule). `QOS_REASONS` and `QOS_FLAG` follow the survey's quality rules: only enabled bot signals become reason codes, 10 only when data-centre flagging is on, and 20 only for text reasons the rules count.

The two newer signals: **machine-exact timing** (7) is printable-key typing whose gaps vary by under 3 ms in at least 3 separate stretches of 8+ keys (a stretch ends at a field change or a 2 s pause; holding Backspace never triggers it), or at least 3 ruler-straight runs of equal mouse steps (4+ points, within 1.5 px) covering at least 40% of 30+ mouse points. **Page times longer than the server saw** (8) is when the page times the browser reports add up to 60+ s and exceed the time the server observed (session creation to the last event received) by more than 30 s or 25% of the reported time, whichever is larger. Page times are measured in the browser and could be made up; the server's own arrival times cannot. A survey that saved its rules before a signal existed gets that signal switched on; signals it switched off stay off.

The honeypot is an off-screen text box labelled "Leave this empty", with no name (so it is never sent to Decipher), `tabIndex` -1 and `aria-hidden`.

A survey tracked before these variables existed keeps working; upload it again to add them. If you import the XML in Decipher yourself instead of using **Upload to Decipher**, and the survey has saved data layouts, add the `QOS_` variables to the layout you export with (or export with all variables).

**Survey id.** Responses are grouped under the survey id. By default it is the survey's title (`alt`), for example `Coffee Machine Study`; enter your own id to override it. Each upload creates or updates the survey's record (`tracked_surveys` table).

**Upload to Decipher.** With `DECIPHER_API_KEY` set on the service (your Decipher REST API key, with `DECIPHER_API_BASE` and `DECIPHER_COMPANY`), the result has an **Upload to Decipher** panel. Choose where the file goes:

- **Create a new Decipher survey**, named after the survey id (the default the first time);
- **Update the survey uploaded last time**: the Decipher path is remembered per survey id, so later uploads replace that survey's XML instead of creating another survey;
- **Replace the XML of an existing survey**: paste its path (`selfserve/53b/240101`) or its link.

Decipher checks the file before saving it (`validate=true`) and never replaces the XML of a live survey (`overwriteLive=false`). When Decipher refuses the file, its messages are shown; if a new survey was already created, it is remembered, so uploading again updates it instead of creating another. Only XML that carries tracking for that survey id is sent. After the upload, the quality variables are added to each of the survey's saved data layouts (`layouts.json`) that lacks them: a saved layout lists its export columns one by one, so without this an SPSS or Excel export using that layout would leave them out. A survey without saved layouts is left alone; if the layouts cannot be updated, the upload still succeeds and says so. The API key goes only to Decipher, as the `x-apikey` header, and is removed from any error text. Without the key, the panel says how to set it up and the download still works.

**Uploading again.** A file that already has tracking (from this service, or from another survey builder that writes the same `QOS_*` pieces, such as Quant OS) is not tracked twice: the old tracking is taken out and added again with the current options, and the file's survey id is kept unless you enter a different one. Uploading the same file with the same options gives the same file back.

**Settings Decipher refuses** are caught before anything is sent: a survey with no `compat` (Decipher reads it as 0), a `compat` below 143 (retired), or `compat` 151 and above without `delphi="1"`. **Add tracking** still adds tracking but warns ("Decipher will refuse this file: ..."), and **Upload to Decipher** stops with the reason without contacting Decipher, so no empty survey is left in the Decipher account. XML exported from Decipher always passes.

**What is refused**, with the reason: files that are not a `<survey>` XML, XML that is not well-formed or not UTF-8, files with a DOCTYPE, and surveys that already use `QOS_` labels of their own.

**Signing.** With `TRACKING_TOKEN_SECRET` set, the tracker carries an HMAC token signed for its survey id, and a survey that requires tokens refuses sessions without it, so nobody can add fake sessions under its name. A survey starts requiring tokens as soon as a signed tracked file is uploaded to Decipher successfully through **Upload to Decipher**, or otherwise when its first signed session arrives. Making the tracked file alone does not protect it, because the live survey may still run an older unsigned tracker. The token stops outsiders who never saw the survey; anyone who opens the survey page can read it. Signing is optional: without the secret, tracking works the same, just unsigned, and nothing warns about it. Production currently has no `TRACKING_TOKEN_SECRET`, so tracking there is unsigned.

**Which API the tracker calls.** Set `TRACKER_API_BASE` to the service's public URL, for example `https://bot-backend-<id>.run.app/api/v1`. Without it, the upload uses the address the request came in on. It must be `https://` (Decipher pages are https); plain `http://` is only allowed for `localhost`, and the summary warns that such a file only works on your own computer.

API (used by the screen; also usable directly):

JSON with the tracked `xml`, what was added, warnings, and `dashboard_path`:

```bash
curl -F "file=@coffee_machine_study.xml" -F "terminate=true" -F "after_page=2" -F "signals=automation,honeypot" -F "privacy_notice=true" "http://localhost:8000/api/v1/tracking/decipher"
```

The tracked file itself:

```bash
curl -F "file=@coffee_machine_study.xml" -o coffee_machine_study_tracked.xml "http://localhost:8000/api/v1/tracking/decipher?format=xml"
```

`GET /api/v1/tracking/decipher/options` lists the bot signals, the default privacy wording, whether tracking is signed, and whether Decipher upload is set up.

`POST /api/v1/tracking/decipher/upload` with JSON `{"xml": ..., "survey_id": ..., "survey_path": null, "create_new": false}` sends tracked XML to Decipher and returns `survey_path` and `survey_url`.

Tests: `backend/tests/test_decipher_tracking.py` (injection: plain survey, already-tracked survey, loops and blocks, invalid XML) and `backend/tests/test_tracking_upload_endpoint.py` (the endpoint and a signed session landing in the survey), `backend/tests/test_decipher_upload.py` (Decipher upload against a mocked Decipher API), and `backend/tests/test_quality_variables.py` (the quality variables and their hidden questions). `backend/tests/fixtures/espresso_machine_tracker.xml` is a made-up survey with a loop and a conditional block to try the screen with; it has Decipher's current survey settings (compat 155, `delphi="1"`) and was accepted by Decipher. `backend/tests/fixtures/coffee_demo_survey.xml` is a small, complete demo survey (screener, rating grid, two open ends) that has been run end to end: tracked, uploaded to Decipher, taken as a respondent, and its results seen on Live Quality and in the `QOS_` columns of Decipher's data.

From `backend/` (needs `aiosqlite` from `requirements-test.txt`):

```bash
SECRET_KEY=test python -m pytest tests/test_decipher_tracking.py tests/test_tracking_upload_endpoint.py tests/test_decipher_upload.py
```

## Live quality

Open **Live Quality** in the dashboard (`/quality`, or `/quality?survey=<survey id>`). The left list shows surveys that had tracking added through **Add tracking** (switch to **All surveys** for surveys sending data through other integrations). For the chosen survey you get, refreshed every 8 seconds while the tab is visible (Pause stops it):

- tiles for started, checked, flagged, bot-like, low-quality text, straight-liners, speeders and duplicates;
- starts over time (clean and flagged, by hour or by day), open-end quality as a histogram, and the number of respondents with each flag (click a bar to filter the table);
- the respondent table: status, text quality, time, flags; click a row for the reasons (behaviour, fraud signals, grid, timing, each flagged open end) and a link to the session;
- **Export CSV**: one row per respondent with the verdict, scores and flags, including `text_unchecked` (open ends the AI check could not score).

In the results payload, `totals.respondents` counts people (sessions sharing a respondent id, the Decipher `uuid`, count once) and `totals.sessions` counts sessions; each row has `other_sessions` (other sessions with the same respondent id) and `text_unchecked`, and `text.unchecked` is the total of open ends not checked.

**Quality rules** are saved per survey id (`survey_quality_rules` table, created at startup) and start on the recommended defaults. They decide:

| Rule | Default | Meaning |
|---|---|---|
| Bot score threshold | 0.7 | Behaviour score (before decisive signals) at which a respondent is a bot |
| Signals that always mean bot | all seven | Automated browser, scripted input, no input, honeypot, untyped open ends, machine-exact timing, page times longer than the server saw |
| Speeder: seconds per page | 3.5 | Average page time below this is a speeder (from the tracker's page times) |
| Speeder: share of median | 0.5 | Also a speeder under this share of the median total time, once 5 respondents are checked (0 turns it off) |
| Straight-lining: minimum grid rows | 3 | Same answer on every row of a grid this size or larger (applied when the tracker sent grid answers) |
| Low-quality reasons | all five | Gibberish, generic, off-topic, copied, low effort |
| Flag pasted answers | on | Open ends that were mostly pasted or appeared without typing |
| High fraud risk threshold | 0.7 | Fraud score at which a respondent is high risk |
| Flag duplicates / data-centre IPs | on / on | |

Rules apply on every read, so the dashboard, the CSV export and the `LQ_` variables follow them as soon as they are saved. They don't change what the service stores. The final check on the last page also uses the survey's rules (bot threshold, enabled signals, data-centre flag, counted text reasons, speeder seconds per page), so the `QOS_*` values written into the Decipher data agree with Live Quality at that moment; values already in Decipher do not change when the rules are edited later. Ending the survey on a bot signal and the privacy notice are chosen on **Add tracking**.

**Add flags to a data file.** Upload the survey's Decipher export (SPSS `.sav`, `.csv` or `.xlsx`, up to 50 MB) and you get the same file back as `<name>_quality.<ext>` with these variables added at the end. Records match on `QOS_SESSION`, then `QOS_RESPONDENT`, then Decipher's `uuid` (the tracker reports respondents under it), so exports without the `QOS_` columns still match. When a `uuid` has several sessions (the respondent reopened the survey), the checked session is used first, then the latest.

| Variable | Meaning |
|---|---|
| `LQ_MATCHED` | 1 when the record was found in the live quality results |
| `LQ_STATUS` | 1 checked, 2 in progress, 3 dropped or ended early |
| `LQ_VERDICT` | 1 human, 2 bot, 3 not checked yet (under the survey's rules) |
| `LQ_BOT_SCORE`, `LQ_BOT_RISK`, `LQ_BOT_SIGNALS` | Behaviour score 0-1, its band (1 low, 2 medium, 3 high), decisive signals that fired |
| `LQ_SECONDS`, `LQ_PAGES`, `LQ_SEC_PER_PAGE` | Time on tracked pages |
| `LQ_TEXT_QUALITY` | Average open-end quality 0-100 |
| `LQ_FRAUD_SCORE`, `LQ_FRAUD_RISK` | Fraud score 0-1 and its band |
| `LQ_F_BOT`, `LQ_F_TEXT`, `LQ_F_PASTED`, `LQ_F_STRAIGHT`, `LQ_F_SPEEDER`, `LQ_F_FLATLINE`, `LQ_F_DUPLICATE`, `LQ_F_FRAUD`, `LQ_F_DATACENTRE` | One 0/1 variable per flag |
| `LQ_NFLAGS`, `LQ_FLAGS` | Number of flags, and all flags as text |

In SPSS files the `LQ_` variables get variable and value labels, and existing variables keep theirs. A file that already has `LQ_` variables gets them replaced, so uploading again after changing the rules refreshes them. CSV and Excel cells are read as text, so ids and codes such as leading zeros come back unchanged.

API (used by the screen; also usable directly; the survey id goes in the query string):

```http
GET    /api/v1/quality/surveys                  # surveys, tracked ones first
GET    /api/v1/quality/results?survey_id=...    # dashboard payload under the survey's rules
GET    /api/v1/quality/export?survey_id=...     # CSV, one row per respondent
GET    /api/v1/quality/rules?survey_id=...      # rules, defaults, what changed, labels
PUT    /api/v1/quality/rules?survey_id=...      # save rules (JSON body: the full rules)
DELETE /api/v1/quality/rules?survey_id=...      # back to the defaults
POST   /api/v1/quality/merge?survey_id=...      # multipart "file"; returns the file, report in X-Quality-Report
```

Tests: `backend/tests/test_live_quality.py` (rows, totals, rules, trend, CSV), `backend/tests/test_quality_merge.py` (matching, CSV, Excel and SPSS round trips), and `backend/tests/test_live_quality_endpoints.py` (the endpoints against SQLite with sessions sent through the API). The data file needs `pandas`, `pyreadstat` and `openpyxl` (in `requirements.txt`).

## Using the dashboard

The dashboard has a left sidebar (a menu button on phones), grouped by task:

- **Monitor**: **Overview** (home: sessions, checks and bots over the last 7 days, every survey with its bot rate, starts and bots per day, the latest bots), **Live Quality** (one survey's live results under its own rules), **Sessions** (every session with its latest verdict; filter by verdict, risk, platform or id; filters stay in the address so a view can be bookmarked).
- **Analyse**: **Open-end quality** and **Reports**.
- **Set up**: **Add tracking** (Decipher XML), **Manual setup** (step-by-step instructions and generated code for Decipher, Qualtrics, other survey platforms, your own web pages and the API), **Integrations** (the ways to connect, and which platform keys are set), **Settings**.
- **Developers**: **Quick start** and **API playground**.

The old `/dashboard` and `/surveys` addresses open the Overview. In production every address is behind `index.html#` (for example `index.html#/sessions?verdict=bot`), because the dashboard is a static page in a storage bucket. Clicking a session opens its page: the verdict and the decisive signals behind it first, then behaviour scores, the session facts, fraud, open ends, grids and timing, with the raw event log and analysis output folded away at the bottom.

**Bot rate** means the same everywhere: sessions judged bots out of sessions that were checked (analysed). A session analysed more than once counts once.

## Settings page

**Settings** shows the keys and options the service uses and where each value comes from (saved here, the environment, or not set):

| Setting | Environment variable |
|---|---|
| Decipher API key, API address, company | `DECIPHER_API_KEY`, `DECIPHER_API_BASE`, `DECIPHER_COMPANY` |
| Qualtrics API token | `QUALTRICS_API_TOKEN` |
| OpenAI API key and model (open-end scoring) | `OPENAI_API_KEY`, `OPENAI_MODEL` |
| Tracker API address, tracking signing secret | `TRACKER_API_BASE`, `TRACKING_TOKEN_SECRET` |
| Bot threshold (verdict stored with each new analysis) | `DETECTION_THRESHOLD` |

A value saved on the page overrides the environment variable and applies at once on the instance that saved it; every other instance re-reads saved values every 30 seconds. **Remove saved value** goes back to the environment. Saved values live in the `app_settings` table (created at startup); keys and secrets are encrypted with a key derived from `SECRET_KEY` and are never sent back to the browser, so the page only shows whether they are set. If `SECRET_KEY` changes, saved secrets can no longer be read and the environment values are used (the log says so).

Changing settings needs `ADMIN_TOKEN` (environment only; it can't be set from the page). Without it the page is read-only. With it, unlock the page with the token; it is kept for that browser tab only. The API: `GET /api/v1/settings`, `PUT /api/v1/settings` with header `X-Admin-Token` and body `{"changes": {"KEY": "value" | null}}`.

Per-survey rules (what counts as a bot, speeder, poor answer or fraud for one survey) stay on **Live Quality**.

Tests: `backend/tests/test_runtime_settings.py` (admin token, encryption at rest, live apply, going back to the environment, refused values) and `backend/tests/test_dashboard_numbers.py` (the same bot rate on every page, session verdicts and filters).

## 📚 Documentation

- [architecture.md](architecture.md): system design and data flow
- [API.md](API.md) and [API_V2.md](API_V2.md): API reference
- [database.md](database.md): schema
- [BOT_DETECTION_METHODOLOGY.md](BOT_DETECTION_METHODOLOGY.md) and [bot_detection_flow.md](bot_detection_flow.md): how detection and judging work
- [decipher_guide.md](decipher_guide.md) and [decipher_simple_guide.md](decipher_simple_guide.md): adding tracking to Decipher surveys
- [SELECTIVE_DEPLOYMENT_GUIDE.md](SELECTIVE_DEPLOYMENT_GUIDE.md) and [rollback-procedures.md](rollback-procedures.md): deploying and rolling back
- [planning.md](planning.md), [prd.md](prd.md), [task.md](task.md): plans, requirements, progress

### API overview

All paths are under `/api/v1` unless noted. Full details in [API.md](API.md).

```http
# Detection (used by the tracker)
POST /detection/sessions
POST /detection/sessions/{session_id}/events
POST /detection/sessions/{session_id}/analyze
POST /detection/sessions/{session_id}/composite-analyze
GET  /detection/sessions/{session_id}/status

# Dashboard
GET  /dashboard/overview?days=7                 # sessions, detections (checked, bots_detected, bot_rate)
GET  /dashboard/sessions                        # latest verdict per session; filters: is_bot, risk_level (incl. unknown), platform, survey_id, search
GET  /dashboard/sessions/{session_id}/details
GET  /dashboard/analytics/trends?days=14        # per day: sessions, checked, bots

# Decipher XML tracking
POST /tracking/decipher                         # survey XML in, tracked XML out
POST /tracking/decipher/upload                  # send tracked XML to Decipher
GET  /tracking/decipher/options
GET  /tracking/decipher/snippet?survey_id=     # the two XML blocks to paste by hand
POST /tracking/decipher/check                  # check an XML first: every problem explained, with how to fix it
POST /tracking/decipher/fix                    # Fix with AI (optional instructions); returns the fixed XML and a new check
GET  /tracking/script.js?survey_id=&platform=  # tracker file for Qualtrics or any website (platform=qualtrics|web)

# Live quality (survey id in the query string)
GET  /quality/surveys
GET  /quality/results?survey_id=
GET  /quality/export?survey_id=
GET|PUT|DELETE /quality/rules?survey_id=
POST /quality/merge?survey_id=                  # data file in, same file with LQ_ variables out

# Settings (PUT and POST /check need header X-Admin-Token)
GET  /settings
POST /settings/check
PUT  /settings

# Surveys (hierarchical), fraud, text analysis, reports, integrations
GET  /surveys, /surveys/{survey_id}, .../platforms/{platform_id}/respondents/...
GET  /fraud/sessions/{session_id}, /fraud/dashboard/summary, ...
POST /text-analysis/questions, /text-analysis/responses; GET /text-analysis/dashboard/summary, ...
GET  /reports/surveys, /reports/summary/{survey_id}, /reports/detailed/{survey_id}[/csv]
POST /integrations/webhooks/qualtrics, /integrations/webhooks/decipher; GET /integrations/status

# Health (no /api/v1 prefix)
GET  /health, /metrics
```

### Example Usage

#### 1. Create a Session
```bash
# Local
curl -X POST "http://localhost:8000/api/v1/detection/sessions" \
  -H "Content-Type: application/json"

# Production
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions" \
  -H "Content-Type: application/json"
```

#### 2. Send Events
```bash
# Local
curl -X POST "http://localhost:8000/api/v1/detection/sessions/{session_id}/events" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "event_type": "keystroke",
      "timestamp": "2024-01-01T12:00:00Z",
      "key": "a",
      "element_id": "input-1"
    }
  ]'

# Production
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/{session_id}/events" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "event_type": "keystroke",
      "timestamp": "2024-01-01T12:00:00Z",
      "key": "a",
      "element_id": "input-1"
    }
  ]'
```

#### 3. Check if Session is Ready for Analysis
```bash
# Local
curl -X GET "http://localhost:8000/api/v1/detection/sessions/{session_id}/ready-for-analysis"

# Production
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/{session_id}/ready-for-analysis"
```

#### 4. Analyze Session
```bash
# Local
curl -X POST "http://localhost:8000/api/v1/detection/sessions/{session_id}/analyze"

# Production
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/{session_id}/analyze"
```

#### 5. Text Quality Analysis
```bash
# Capture a survey question
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/questions" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "question_text": "What is your favorite color?",
    "question_type": "open_ended",
    "element_id": "color-input"
  }'

# Analyze a response
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/responses" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "question_id": "question-id",
    "response_text": "My favorite color is blue because it reminds me of the ocean.",
    "response_time_ms": 2500
  }'

# Get text quality summary
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/sessions/{session_id}/summary"

# Composite analysis (behavioral + text quality)
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/{session_id}/composite-analyze"

# Hierarchical text analysis endpoints (V2)
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/text-analysis/summary"
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/text-analysis/summary"
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/text-analysis/summary"
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/text-analysis"
```

#### 6. Fraud Detection Analysis
```bash
# Get fraud summary for a survey
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/fraud/summary"

# Get fraud summary for a platform
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/fraud/summary"

# Get fraud summary for a respondent
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/fraud/summary"

# Get fraud details for a session
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/fraud"

# Trigger fraud analysis for a session
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/fraud/analyze/{session_id}"

# Get fraud dashboard summary
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/fraud/dashboard/summary?days=7"

# Get duplicate sessions
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/fraud/dashboard/duplicates?limit=50"
```

#### 7. Generate Reports
```bash
# Get available surveys
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/reports/surveys"

# Generate summary report
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/reports/summary/SURVEY_001"

# Generate detailed report
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/reports/detailed/SURVEY_001"

# Download CSV report
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/reports/detailed/SURVEY_001/csv" \
  -o survey_report.csv

# Get text analysis dashboard summary
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/dashboard/summary?days=7"

# Get respondent-level text analysis
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/dashboard/respondents?days=7&limit=10"
```

## 🔧 Configuration

### Backend environment (`backend/.env`, or Cloud Run variables and secrets)

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/bot_detection
SECRET_KEY=change-me                 # also derives the key that encrypts saved secrets
ADMIN_TOKEN=a-long-random-token      # lets the Settings page save; unset = read-only (env only)
ALLOWED_ORIGINS=["http://localhost:3000"]

# Can also be set on the Settings page (saved values override these)
DECIPHER_API_KEY=
DECIPHER_API_BASE=https://selfserve.decipherinc.com/api/v1
DECIPHER_COMPANY=self
QUALTRICS_API_TOKEN=
OPENAI_API_KEY=                      # without it, open ends are stored as not checked (no score, not flagged)
OPENAI_MODEL=gpt-4o-mini
TRACKER_API_BASE=                    # public https address the tracker calls, ending in /api/v1
TRACKING_TOKEN_SECRET=               # optional: signs trackers
DETECTION_THRESHOLD=0.7              # bot probability for the stored verdict

# Environment only
OPENAI_REQUESTS_PER_MINUTE=300       # OpenAI calls per minute, per server instance
OPENAI_RATE_WAIT_SECONDS=20          # how long an answer waits for a free slot before it is stored as not checked
DB_POOL_SIZE=4                       # PostgreSQL connections kept open per server (0 = a new one per request)
DB_MAX_OVERFLOW=4                    # extra connections a server may open in a burst (keep size + overflow x max servers under the database's limit)
```

**Open-end check.** One OpenAI call per answer covers all five checks (gibberish, copied, relevance, generic, quality), each judged against the question. When the per-minute limit is reached, an answer waits up to `OPENAI_RATE_WAIT_SECONDS` for a slot. An answer that still cannot be checked (OpenAI unavailable, or the limit still reached) is stored as not checked: `quality_score` empty, `analysis_details` `{"unchecked": true, "error": ...}`, not flagged. It is never given a middle score and never counted as acceptable. How an answer was entered is judged separately: "pasted" when at least half of a 20+ character answer was pasted, "no typing" when a 20+ character answer had no input events.

`backend/.env.example` lists every variable.

### Frontend (`frontend/.env`, `frontend/.env.production`)

```env
VITE_API_BASE_URL=https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1
VITE_FRONTEND_BASE_URL=https://storage.googleapis.com/bot-detection-frontend-20251208
VITE_APP_NAME=Bot Detection Dashboard
VITE_ROUTER_MODE=hash                # production only: index.html#/path addresses for bucket hosting
```

## 🧪 Testing

```bash
cd backend
pip install -r requirements.txt -r requirements-test.txt
SECRET_KEY=test python -m pytest tests          # 275 tests; uses SQLite via aiosqlite
```

`backend/tests/fixtures/coffee_demo_survey.xml` is a complete demo survey that has been run end to end (tracked, uploaded to Decipher, taken as a respondent, results seen on Live Quality and in Decipher's data). Load testing: `locust -f backend/locustfile.py`.

## 📊 Monitoring

- `/health`: status, plus how many data-centre IP networks are loaded
- `/metrics`: Prometheus metrics
- Cloud Run logs: `gcloud logging read 'resource.labels.service_name="bot-backend"' --project survey-bot-detection --limit 50`

## 🔒 Security

- The dashboard and API have no user login. Changing settings requires `ADMIN_TOKEN` (header `X-Admin-Token`); saved secrets are encrypted at rest and never returned to the browser.
- Decipher API keys are sent only to Decipher and removed from any error text.
- Signed trackers (`TRACKING_TOKEN_SECRET`, optional) stop outsiders who never saw the survey from adding sessions under its name; anyone who opens the survey page can read the token. Production currently runs without it.
- Rate limits per IP, per server instance: new sessions 30 a minute, other writes 600 a minute, Fix with AI 20 an hour. Input validation with Pydantic; parameterised queries.
- Rejected events are logged by type only, because the page address can hold personal details. Stored event JSON keeps only the event's own fields (page details, ids and sizes are kept in their own columns or once on the session).
- `.gcloudignore` and `.dockerignore` keep `.env` and local data out of builds and images.

## 🚀 Deployment

Production runs in Google Cloud project `survey-bot-detection`, region `northamerica-northeast2`.

**Backend (Cloud Run service `bot-backend`)**: 1 CPU, 1 GiB memory, 1 to 10 instances, Cloud SQL `bot-db` and `bot-db-v2`, VPC connector `serverless-connector`, secrets `DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY`, `ADMIN_TOKEN`. Build an image tagged with the commit, then deploy only the image (other settings are kept):

```bash
gcloud meta list-files-for-upload backend        # check: no .env, .venv, *.db, tests
gcloud builds submit ./backend --tag northamerica-northeast2-docker.pkg.dev/survey-bot-detection/backend/bot-backend:$(git rev-parse --short HEAD) --project survey-bot-detection
gcloud run deploy bot-backend --image northamerica-northeast2-docker.pkg.dev/survey-bot-detection/backend/bot-backend:$(git rev-parse --short HEAD) --region northamerica-northeast2 --project survey-bot-detection
```

Add `--update-env-vars` / `--update-secrets` only for values that change. **Don't run `deploy-backend.ps1` as written**: it replaces all environment variables and secrets and attaches only `bot-db`, which would drop the `bot-db-v2` connection. New tables are created at startup; no migration is needed for this release.

**Dashboard (Cloud Storage bucket `bot-detection-frontend-20251208`)**:

```bash
cd frontend && npx vite build --mode production && cd ..
gcloud storage rsync -r frontend/dist gs://bot-detection-frontend-20251208 --project survey-bot-detection
gcloud storage objects update gs://bot-detection-frontend-20251208/index.html --cache-control="no-cache"
gcloud storage objects update "gs://bot-detection-frontend-20251208/assets/**" --cache-control="public, max-age=31536000, immutable"
```

Don't delete unmatched files in the bucket: `tracking-client.js` there may be used by surveys in the field.

**After a fresh deploy**: read the admin token with `gcloud secrets versions access latest --secret ADMIN_TOKEN --project survey-bot-detection`, open the deployed Settings page (`index.html#/settings`), unlock, and enter the Decipher API key to turn on Upload to Decipher.

**Rollback**: the previous backend revision is `bot-backend-00068-2rf`:

```bash
gcloud run services update-traffic bot-backend --to-revisions bot-backend-00068-2rf=100 --region northamerica-northeast2 --project survey-bot-detection
```

More in [SELECTIVE_DEPLOYMENT_GUIDE.md](SELECTIVE_DEPLOYMENT_GUIDE.md) and [rollback-procedures.md](rollback-procedures.md).

## 🗺️ Roadmap

Done: behaviour, text, fraud, grid and timing analysis; composite scoring; hierarchical API; reports; Decipher XML tracking and upload; Live Quality with per-survey rules and data-file flags; Settings that save; redesigned dashboard; production deployment.

Next:
- Fix `deploy-backend.ps1` to update settings instead of replacing them
- User accounts (today only settings changes are protected)
- Real-time alerts for surveys with rising bot rates
- Machine-learning models alongside the rule-based engine

## 📄 License

MIT License. See [LICENSE](LICENSE).
