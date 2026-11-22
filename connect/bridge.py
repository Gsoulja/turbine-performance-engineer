"""Connect a model to the wind farm monitor demo.

Reads the real Hill of Towie rows the demo replays (2-10 July 2023, 21 turbines, 10-minute steps),
asks predict_day() for answers, and serves them as windmonitor.model/1 messages the page can poll.

    python3 bridge.py                 # serve at http://localhost:8790/latest
    python3 bridge.py --out feed.jsonl  # or write a file to load in the demo's Model feed dialog

Then open https://turbine-performance-engineer.vercel.app/demo/?model=http://localhost:8790/latest,
choose Hill of Towie and press "Replay the real rows".

Python 3.9+, standard library only. The message contract: https://turbine-performance-engineer.vercel.app/demo/MODEL_FEED.md
"""
import argparse
import csv
import io
import json
import urllib.request
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SITE = "https://turbine-performance-engineer.vercel.app/demo/data/rows/towie"
TURBINES = [f"T{i:02d}" for i in range(1, 22)]
MODEL = {"name": "stand-in rule", "version": "bridge example"}   # name your model here; the page shows it
STATUSES = {"normal", "stopped", "curtailed", "low", "sensor"}
COLUMNS = {"Power (kW)": "power_kw", "Wind speed (m/s)": "wind_ms", "Rotor speed (RPM)": "rotor_rpm",
           "Pitch angle (°)": "pitch_deg", "Nacelle position (°)": "nacelle_deg"}


def predict_day(turbine, day, rows):
    """Replace this with your model.

    turbine: "T01" ... "T21"; day: "2023-07-03"; rows: that day's 10-minute steps in time order, each a dict with
    time ("2023-07-03T14:20:00Z"), power_kw, wind_ms, rotor_rpm, pitch_deg and nacelle_deg (None when missing).

    Return {time: answer} for the steps your model covers. An answer needs a status (normal, stopped, curtailed,
    low or sensor) and can add cause, diagnosis, next_step, confidence (0 to 1), expected_kw and evidence (a list
    of short strings). Steps you leave out keep the page's stand-in rules.

    A day-level model, such as our stops model on Hugging Face, answers once per turbine-day: if it says yes,
    return its answer for the steps where the turbine stood still, with its probability as the confidence.

    The stand-in below is not a trained model. It only lets you try the connection: a turbine making almost
    nothing while the wind is usable is called stopped.
    """
    out = {}
    for r in rows:
        p, w = r["power_kw"], r["wind_ms"]
        if p is not None and w is not None and w >= 4 and p < 20:
            out[r["time"]] = {
                "status": "stopped",
                "cause": "stand-in rule",
                "diagnosis": f"Stand-in rule, not a trained model: {p:.0f} kW at {w:.1f} m/s.",
                "confidence": 0.5,
                "evidence": [f"wind {w:.1f} m/s", f"power {p:.0f} kW"],
            }
    return out


def load_rows(rows_dir=None):
    """{turbine: [row, ...]} from a local folder of T01.csv ... T21.csv, or from the demo site."""
    farm = {}
    for t in TURBINES:
        if rows_dir:
            text = (Path(rows_dir) / f"{t}.csv").read_text(encoding="utf-8")
        else:
            with urllib.request.urlopen(f"{SITE}/{t}.csv", timeout=60) as resp:
                text = resp.read().decode("utf-8")
        rows = []
        for rec in csv.DictReader(io.StringIO(text)):
            row = {"time": rec["Date and time"].replace(" ", "T")[:16] + ":00Z"}
            for col, key in COLUMNS.items():
                v = (rec.get(col) or "").strip()
                row[key] = float(v) if v else None
            rows.append(row)
        farm[t] = rows
    return farm


def build_messages(farm):
    """Run predict_day over every turbine-day; one windmonitor.model/1 message per step that has answers."""
    by_time = defaultdict(dict)
    for turbine, rows in farm.items():
        days = defaultdict(list)
        for r in rows:
            days[r["time"][:10]].append(r)
        for day, day_rows in sorted(days.items()):
            for time, answer in (predict_day(turbine, day, day_rows) or {}).items():
                if answer.get("status") not in STATUSES:
                    raise ValueError(f"{turbine} {time}: status must be one of {sorted(STATUSES)}")
                by_time[time][turbine] = answer
    return [{"schema": "windmonitor.model/1", "farm": "towie", "time": t, "model": MODEL, "turbines": by_time[t]}
            for t in sorted(by_time)]


def serve(messages, port):
    body = ("\n".join(json.dumps(m, ensure_ascii=False) for m in messages) + "\n").encode("utf-8")
    health = json.dumps({"ok": True, "schema": "windmonitor.model/1", "messages": len(messages)}).encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def _head(self, code, ctype, length=0):
            self.send_response(code)
            self.send_header("Access-Control-Allow-Origin", "*")            # the demo runs on another origin
            self.send_header("Access-Control-Allow-Private-Network", "true")  # lets a public page reach localhost
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(length))
            self.end_headers()

        def do_OPTIONS(self):
            self._head(204, "text/plain")

        def do_GET(self):
            path = self.path.split("?")[0].rstrip("/")
            if path in ("/latest", "/feed/towie"):     # /feed/towie also serves the Model feed dialog's server button
                self._head(200, "application/x-ndjson; charset=utf-8", len(body))
                self.wfile.write(body)
            elif path == "/health":
                self._head(200, "application/json", len(health))
                self.wfile.write(health)
            else:
                self._head(404, "text/plain")

        def log_message(self, *args):
            pass

    print(f"{len(messages)} messages for {len({t for m in messages for t in m['turbines']})} turbines")
    print(f"Serving at http://localhost:{port}/latest  (Ctrl+C to stop)")
    print(f"Open: https://turbine-performance-engineer.vercel.app/demo/?model=http://localhost:{port}/latest")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Connect a model to the wind farm monitor demo.")
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--rows", help="local folder with T01.csv ... T21.csv (default: read them from the demo site)")
    ap.add_argument("--out", help="write the messages to this .jsonl file instead of serving them")
    args = ap.parse_args()
    msgs = build_messages(load_rows(args.rows))
    if args.out:
        Path(args.out).write_text("\n".join(json.dumps(m, ensure_ascii=False) for m in msgs) + "\n", encoding="utf-8")
        print(f"Wrote {len(msgs)} messages to {args.out}. In the demo: Model feed, then File.")
    else:
        serve(msgs, args.port)
