#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FullFilm-zle Film Bot Scraper
Sürekli güncel film verilerini fullhdfilmizlesene.now sitesinden çeker.
"""
import json
import re
import time
import urllib.request
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup yükleniyor...")
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4", "lxml", "requests"])
    from bs4 import BeautifulSoup

try:
    import requests
except ImportError:
    import urllib.request

BASE = "https://www.fullhdfilmizlesene.now"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CACHE_FILE = DATA_DIR / "movie_cache.json"


def fetch(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Fetch hatası ({url}): {e}")
        return None


def parse_film_cards(html):
    soup = BeautifulSoup(html, "lxml")
    films = []
    # Site yapısı: <a href="/film/.../"> ... <img> ... <h3> ... </a> şeklinde kartlar
    # Tüm film bağlantılarını topla
    links = soup.select('a[href^="/film/"]')
    seen = set()
    for a in links:
        href = a.get("href", "").strip()
        if not href.startswith("/film/"):
            continue
        # Aynı bağlantıyı birden fazla ekleme
        if href in seen:
            continue
        seen.add(href)
        # Kart içindeki img src'yi bul
        img_tag = a.select_one("img")
        poster = img_tag.get("src", "") if img_tag else ""
        if poster and not poster.startswith("http"):
            poster = BASE + poster
        # Kart başlığı
        title_tag = a.select_one("h2, h3, .title, strong")
        name = title_tag.get_text(strip=True) if title_tag else ""
        # Eğer başlık çok kısa veya anlamsızsa href'den türet
        if not name or len(name) < 2:
            slug = href.split("/")[-2] if href.endswith("/") else href.split("/")[-1]
            name = slug.replace("-", " ").title()
        # Açıklama / sinopsis için film sayfasından çekebiliriz ama hızlıca burada tutalım
        # Not: detay sayfası ayrı çekilecek
        films.append({
            "id": href,
            "url": BASE + href,
            "slug": href.strip("/"),
            "name": name,
            "poster": poster,
            "year": None,
            "rating": None,
            "quality": None,
            "language": None,
            "genres": None,
            "description": None,
        })
    return films


def parse_home():
    html = fetch(BASE + "/")
    if not html:
        return []
    films = parse_film_cards(html)
    # Ek olarak yeni filmler sayfasından çekelim
    extra = fetch(BASE + "/yeni-filmler/")
    if extra:
        extra_films = parse_film_cards(extra)
        seen_ids = {f["id"] for f in films}
        for ef in extra_films:
            if ef["id"] not in seen_ids:
                films.append(ef)
                seen_ids.add(ef["id"])
    return films[:200]  # İlk 200 film


def parse_film_detail(url):
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    # Başlık
    title_tag = soup.select_one("h1") or soup.select_one("title")
    name = title_tag.get_text(strip=True) if title_tag else ""
    # Açıklama
    desc_tag = soup.select_one('[class*="description"], .sinopsis, .content p')
    description = desc_tag.get_text(strip=True) if desc_tag else ""
    # Poster büyük boy
    poster_tag = soup.select_one('img[src*="poster/film-lg/"]') or soup.select_one('img[src*="cover/"]')
    poster = poster_tag.get("src", "") if poster_tag else ""
    if poster and not poster.startswith("http"):
        poster = BASE + poster
    # Rating (IMDB puanı gibi sayısal)
    rating_tag = soup.select_one('.imdb, [class*="rating"]')
    rating = None
    if rating_tag:
        m = re.search(r"([0-9]+[.,][0-9]+)", rating_tag.get_text())
        if m:
            rating = m.group(1).replace(",", ".")
    # Yıl
    year_tag = soup.select_one('a[href*="/yil/"]')
    year = None
    if year_tag:
        m = re.search(r"(\d{4})", year_tag.get_text())
        if m:
            year = int(m.group(1))
    # Kalite
    quality = None
    for q in ["4K", "1080p", "HD", "Normal"]:
        if html.find(q) != -1:
            quality = q
            break
    # Dil
    language = None
    if "Türkçe Dublaj" in html:
        language = "Türkçe Dublaj"
    elif "Türkçe Altyazılı" in html or "Türkçe Altyazı" in html:
        language = "Türkçe Altyazılı"
    elif "Dublaj" in html:
        language = "Dublaj"
    elif "Altyazı" in html:
        language = "Altyazılı"
    else:
        language = "Yerli"
    # Tür/Genre
    genres = []
    genre_links = soup.select('a[href*="/filmizle/"]')
    for gl in genre_links:
        text = gl.get_text(strip=True)
        if text in ["Aksiyon Filmleri", "Komedi Filmleri", "Dram Filmleri", "Korku Filmleri",
                    "Gerilim Filmleri", "Romantik Filmleri", "Bilim Kurgu Filmleri",
                    "Fantastik Filmleri", "Suç Filmleri", "Animasyon Filmleri",
                    "Tarih Filmleri", "Aile Filmleri", "Yerli"]:
            genres.append(text.replace(" Filmleri", ""))
    # Kart bilgilerini zenginleştir
    # Yorum sayısı
    comments_tag = soup.select_one('[class*="yorum"]')
    comments = None
    if comments_tag:
        m = re.search(r"(\d+)\s+yorum", comments_tag.get_text())
        if m:
            comments = int(m.group(1))
    # Ekstra: iframe kodları (video embed)
    iframes = []
    for iframe in soup.select("iframe[src]"):
        src = iframe.get("src", "")
        if src and not src.startswith("data:"):
            if not src.startswith("http"):
                src = BASE + src
            iframes.append(src)
    # M3U8
    m3u8_links = re.findall(r"(https?://[^\s\"']+\.m3u8[^\s\"']*)", html)
    m3u8_links = list(dict.fromkeys(m3u8_links))  # unique

    return {
        "id": url.replace(BASE, "").rstrip("/"),
        "url": url,
        "slug": url.replace(BASE, "").rstrip("/"),
        "name": name,
        "description": description,
        "poster": poster,
        "rating": rating,
        "year": year,
        "quality": quality,
        "language": language,
        "genres": list(dict.fromkeys(genres)),
        "comments": comments,
        "iframes": iframes,
        "m3u8": m3u8_links,
    }


def enrich_films(films):
    enriched = []
    for film in films:
        # Detay sayfasını çek (sadece ilk 20 film için hızlı olsun)
        detail = parse_film_detail(film["url"])
        if detail:
            # Üzerine yaz ama id/url koru
            detail["id"] = film.get("id", detail["id"])
            detail["url"] = film.get("url", detail["url"])
            detail["slug"] = film.get("slug", detail["slug"])
            # Eğer detayda poster yoksa eskiyi kullan
            if not detail.get("poster"):
                detail["poster"] = film.get("poster")
            enriched.append(detail)
        else:
            enriched.append(film)
    return enriched


def scrape_all():
    print("[SCRAPER] Film listesi çekiliyor...")
    films = parse_home()
    print(f"[SCRAPER] {len(films)} film bulundu.")
    # İlk 30 film detaylandır
    print("[SCRAPER] Detay verileri zenginleştiriliyor...")
    enriched = []
    for i, f in enumerate(films):
        print(f"  [{i+1}/{min(30, len(films))}] {f['name']}")
        detail = parse_film_detail(f["url"])
        if detail:
            detail["id"] = f.get("id", detail["id"])
            detail["url"] = f.get("url", detail["url"])
            detail["slug"] = f.get("slug", detail["slug"])
            if not detail.get("poster"):
                detail["poster"] = f.get("poster")
            enriched.append(detail)
        else:
            enriched.append(f)
        time.sleep(0.5)  # Sunucuyu yormamak için
    # Kalan 170 film için sadece temel veriler
    for f in films[30:]:
        if f not in enriched:
            enriched.append(f)
    # Cache yaz
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump({
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(enriched),
            "films": enriched,
        }, file, ensure_ascii=False, indent=2)
    print(f"[SCRAPER] {len(enriched)} film kaydedildi: {CACHE_FILE}")
    return enriched


def main():
    while True:
        try:
            scrape_all()
        except Exception as e:
            print(f"[SCRAPER] Hata: {e}")
        print("[SCRAPER] 30 dakika sonra tekrar çekilecek...")
        time.sleep(1800)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        scrape_all()
    elif len(sys.argv) > 1 and sys.argv[1] == "--serve":
        main()
    else:
        # Varsayılan: bir kez çalıştır
        scrape_all()
