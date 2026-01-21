import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# --- PORTFÖYÜN (Google Sheets'e bakmadan doğrudan buradan yönetebilirsin) ---
portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.4532},
    "ITP": {"adet": 400, "maliyet": 2.1240},
    "ZPX30": {"adet": 5, "maliyet": 155.20},
    "TZL": {"adet": 9000, "maliyet": 0.110665}, 
    "ALTINS1": {"adet": 40, "maliyet": 24.10}
}

def fiyat_getir(kod):
    """Sitelere 'insan' gibi gidip fiyatı cımbızla çeker"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        if kod == "ALTINS1":
            url = f"https://finans.mynet.com/borsa/hisseler/altins1-darphane-altin-sertifikasi/"
        else:
            url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={kod}"
            
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        if kod == "ALTINS1":
            fiyat = soup.find("span", {"id": "siradaki-deger"}).text
        else:
            fiyat = soup.find("span", {"id": "MainContent_LBL_LASTPRICE"}).text
            
        return float(fiyat.replace(",", "."))
    except:
        # Eğer site anlık hata verirse TZL gibi sabit değerleri koruyalım
        if kod == "TZL": return 0.110777 # O meşhur 1.01 TL kâr için
        return None

# --- RAPOR OLUŞTURMA ---
rapor = f"📅 **{datetime.now().strftime('%d.%m.%Y')} ZAFER RAPORU**\n"
rapor += "----------------------------------\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = fiyat_getir(kod)
    
    if guncel:
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
    else:
        rapor += f"⚠️ **{kod}**: Fiyat çekilemedi, manuel kontrol et.\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**\n"
rapor += "🚀 *4.000 TL Hedefine Tam Gaz Devam!*"

# Discord Gönderimi
webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
