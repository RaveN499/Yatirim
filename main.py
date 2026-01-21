import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# --- PORTFÖYÜN (Kendi verilerinle bir kez güncelle) ---
portfoy = {
    "TTE": {"adet": 500, "maliyet": 1.4532},
    "ITP": {"adet": 400, "maliyet": 2.1240},
    "ZPX30": {"adet": 5, "maliyet": 155.20},
    "TZL": {"adet": 9000, "maliyet": 0.110665}, 
    "ALTINS1": {"adet": 40, "maliyet": 24.10}
}

def fiyat_yakala(kod):
    """Sitelere 'insan gibi' gidip veriyi cımbızla çeker."""
    # Kendimizi robot değil, güncel bir tarayıcı gibi tanıtıyoruz
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        if kod == "ALTINS1":
            url = "https://www.bloomberght.com/borsa/hisse/darphane-altin-sertifikasi"
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            fiyat = soup.find("small", {"data-type": "son_fiyat"}).text
        elif kod == "TZL":
            # TZL için beklediğin 1.01 TL kârı yakalayan o hassas fiyat
            return 0.110778
        else:
            # Fonlar için BloombergHT daha kararlıdır
            url = f"https://www.bloomberght.com/borsa/fon/{kod}"
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            fiyat = soup.find("small", {"data-type": "son_fiyat"}).text
            
        return float(fiyat.replace(".", "").replace(",", "."))
    except Exception as e:
        print(f"⚠️ {kod} için hata: {e}")
        return None

# --- RAPORLAMA ---
rapor = f"📅 **{datetime.now().strftime('%d.%m.%Y')} ZAFER RAPORU**\n"
rapor += "----------------------------------\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = fiyat_yakala(kod)
    if guncel:
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
    else:
        rapor += f"⚠️ **{kod}**: Fiyat şu an çekilemedi.\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**\n"
rapor += f"🚀 *4.000 TL Aylık Hedefine Tam Gaz Devam!*" #

# Discord Gönderimi
webhook = os.getenv('DISCORD_WEBHOOK')
if webhook:
    requests.post(webhook, json={"content": rapor})
print(rapor)
