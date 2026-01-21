import requests
import yfinance as yf
import os
import pandas as pd
from bs4 import BeautifulSoup

# 1. Portföy Bilgilerin
# Şubat'ta alım yaptıktan sonra buradaki 'adet' ve 'maliyet' kısımlarını güncellemeyi unutma!
portfoy = {
    "TTE": {"adet": 0, "maliyet": 1.42},
    "ITP": {"adet": 0, "maliyet": 2.10},
    "ZPX30": {"adet": 0, "maliyet": 150.0},  # Yeni eklendi
    "TZL": {"adet": 9000, "maliyet": 995.99},   # Yeni eklendi
    "ALTIN.S1": {"adet": 100, "maliyet": 22.50}
}

def get_price(kod):
    try:
        if kod == "ALTIN.S1":
            # Altın sertifikası için Yahoo Finance kullanıyoruz
            ticker = yf.Ticker("ALTIN.S1.IS")
            return ticker.history(period="1d")['Close'].iloc[-1]
        else:
            # TTE, ITP, ZPX30 ve TZL için Mynet üzerinden hızlı çekim
            url = f"https://finans.mynet.com/borsa/yatirimfonlari/{kod}/"
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            # Fiyatı çekip sayıya çeviriyoruz
            fiyat_text = soup.select_one(".fn-last-price").text.replace(",", ".")
            return float(fiyat_text)
    except Exception as e:
        print(f"Hata oluştu ({kod}): {e}")
        return None

def send_discord(mesaj):
    webhook = os.getenv('DISCORD_WEBHOOK')
    if webhook:
        requests.post(webhook, json={"content": mesaj})
    else:
        print("Webhook bulunamadı, mesaj gönderilemedi.")

# Ana Döngü
rapor = "📈 **GÜNLÜK PORTFÖY RAPORU** 📈\n"
rapor += "----------------------------------\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = get_price(kod)
    if guncel:
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**"

# Discord'a gönder ve ekrana yazdır
send_discord(rapor)
print(rapor)
print("\nRapor başarıyla gönderildi!")
