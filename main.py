import requests
import yfinance as yf
import os
import pandas as pd

# --- PORTFÖYÜN ---
portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.45},
    "ITP": {"adet": 400, "maliyet": 2.12},
    "ZPX30": {"adet": 5, "maliyet": 155.0},
    "TZL": {"adet": 9000, "maliyet": 0.1107}, # TZL fiyatı hep 1'dir
    "ALTIN.S1": {"adet": 40, "maliyet": 24.10}
}

def get_all_funds():
    url = "https://www.tefas.gov.tr/api/Common/GetFunds"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.tefas.gov.tr",
        "Referer": "https://www.tefas.gov.tr/FonAnaliz.aspx"
    }
    data = {"fontype": "YAT"} # Tüm yatırım fonlarını getir
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json().get('data', [])
    except:
        return []
    return []

def get_gold_price():
    # Altın için Yahoo bazen GitHub'da naz yapar, farklı bir yöntem deniyoruz
    try:
        gold = yf.Ticker("ALTIN.S1.IS")
        # En son kapanış fiyatını al
        hist = gold.history(period="2d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
    except:
        return None

# Verileri topla
all_funds_data = get_all_funds()
gold_price = get_gold_price()

# Rapor oluştur
rapor = "📈 **GÜNLÜK PORTFÖY RAPORU** 📈\n"
rapor += "----------------------------------\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel_fiyat = None
    
    if kod == "ALTIN.S1":
        guncel_fiyat = gold_price
    elif kod == "TZL":
        guncel_fiyat = 1.0 # Para piyasası fonu birim fiyatı her zaman 1'dir
    else:
        # İndirdiğimiz listeden ilgili fonu bul
        match = next((x for x in all_funds_data if x['FundCode'] == kod), None)
        if match:
            guncel_fiyat = float(match['Price'])

    if guncel_fiyat:
        kar = (guncel_fiyat - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel_fiyat:.4f} TL (Kâr: {kar:,.2f} TL)\n"
    else:
        rapor += f"⚠️ **{kod}**: Veri alınamadı!\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**"

# Discord'a gönder
webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
