import requests
import yfinance as yf
import os
import pandas as pd
from datetime import datetime

# --- SENİN GERÇEK VERİLERİN ---
portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.4532},
    "ITP": {"adet": 400, "maliyet": 2.1240},
    "ZPX30": {"adet": 5, "maliyet": 155.20},
    "TZL": {"adet": 9000, "maliyet": 0.110665}, # 995.99 TL / 9000 adet
    "ALTIN.S1": {"adet": 40, "maliyet": 24.10}
}

def get_price(kod):
    # 1. ALTIN SERTİFİKASI
    if kod == "ALTIN.S1":
        try:
            ticker = yf.Ticker("ALTIN.S1.IS")
            hist = ticker.history(period="5d") # Daha geniş bir aralık bakıyoruz
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        except: return None

    # 2. FONLAR İÇİN TEFAS (Daha güvenli bir yöntem)
    url = "https://www.tefas.gov.tr/api/Common/GetFunds"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    try:
        # TZL için bazen fiyat 1.0 görünür, 0.1107'yi yakalamak için tüm veriyi tarıyoruz
        response = requests.post(url, data={"fontype": "YAT"}, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json().get('data', [])
            match = next((x for x in data if x['FundCode'] == kod), None)
            if match:
                return float(match['Price'])
    except:
        pass
    
    # 3. YEDEK KAYNAK (Eğer TEFAS patlarsa Mynet denemesi)
    try:
        url_mynet = f"https://finans.mynet.com/borsa/yatirimfonlari/{kod}/"
        r = requests.get(url_mynet, headers=headers, timeout=10)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        fiyat_tag = soup.select_one(".fn-last-price")
        if fiyat_tag:
            return float(fiyat_tag.text.replace(".", "").replace(",", "."))
    except:
        return None

# --- RAPORLAMA ---
rapor = f"📅 **{datetime.now().strftime('%d.%m.%Y')} PORTFÖY RAPORU**\n"
rapor += "----------------------------------\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = get_price(kod)
    if guncel:
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
    else:
        rapor += f"⚠️ **{kod}**: Fiyat şu an alınamadı.\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**"

# Discord Gönderimi
webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
