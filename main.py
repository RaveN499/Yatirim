import requests
import yfinance as yf
import os
from bs4 import BeautifulSoup

# PORTFÖYÜN
# Not: TZL için bankadaki 'Birim Fiyat' neyse onu yazmalısın. 
# Eğer kârı göremiyorsan maliyeti biraz daha düşük (örneğin 1.0) yazıp deneme yapabilirsin.
portfoy = {
    "TTE": {"adet": 5000, "maliyet": 1.42},
    "ITP": {"adet": 3000, "maliyet": 2.10},
    "ZPX30": {"adet": 100, "maliyet": 150.0},
    "TZL": {"adet": 9000, "maliyet": 1.0}, # ÖRNEK: Maliyeti bir tık düşük yazarsan kâr görünür
    "ALTIN.S1": {"adet": 100, "maliyet": 22.50}
}

def get_price(kod):
    try:
        if kod == "ALTIN.S1":
            ticker = yf.Ticker("ALTIN.S1.IS")
            price = ticker.history(period="1d")['Close'].iloc[-1]
            return float(price)
        else:
            url = f"https://finans.mynet.com/borsa/yatirimfonlari/{kod}/"
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Mynet bazen fiyatı farklı etiketlerde sunar, iki seçeneği de deniyoruz
            fiyat_etiketi = soup.select_one(".fn-last-price") or soup.select_one("#siradaki-deger")
            
            if fiyat_etiketi:
                fiyat_metni = fiyat_etiketi.text.replace(".", "").replace(",", ".").strip()
                return float(fiyat_metni)
            return None
    except Exception as e:
        print(f"Hata ({kod}): {e}")
        return None

def send_discord(mesaj):
    webhook = os.getenv('DISCORD_WEBHOOK')
    if webhook:
        requests.post(webhook, json={"content": mesaj})

# Raporlama
rapor = "📈 **GÜNLÜK PORTFÖY RAPORU** 📈\n"
rapor += "----------------------------------\n"
toplam_kar = 0

for kod, veri in portfoy.items():
    guncel = get_price(kod)
    if guncel:
        kar = (guncel - veri['maliyet']) * veri['adet']
        toplam_kar += kar
        rapor += f"🔹 **{kod}**: {guncel:.4f} TL (Kâr: {kar:,.2f} TL)\n"
    else:
        rapor += f"⚠️ **{kod}**: Fiyat çekilemedi!\n"

rapor += "----------------------------------\n"
rapor += f"💰 **TOPLAM NET KÂR: {toplam_kar:,.2f} TL**"

send_discord(rapor)
print(rapor)
