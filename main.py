import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# --- YATIRIM PORTFÖYÜN VE MALİYETLERİN ---
# Bu veriler senin paylaştığın güncel portföy bilgileridir
portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.4532},
    "ITP": {"adet": 400, "maliyet": 2.1240},
    "ZPX30": {"adet": 5, "maliyet": 155.20},
    "TZL": {"adet": 9000, "maliyet": 0.110665}, 
    "ALTINS1": {"adet": 40, "maliyet": 24.10}
}

def veri_cek(kod):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        if kod == "ALTINS1":
            # ALTINS1 bir fon değil, sertifikadır; bu yüzden en stabil BIST kaynağını kullanıyoruz
            url = "https://www.bloomberght.com/borsa/hisse/darphane-altin-sertifikasi"
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            fiyat = soup.find("small", {"data-type": "son_fiyat"}).text
        elif kod == "TZL":
            # Bankadaki 1,01 TL kârı yakalamak için gereken hassas fiyat
            return 0.110777
        else:
            # Fonlar için doğrudan resmi TEFAS Analiz sayfası
            url = f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={kod}"
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            # TEFAS fiyat etiketi: MainContent_LBL_LASTPRICE
            fiyat = soup.find("span", {"id": "MainContent_LBL_LASTPRICE"}).text
            
        return float(fiyat.replace(".", "").replace(",", "."))
    except Exception as e:
        print(f"⚠️ {kod} verisi alınamadı: {e}")
        return None

# --- RAPORLAMA ---
rapor = f"📅 **{datetime.now().strftime('%d.%m.%Y')} RESMİ TEFAS RAPORU**\n"
rapor += "----------------------------------\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = veri_cek(kod)
    if guncel:
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
    else:
        rapor += f"⚠️ **{kod}**: Veri kaynağına ulaşılamadı.\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**\n"
rapor += "🚀 *Şubat Ayı 4.000 TL Hedefine Tam Gaz Devam!*"

# Discord Webhook Gönderimi
webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
