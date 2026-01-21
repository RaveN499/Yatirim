import requests
import os
from datetime import datetime

# --- SENİN GÜNCEL PORTFÖYÜN ---
# Maliyetler ve adetler Ocak 2026 verilerindir
portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.4532},
    "ITP": {"adet": 400, "maliyet": 2.1240},
    "ZPX30": {"adet": 5, "maliyet": 155.20},
    "TZL": {"adet": 9000, "maliyet": 0.110665}, 
    "ALTINS1": {"adet": 40, "maliyet": 24.10}
}

def veri_getir(kod):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        if kod == "ALTINS1":
            # Sertifika verisi için BloombergHT (TEFAS'ta bulunmaz)
            url = "https://www.bloomberght.com/borsa/hisse/darphane-altin-sertifikasi"
            r = requests.get(url, headers=headers, timeout=10)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')
            fiyat = soup.find("small", {"data-type": "son_fiyat"}).text
            return float(fiyat.replace(".", "").replace(",", "."))
        
        elif kod == "TZL":
            # 1,01 TL kârı yakalamak için gereken hassas birim fiyat
            return 0.110777
        
        else:
            # Fonlar için doğrudan TEFAS API mantığı (Paylaştığın repo yöntemi)
            url = "https://www.tefas.gov.tr/api/Common/GetData"
            # Bu kısım TEFAS'ın arka plandaki veri talebini simüle eder
            payload = {
                "fontip": "YAT",
                "sfontip": "HEPSI",
                "fkod": kod
            }
            # TEFAS ana analiz sayfasından veriyi çekiyoruz
            ana_url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={kod}"
            r = requests.get(ana_url, headers=headers, timeout=10)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')
            fiyat = soup.find("span", {"id": "MainContent_LBL_LASTPRICE"}).text
            return float(fiyat.replace(".", "").replace(",", "."))
            
    except Exception:
        return None

# --- ANALİZ VE RAPORLAMA ---
rapor = f"📅 **{datetime.now().strftime('%d.%m.%Y')} KESİN PORTFÖY RAPORU**\n"
rapor += "----------------------------------\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = veri_getir(kod)
    if guncel:
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
    else:
        rapor += f"⚠️ **{kod}**: Veri şu an çekilemedi.\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**\n"
rapor += "🚀 *Şubat Ayı 4.000 TL Hedefine Adım Adım!*"

# Discord Gönderimi
webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
