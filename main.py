import requests
import yfinance as yf
import os
import pandas as pd

# 1. Portföy Bilgilerin (Burası senin 'Kasan')
portfoy = {
    "TTE": {"adet": 5000, "maliyet": 1.42}, # Örnek değerler
    "ITP": {"adet": 3000, "maliyet": 2.10},
    "ALTIN.S1": {"adet": 100, "maliyet": 22.50}
}

def get_price(kod):
    try:
        if kod == "ALTIN.S1":
            ticker = yf.Ticker("ALTIN.S1.IS")
            return ticker.history(period="1d")['Close'].iloc[-1]
        else:
            # Fonlar için Mynet üzerinden hızlı çekim
            url = f"https://finans.mynet.com/borsa/yatirimfonlari/{kod}/"
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            fiyat = soup.select_one(".fn-last-price").text.replace(",", ".")
            return float(fiyat)
    except:
        return None

def send_discord(mesaj):
    webhook = os.getenv('DISCORD_WEBHOOK')
    if webhook:
        requests.post(webhook, json={"content": mesaj})

# Ana Döngü
rapor = "📈 **GÜNLÜK PORTFÖY RAPORU** 📈\n\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = get_price(kod)
    if guncel:
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"

rapor += f"\n💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**"
send_discord(rapor)
print("Rapor gönderildi!")
