import requests
import os
import io
import pandas as pd
from datetime import datetime

# --- GOOGLE SHEETS CSV LİNKİNİ BURAYA YAPIŞTIR ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcrNoWHwYj8ueNd9Z56GGCVAo6r6Fc2YfP2pEiHtcj5ffsB9e5qRWy2I24Yrlsj7OThjJqyVfgbWTQ/pub?gid=0&single=true&output=csv"

portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.4532},
    "ITP": {"adet": 400, "maliyet": 2.1240},
    "ZPX30": {"adet": 5, "maliyet": 155.20},
    "TZL": {"adet": 9000, "maliyet": 0.110665}, 
    "ALTINS1": {"adet": 40, "maliyet": 24.10}
}

def verileri_cek():
    try:
        r = requests.get(CSV_URL, timeout=15)
        # Veriyi oku ve temizle
        df = pd.read_csv(io.StringIO(r.text), header=None).dropna()
        veriler = {}
        
        for _, row in df.iterrows():
            # Kodları temizle (boşlukları sil, büyük harf yap)
            kod = str(row[0]).strip().upper()
            fiyat_ham = str(row[1]).replace(",", ".").strip()
            
            try:
                veriler[kod] = float(fiyat_ham)
            except ValueError:
                print(f"⚠️ {kod} için geçersiz fiyat: {fiyat_ham}")
                
        return veriler
    except Exception as e:
        print(f"💥 Bağlantı Hatası: {e}")
        return {}

# Raporlama
fiyatlar = verileri_cek()
print(f"Sistemden çekilen ham veriler: {fiyatlar}") # Debug için

rapor = f"📅 **{datetime.now().strftime('%d.%m.%Y')} PORTFÖY RAPORU**\n"
rapor += "----------------------------------\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = fiyatlar.get(kod)
    
    if guncel and not pd.isna(guncel):
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
    else:
        rapor += f"⚠️ **{kod}**: Fiyat verisi hatalı veya boş!\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**"

webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
