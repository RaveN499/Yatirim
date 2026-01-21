import os
import requests
import pandas as pd
from tefas import Crawler
from datetime import datetime, timedelta

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
# Ziraat ve diger fonlarin
FUNDS = ["TTE", "ITP", "ZBB", "TZL"]
TODAY = datetime.now().strftime("%Y-%m-%d")
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def main():
    tefas = Crawler()
    results = []

    # 1. TEFAS FONLARI (TTE, ITP, ZBB, TZL)
    try:
        # Once bugunun verisini dene
        data = tefas.fetch(start=TODAY)
        if data.empty or not any(f in data['code'].values for f in FUNDS):
            print("Bugunun verisi eksik, dunun verisi çekiliyor...")
            data = tefas.fetch(start=YESTERDAY)
        
        # ZBB için özel kontrol - bazen farklı formatlarda gelebilir
        filtered = data[data['code'].isin(FUNDS)]
        
        # Debug: Hangi fonlar geldi?
        print(f"Bulunan fonlar: {filtered['code'].tolist()}")
        
        for _, row in filtered.iterrows():
            results.append({"code": row['code'], "price": float(row['price'])})
            
        # ZBB özellikle gelmemişse alternatif arama
        if "ZBB" not in [r['code'] for r in results]:
            print("ZBB bulunamadı, alternatif kodlar deneniyor...")
            # ZBB'nin tam adıyla arama
            zbb_alternatives = data[data['code'].str.contains('ZBB', case=False, na=False)]
            if not zbb_alternatives.empty:
                print(f"Alternatif ZBB kodları: {zbb_alternatives['code'].tolist()}")
                for _, row in zbb_alternatives.iterrows():
                    results.append({"code": row['code'], "price": float(row['price'])})
                    
    except Exception as e:
        print(f"TEFAS hatasi: {e}")

    # 2. ALTIN.S1 (Farklı formatlar deneniyor)
    altin_symbols = ["GLDGR.IS", "ALTIN.IS", "ALTINS1.IS"]
    for symbol in altin_symbols:
        try:
            import yfinance as yf
            print(f"Altın için {symbol} deneniyor...")
            altin_df = yf.download(symbol, period="5d", progress=False)
            if not altin_df.empty and len(altin_df) > 0:
                price = float(altin_df['Close'].iloc[-1])
                results.append({"code": "ALTIN.S1", "price": price})
                print(f"✓ Altın verisi {symbol} ile alındı: {price}")
                break
        except Exception as e:
            print(f"{symbol} hatasi: {e}")
            continue

    # 3. DISCORD'A GONDER
    if results:
        send_to_discord(results)
        print(f"✓ {len(results)} ürün Discord'a gönderildi")
    else:
        print("⚠️ Hiç veri bulunamadı!")

def send_to_discord(data):
    fields = []
    for item in sorted(data, key=lambda x: x['code']):
        fields.append({
            "name": f"🔹 {item['code']}",
            "value": f"**Fiyat:** {item['price']:.4f} TL",
            "inline": True
        })

    payload = {
        "embeds": [{
            "title": f"📈 Günlük Portföy Özeti ({TODAY})",
            "color": 3066993,
            "fields": fields,
            "footer": {"text": "Ziraat & Midas Yatırım Takibi"}
        }]
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Discord gönderim hatası: {e}")

if __name__ == "__main__":
    main()
