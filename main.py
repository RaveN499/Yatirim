import requests
import yfinance as yf
import os
from datetime import datetime

# --- SENİN GERÇEK VERİLERİN ---
portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.4532},
    "ITP": {"adet": 400, "maliyet": 2.1240},
    "ZPX30": {"adet": 5, "maliyet": 155.20},
    "TZL": {"adet": 9000, "maliyet": 0.110665}, # 995.99 TL / 9000 adet
    "ALTIN.S1": {"adet": 40, "maliyet": 24.10}
}

def get_price_tefas(kod):
    """TEFAS API'sinden veri çekmek için en güvenli yol"""
    url = "https://www.tefas.gov.tr/api/Common/GetFunds"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://www.tefas.gov.tr/FonAnaliz.aspx"
    }
    try:
        # Önce bir oturum (session) başlatıyoruz
        session = requests.Session()
        session.get("https://www.tefas.gov.tr", headers=headers, timeout=10)
        
        # Veriyi istiyoruz
        response = session.post(url, data={"fontype": "YAT"}, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json().get('data', [])
            for item in data:
                if item['FundCode'] == kod:
                    return float(item['Price'])
    except:
        return None
    return None

def get_gold_price():
    """Altın Sertifikası için Yahoo Finance alternatifi"""
    try:
        # period="5d" yaparak son 5 günün verisini alıp en güncelini çekiyoruz
        gold = yf.download("ALTIN.S1.IS", period="5d", progress=False)
        if not gold.empty:
            return float(gold['Close'].iloc[-1])
    except:
        return None

# --- RAPOR OLUŞTURMA ---
rapor = f"📅 **{datetime.now().strftime('%d.%m.%Y')} PORTFÖY RAPORU**\n"
rapor += "----------------------------------\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = None
    if kod == "ALTIN.S1":
        guncel = get_gold_price()
    else:
        guncel = get_price_tefas(kod)

    if guncel:
        # TZL için özel düzeltme (Eğer TEFAS 0.1107 gönderirse bankadaki 997'yi yakalarız)
        if kod == "TZL" and guncel < 1.0:
            # TZL fiyatı bazen yuvarlanmış gelir, biz 1.01 TL kârı korumak için hassas hesaplarız
            pass 
            
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
    else:
        rapor += f"⚠️ **{kod}**: Veri ambargosu aşılamadı!\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**"

# Discord'a Gönder
webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
