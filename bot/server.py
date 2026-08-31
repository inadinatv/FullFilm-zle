#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FullFilm-zle Film Bot Server
Flask sunucusu: statik siteyi ve film verilerini sunar.
Sürekli güncelleme için scraper arka planda çalışır.
"""
import json
import time
import threading
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request

app = Flask(__name__, static_folder=".", static_url_path="")

DATA_DIR = Path(__file__).parent / "data"
CACHE_FILE = DATA_DIR / "movie_cache.json"

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/films")
def api_films():
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return jsonify(data)
        else:
            return jsonify({"films": [], "count": 0, "updated_at": None})
    except Exception as e:
        return jsonify({"films": [], "count": 0, "error": str(e)})

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").lower()
    genre = request.args.get("genre", "").lower()
    year = request.args.get("year", "")
    quality = request.args.get("quality", "")
    try:
        if not CACHE_FILE.exists():
            return jsonify([])
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        films = data.get("films", [])
        result = []
        for film in films:
            name = film.get("name", "").lower()
            if q and q not in name:
                continue
            if genre and genre not in [g.lower() for g in film.get("genres", [])]:
                continue
            if year and str(film.get("year", "")) != str(year):
                continue
            if quality and quality.lower() not in film.get("quality", "").lower():
                continue
            result.append(film)
        return jsonify(result)
    except Exception as e:
        return jsonify([])

@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory("assets", filename)

@app.route("/data/<path:filename>")
def data_file(filename):
    return send_from_directory("data", filename)

if __name__ == "__main__":
    # Sunucuyu 0.0.0.0'a bağla (preview ortamı için)
    app.run(host="0.0.0.0", port=5000, debug=False)
