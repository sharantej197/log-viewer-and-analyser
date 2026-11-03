from datetime import datetime
from pathlib import Path
import csv
import os
import re
import secrets
import shutil
import subprocess
import time

from flask import Flask, abort, redirect, render_template, request, send_file, session, url_for
from werkzeug.utils import secure_filename

import plotter

BASE_DIR = Path(__file__).resolve().parent
WORKSPACES_DIR = Path(os.environ.get("WORKSPACES_DIR", BASE_DIR / "instance" / "workspaces"))
WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB per upload
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

ALLOWED_WORKSPACE_FILES = {
    "EperSvsT.svg", "EperSvsT.png", "EperSvsT.pdf",
    "LsPiChart.svg", "LsPiChart.png", "LsPiChart.pdf",
    "Esbar.svg", "Esbar.png", "Esbar.pdf",
    "Realtime.svg", "Realtime.png", "Realtime.pdf",
}


def workspace_path(create=False):
    workspace_id = session.get("workspace_id")
    if not workspace_id or not re.fullmatch(r"[a-f0-9]{32}", workspace_id):
        if not create:
            return None
        workspace_id = secrets.token_hex(16)
        session["workspace_id"] = workspace_id
    path = WORKSPACES_DIR / workspace_id
    if create:
        path.mkdir(parents=True, exist_ok=True)
    if path.is_dir():
        try:
            os.utime(path, None)
        except OSError:
            pass
        return path
    return None


def run_script(script, *args):
    return subprocess.run(
        ["bash", str(BASE_DIR / script), *map(str, args)],
        cwd=BASE_DIR, capture_output=True, text=True, timeout=60, check=False
    )


def load_rows(csv_path):
    with csv_path.open("r", newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.reader(handle))


@app.before_request
def expire_old_workspaces():
    # Remove abandoned workspaces after 24 hours; active sessions refresh mtime above.
    cutoff = time.time() - 24 * 60 * 60
    try:
        for item in WORKSPACES_DIR.iterdir():
            if item.is_dir() and item.stat().st_mtime < cutoff:
                shutil.rmtree(item, ignore_errors=True)
    except OSError:
        pass


@app.errorhandler(413)
def upload_too_large(_error):
    return render_template("upload.html", error="File exceeds the 20 MB upload limit."), 413


@app.route("/", methods=["GET", "POST"])
def uploadpage():
    if request.method == "GET":
        return render_template("upload.html")

    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return render_template("upload.html", error="Please choose a .log file."), 400
    safe_name = secure_filename(uploaded.filename)
    if not safe_name.lower().endswith(".log"):
        return render_template("upload.html", error="Only .log files are accepted."), 400

    workspace = workspace_path(create=True)
    log_path = workspace / "given.log"
    data_path = workspace / "data.csv"
    original_path = workspace / "originaldata.csv"
    uploaded.save(log_path)

    validation = run_script("checker.sh", log_path)
    if validation.returncode != 0 or validation.stdout.strip() != "true":
        log_path.unlink(missing_ok=True)
        return render_template("upload.html", error="Unsupported log format. Upload a valid supported Apache error log."), 400

    conversion = run_script("tablemaker.sh", log_path, data_path, original_path)
    if conversion.returncode != 0 or not data_path.exists():
        return render_template("upload.html", error="The log file could not be processed. Check that it follows the supported format."), 500

    session["has_data"] = True
    return redirect(url_for("Displaypage"))


@app.route("/Display")
def Displaypage():
    workspace = workspace_path()
    if not workspace or not session.get("has_data") or not (workspace / "data.csv").exists():
        return redirect(url_for("uploadpage"))
    return render_template("displaypage.html", rows=load_rows(workspace / "data.csv"))


@app.route("/filedownload")
def filedownload():
    workspace = workspace_path()
    data_path = workspace / "data.csv" if workspace else None
    if not session.get("has_data") or not data_path or not data_path.is_file():
        return redirect(url_for("uploadpage"))
    return send_file(data_path, as_attachment=True, download_name="LogAnalysis.csv", mimetype="text/csv")


@app.route("/DataVisualisation", methods=["GET", "POST"])
def finalpage():
    workspace = workspace_path()
    if not workspace or not session.get("has_data"):
        return redirect(url_for("uploadpage"))
    data_path = workspace / "data.csv"
    original_path = workspace / "originaldata.csv"
    if request.method == "POST":
        try:
            start = datetime.strptime(request.form.get("fromdate", "") + " " + request.form.get("fromtime", ""), "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(request.form.get("todate", "") + " " + request.form.get("totime", ""), "%Y-%m-%d %H:%M:%S")
            if start > end:
                raise ValueError
        except ValueError:
            return render_template("finalpage.html", message="invalid"), 400

        selected = []
        with original_path.open("r", newline="", encoding="utf-8", errors="replace") as source:
            for row in csv.reader(source):
                if len(row) < 2:
                    continue
                try:
                    timestamp = datetime.strptime(row[1], "%a %b %d %H:%M:%S %Y")
                except ValueError:
                    continue
                if start <= timestamp <= end:
                    selected.append(row)
        with data_path.open("w", newline="", encoding="utf-8") as target:
            csv.writer(target).writerows(selected)
        return redirect(url_for("finalpage"))

    message = plotter.analyse(data_path, workspace / "plots")
    return render_template("finalpage.html", message=message)


@app.route("/workspace-file/<filename>")
def workspace_file(filename):
    if filename not in ALLOWED_WORKSPACE_FILES:
        abort(404)
    workspace = workspace_path()
    if not workspace or not session.get("has_data"):
        abort(404)
    file_path = workspace / "plots" / filename
    if not file_path.is_file():
        abort(404)
    return send_file(file_path, as_attachment=request.args.get("download") == "1")


@app.route("/reset", methods=["POST"])
def reset_workspace():
    workspace = workspace_path()
    if workspace:
        shutil.rmtree(workspace, ignore_errors=True)
    session.clear()
    return redirect(url_for("uploadpage"))


if __name__ == "__main__":
    app.run(debug=False)
