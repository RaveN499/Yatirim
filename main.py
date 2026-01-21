import requests
import os
import io
import pandas as pd
from datetime import datetime

# --- KRİTİK: Buraya Google Sheets'ten aldığın .csv ile biten linki koy ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcrNoWHwYj8ueNd9Z56GGCVAo6r6Fc2YfP2pEiHtcj5ffsB9e5qRWy2I24Yrlsj7OThjJqyVfgbWTQ/pub?gid=0&single=true&output=csv"

# --- PORTFÖY VERİLERİN ---
portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.4532},
    "ITP": {"adet": 400, "maliyet": 2.1240},
    "ZPX30": {"adet": 5, "maliyet": 155.20},
    "TZL": {"adet": 9000, "maliyet": 0.110665}, 
    "ALTINS1": {"adet": 40, "maliyet": 24.10}
}

def verileri_cek():
    try:
        # Linkin boş olup olmadığını kontrol et
        if "BURAYA_LİNKİ" in CSV_URL or not CSV_URL.startswith("http"):
            print("⚠️ HATA: CSV_URL henüz doğru tanımlanmamış!")
            return {}

        r = requests.get(CSV_URL, timeout=15)
        r.encoding = 'utf-8' # Türkçe karakter sorunu olmasın
        
        if r.status_code != 200:
            print(f"⚠️ HATA: Google Sheets'e ulaşılamadı. Kod: {r.status_code}")
            return {}

        # CSV'yi oku (Başlık olmadığını varsayıyoruz)
        df = pd.read_csv(io.StringIO(r.text), header=None)
        veriler = {}
        
        for _, row in df.iterrows():
            if len(row) >= 2:
                kod = str(row[0]).strip().upper()
                # Sayı temizleme: Virgülleri noktaya çevir
                fiyat_str = str(row[1]).replace(",", ".")
                try:
                    veriler[kod] = float(fiyat_str)
                except:
                    print(f"⚠️ {kod} için geçersiz fiyat formatı: {row[1]}")
        
        return veriler
    except Exception as e:
        print(f"💥 Sistemsel Hata: {e}")
        return {}

# --- RAPORLAMA ---
fiyatlar = verileri_cek()
rapor = f"📅 **{datetime.now().strftime('%d.%m.%Y')} PORTFÖY RAPORU**\n"
rapor += "----------------------------------\n"
toplam_kar = 0

if not fiyatlar:
    rapor += "❌ Veriler Google Sheets köprüsünden geçemedi!\n"
    rapor += "Lütfen CSV linkini ve hücreleri kontrol et.\n"
else:
    for kod, veri in portfoy.items():
        # Google'daki kodlarla (TTE, ALTINS1 vb.) eşleştir
        guncel = fiyatlar.get(kod)
        if guncel:
            kar = (guncel - veri['maliyet']) * veri['adet']
            toplam_kar += kar
            rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
        else:
            rapor += f"⚠️ **{kod}**: Tabloda bulunamadı!\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**"

# Discord Gönderimi
webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
