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
        
        filtered = data[data['code'].isin(FUNDS)]
        for _, row in filtered.iterrows():
            results.append({"code": row['code'], "price": float(row['price'])})
    except Exception as e:
        print(f"TEFAS hatasi: {e}")

    # 2. ALTIN.S1 (Import hatasi vermemesi icin fonksiyona gomduk)
    try:
        import yfinance as yf
        altin_df = yf.download("ALTINS1.IS", period="5d", progress=False)
        if not altin_df.empty:
            price = float(altin_df['Close'].iloc[-1])
            results.append({"code": "ALTIN.S1", "price": price})
    except Exception as e:
        print(f"Altin.S1 hatasi: {e}")

    # 3. DISCORD'A GONDER
    if results:
        send_to_discord(results)

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
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    main()
