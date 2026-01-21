import requests
import os
import io
import pandas as pd
from datetime import datetime

# --- BURAYA GOOGLE'DAN KOPYALADIĞIN CSV LİNKİNİ YAPIŞTIR ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcrNoWHwYj8ueNd9Z56GGCVAo6r6Fc2YfP2pEiHtcj5ffsB9e5qRWy2I24Yrlsj7OThjJqyVfgbWTQ/pub?gid=0&single=true&output=csv"

# --- PORTFÖY VERİLERİN ---
portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.4532},
    "ITP": {"adet": 400, "maliyet": 2.1240},
    "ZPX30": {"adet": 5, "maliyet": 155.20},
    "TZL": {"adet": 9000, "maliyet": 0.110665}, # 995.99 / 9000
    "ALTINS1": {"adet": 40, "maliyet": 24.10}
}

def verileri_cek():
    try:
        r = requests.get(CSV_URL)
        df = pd.read_csv(io.StringIO(r.text), header=None)
        # Tabloyu bir sözlüğe çeviriyoruz: {"TTE": 1.45, "ITP": 2.12 ...}
        veriler = {}
        for index, row in df.iterrows():
            kod = str(row[0]).strip()
            # Fiyatı sayıya çevirirken virgülleri noktaya çeviriyoruz
            fiyat = float(str(row[1]).replace(",", "."))
            veriler[kod] = fiyat
        return veriler
    except Exception as e:
        print(f"Veri çekme hatası: {e}")
        return {}

# Raporlama
fiyatlar = verileri_cek()
rapor = f"📅 **{datetime.now().strftime('%d.%m.%Y')} PORTFÖY RAPORU**\n"
rapor += "----------------------------------\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = fiyatlar.get(kod)
    if guncel:
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
    else:
        rapor += f"⚠️ **{kod}**: Veri köprüden geçemedi!\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**"

# Discord Gönderimi
webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
