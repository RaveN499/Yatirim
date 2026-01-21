import requests
import yfinance as yf
import os
from bs4 import BeautifulSoup

# --- PORTFÖYÜN (Kendi değerlerinle güncelle) ---
portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.45},
    "ITP": {"adet": 400, "maliyet": 2.12},
    "ZPX30": {"adet": 5, "maliyet": 155.0},
    "TZL": {"adet": 9000, "maliyet": 0.1107},
    "ALTIN.S1": {"adet": 40, "maliyet": 24.10}
}

def get_price(kod):
    # Daha profesyonel "Ben insanım" kimliği
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    }

    # 1. ALTIN SERTİFİKASI (Yahoo Finance)
    if kod == "ALTIN.S1":
        try:
            # yf.download sunucularda bazen daha iyi çalışır
            data = yf.download("ALTIN.S1.IS", period="1d", progress=False)
            if not data.empty:
                return float(data['Close'].iloc[-1])
        except:
            return None

    # 2. FONLAR (Mynet denemesi)
    try:
        url = f"https://finans.mynet.com/borsa/yatirimfonlari/{kod}/"
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # Mynet'in olası tüm fiyat etiketlerini tarıyoruz
            fiyat_etiketi = (
                soup.select_one(".fn-last-price") or 
                soup.select_one("#siradaki-deger") or
                soup.find("span", {"id": "siradaki-deger"})
            )
            
            if fiyat_etiketi:
                # "1.234,56" formatını "1234.56" formatına çeviriyoruz
                temiz_metin = fiyat_etiketi.text.strip().replace(".", "").replace(",", ".")
                return float(temiz_metin)
    except:
        pass
    return None

# --- RAPOR OLUŞTURMA ---
rapor = "📈 **GÜNLÜK PORTFÖY RAPORU** 📈\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = get_price(kod)
    if guncel:
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
    else:
        rapor += f"⚠️ **{kod}**: Fiyat alınamadı!\n"

rapor += f"\n💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**"

# Discord'a gönder
webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
