import os
import requests
import pandas as pd
from tefas import Crawler
from datetime import datetime, timedelta

# Ayarlar
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
FUNDS = ["TTE", "ITP", "ZBB", "TZL"]
TODAY = datetime.now().strftime("%Y-%m-%d")
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def main():
    tefas = Crawler()
    portfolio_data = []

    # 1. TEFAS Verileri (ZBB, TTE, ITP, TZL)
    try:
        # Önce bugünü dene
        data = tefas.fetch(start=TODAY)
        if data.empty:
            print("Bugünün verisi henüz yok, düne bakılıyor...")
            data = tefas.fetch(start=YESTERDAY)
        
        my_funds = data[data['code'].isin(FUNDS)]
        for _, row in my_funds.iterrows():
            portfolio_data.append({'code': row['code'], 'price': float(row['price'])})
            print(f"✅ {row['code']} eklendi.")
    except Exception as e:
        print(f"TEFAS Hatası: {e}")

    # 2. ALTIN.S1 Verisi (Yahoo Finance)
    try:
        import yfinance as yf # Sadece burada çağırıyoruz
        altin = yf.download("ALTINS1.IS", period="5d", progress=False)
        if not altin.empty:
            # En son kapanış fiyatını al
            last_price = float(altin['Close'].iloc[-1])
            portfolio_data.append({'code': 'ALTIN.S1', 'price': last_price})
            print(f"✅ ALTIN.S1 eklendi: {last_price}")
    except Exception as e:
        print(f"ALTIN.S1 Hatası: {e}")

    # 3. Discord'a Gönder
    if portfolio_data:
        send_discord_message(portfolio_data)
    else:
        print("❌ Hiç veri çekilemedi!")

def send_discord_message(data_list):
    fields = []
    for item in data_list:
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
            "footer": {"text": "Veriler otomatik güncellendi."}
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    main()
