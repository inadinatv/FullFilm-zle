# FullFilm-zle — Film Botu

Bu depo, `https://www.fullhdfilmizlesene.now/` adresindeki film içeriklerini sürekli güncel tutarak sunan, kart tabanlı bir film botu içerir.

## Özellikler

- **Sürekli güncelleme**: `scraper.py` ile sitenin film verileri periyodik olarak çekilir.
- **Film kartları**: Her film poster, kalite (4K/HD/Normal), dil (Türkçe Dublaj / Altyazılı / DUAL), yıl, tür ve IMDB puanı ile gösterilir.
- **Film Robotu (Filtreler)**: Tür, yıl, kalite, dil ve isim bazlı filtreleme yapılabilir.
- **Iframe oynatıcı**: Film detaylarında kaynak sitedeki içerik iframe ile gömülü olarak sunulur.
- **Modern tasarım**: Karanlık tema, animasyonlu kartlar, responsive yapı.

## Çalıştırma

```bash
# Gerekli paketleri yükle
python3 -m venv venv
source venv/bin/activate
pip install beautifulsoup4 lxml requests flask

# Sunucuyu başlat
python server.py
```

Sunucu `http://localhost:5000` adresinde çalışacaktır.

## Dosya Yapısı

```
bot/
  index.html          # Ana film sitesi (SPA tarzı)
  server.py            # Flask sunucusu (API + statik dosya sunumu)
  scraper.py           # Sürekli güncelleme scraper'ı
  start.sh             # Tek komutla başlatma
  data/movie_cache.json # Güncel film verisi
```
