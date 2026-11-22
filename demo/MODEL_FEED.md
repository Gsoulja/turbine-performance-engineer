# Model feed contract (`windmonitor.model/1`)

The page runs on stand-in rules today. Anything the trained model sends replaces the rules for that turbine and step. Where it sends nothing, the rules keep running.

## Message (one per 10-minute step, any number of turbines)

```json
{
  "schema": "windmonitor.model/1",
  "farm": "kelmarsh",
  "time": "2023-05-01T10:00:00Z",
  "model": { "name": "OpenTSLM", "version": "r1" },
  "turbines": {
    "T04": {
      "status": "low",
      "cause": "possible yaw misalignment",
      "diagnosis": "Power runs 9% below expected at 7.8 m/s with no stop and no limit.",
      "next_step": "Check yaw alignment and the nacelle north calibration.",
      "confidence": 0.74,
      "expected_kw": 1450,
      "evidence": ["nacelle 11 deg off its neighbours", "pitch normal"]
    }
  }
}
```

| field | required | notes |
|---|---|---|
| `time` | yes | UTC ISO time of the step described. Must match the SCADA row time to the minute. |
| `turbines.<id>.status` | yes | `normal`, `stopped`, `curtailed`, `low`, `sensor`. Anything else drops that turbine. |
| `cause` | no | Short label. Used in the ledger and cause shares. Without it the page derives one from the status. |
| `diagnosis` | no | Plain-language explanation shown on the card and quoted by the Copilot. |
| `next_step` | no | Shown in Fix first. |
| `confidence` | no | 0 to 1. Outside the range it is ignored with a warning. |
| `expected_kw` | no | Replaces the baseline expected power, so losses are computed from the model's own expectation. |
| `evidence` | no | Up to 6 short strings shown under the diagnosis. |

Text is cut to 600 characters (cause 120, next step 300, evidence 200) and `<` `>` are stripped.

## Ways to send it

- `windMonitor.ingestModel(message)` returns `{ ok, accepted, errors }`; `windMonitor.checkModel(message)` validates without applying.
- Inline with the rows: `windMonitor.ingest({ time, turbines: { T04: { ...row, model: { status, ... } } } })`.
- Model feed dialog: file (`.json`, or `.jsonl` with one message per line), URL polling, paste.
- `?model=URL` in the page address starts polling that URL (a URL on another origin needs CORS).
- `window.postMessage({ type: "windmonitor.model", payload: message }, "*")` from the parent page.

Order: send a step's model output before that step's rows, or inline. A message for a past step only fills the replay store; it does not change steps already applied.

## What changes when it is connected

Status, diagnosis, cause, next step and expected power for covered turbines; the loss ledger and money (attributed by the model's status); the worklist; the Copilot, which says whether a diagnosis came from the model and quotes its confidence. The footer and each card say which source is live.

## Not covered yet

Fix-check verdicts from the model (still a before/after ratio), per-day confidence in the ledger, and a model-specific uncertainty band on expected power.

## Result packs (real results, loaded from `data/`)

Separate from the live feed: the page loads `data/index.json` at start and the files it lists, checks each one, and skips (with the reason in the Model feed dialog) any that fails.

| file | schema | where it shows |
|---|---|---|
| `days_<farm>.json` | `windmonitor.days/1` | Real results tab (turbine by day grid, counts computed from the file) and the turbine card while the real-rows replay is on that day. Rows outside the test cohort may carry `p_yes: null` and a `reason`; they are shown as "no model answer". |
| `stops_<farm>.json` | `windmonitor.stops/1` | Real results tab: energy by the model's cause against the log, largest stops, agreement counted from the file, `in_sample` flag per stop. |
| `fixcheck_<farm>_<turbine>.json` | `windmonitor.fixcheck/1` | "Did the fix work?" tab, first case: daily references, install date, estimates with 90% intervals, verdict, caveats. |
| `rows/<farm>/T01.csv ...` | Greenbyte-style CSV | A "Replay the real rows" button appears on that farm; terrain and positions stay real. |

The Copilot reads them through `get_stop_causes`, `get_stop_day_answers` and `get_fix_checks`, and is told to state the data basis, the log's limits and any in-sample flag.

### Checks (`checks.json`, `windmonitor.checks/1`)

Ground truth next to each answer. The page counts agreements itself from the per-stop checks (it does not copy the file's totals), shows a "Checked against" block per Kelmarsh stop (icon plus word for agrees / disagrees / not decisive / context only), a filter for stops where a source disagrees, the public track record under each answer type, the loop rule with pending / checked / accepted counters, and the "log was wrong" case. Copilot tools: `get_checks`, `get_track_record`, `get_log_wrong_case`. Engineer verdicts are stored as `state: "pending"`; nothing on the page promotes one to checked or accepted, because that check runs offline.

### Three questions (`days_*.json`)

`windmonitor.days/1` carries one question per file. Optional top-level `use_case` is `curtailment` or `underperformance`; absent means downtime. Optional `answered_by`, `check_note`, and per-row `lost_pct`. The Real results tab opens with a table of the three questions, then one section per loaded question (grid, counts computed from the file, the log as one check, the public track record). A question with no file shows "No result loaded for this question yet". The Copilot reads them with `get_stop_day_answers` (`use_case`) and `get_checks` (`turbine`, `date`, `use_case`).

## Local model server (curtailment tree)

`serve/server.py` (run `uv run serve/server.py` from the project folder, port 8780) loads the frozen `models/curtailment_frozen_v1` tree and serves `GET /feed/towie`, the tree run over the Hill of Towie real rows as `windmonitor.model/1` lines, and `POST /score/curtailment` for one day of any farm. In the page: Model feed, "Run the tree on Hill of Towie rows".

- It answers one question. It sends a message only for steps that at least 2 of 3 seeds flag on an alerting day; every other step keeps the stand-in rules.
- Hill of Towie is a maker the model never saw, so the expected-power curves come from the farm's own days (power scaled to the 2050 kW basis), as the model's config describes.
- Check on those rows against the grid operator's dispatch record (Elexon, unit HLTWW-1): the tree alerts on 2023-07-02, 07-03 and 07-07 (17 to 20 turbines), the three days with instructions, and on none of the days without one except 2 turbines on 07-08. These 2023 rows are not part of the saved curtailment pack, and nothing here was used to pick a threshold.
- Models and data stay on the machine; the page only receives the answers. The public showcase does not include the server.
