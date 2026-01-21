import requests
import os
import io
import pandas as pd
from datetime import datetime

# --- GOOGLE SHEETS KÖPRÜ LİNKİ ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcrNoWHwYj8ueNd9Z56GGCVAo6r6Fc2YfP2pEiHtcj5ffsB9e5qRWy2I24Yrlsj7OThjJqyVfgbWTQ/pub?gid=0&single=true&output=csv"

# --- PORTFÖY VERİLERİN ---
portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.4532},
    "ITP": {"adet": 400, "maliyet": 2.1240},
    "ZPX30": {"adet": 5, "maliyet": 155.20},
    "TZL": {"adet": 9000, "maliyet": 0.110665}, # 995.99 TL / 9000 adet
    "ALTINS1": {"adet": 40, "maliyet": 24.10}
}

def verileri_cek():
    try:
        # Google Sheets'ten CSV verisini çekiyoruz
        r = requests.get(CSV_URL, timeout=15)
        r.encoding = 'utf-8'
        
        # Boş satırları temizleyerek oku
        df = pd.read_csv(io.StringIO(r.text), header=None).dropna()
        veriler = {}
        
        for _, row in df.iterrows():
            if len(row) >= 2:
                # Kodları temizle ve büyük harfe çevir
                kod = str(row[0]).strip().upper()
                # Virgülleri noktaya çevirip sayıya dönüştür
                fiyat_str = str(row[1]).replace(",", ".").strip()
                try:
                    veriler[kod] = float(fiyat_str)
                except:
                    continue
        return veriler
    except Exception as e:
        print(f"Köprü Hatası: {e}")
        return {}

# --- RAPORLAMA MANTIĞI ---
fiyatlar = verileri_cek()
rapor = f"📅 **{datetime.now().strftime('%d.%m.%Y')} PORTFÖY RAPORU**\n"
rapor += "----------------------------------\n"
toplam_kar = 0

if not fiyatlar:
    rapor += "⚠️ Veriler henüz köprüden geçemedi. Sheets formüllerini kontrol et!\n"
else:
    for kod, veri in portfoy.items():
        # Google'daki kodlarla eşleştirme
        guncel = fiyatlar.get(kod)
        
        if guncel:
            kar = (guncel - veri['maliyet']) * veri['adet']
            toplam_kar += kar
            rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
        else:
            rapor += f"⚠️ **{kod}**: Tabloda veri bulunamadı!\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**"

# Discord Gönderimi
webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
