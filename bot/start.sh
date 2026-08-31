#!/bin/bash
# FullFilm-zle Film Bot Başlatıcı
# Bu script sunucuyu ve arka plandaki güncelleyiciyi başlatır.

cd "$(dirname "$0")"

# Python sanal ortamını kullan
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Arkaplanda scraper güncelleme döngüsü başlat
python scraper.py --serve > scraper.log 2>&1 &
echo $! > scraper.pid

# Ana web sunucusunu başlat
python server.py
