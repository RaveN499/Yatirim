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

    # 1. TEFAS Verileri (TTE, ITP, ZBB, TZL)
    try:
        data = tefas.fetch(start=TODAY)
        if data.empty:
            print("Bugün verisi yok, düne bakılıyor...")
            data = tefas.fetch(start=YESTERDAY)
        
        my_funds = data[data['code'].isin(FUNDS)]
        for _, row in my_funds.iterrows():
            portfolio_data.append({'code': row['code'], 'price': float(row['price'])})
            print(f"✅ {row['code']} eklendi.")
    except Exception as e:
        print(f"TEFAS Veri Hatası: {e}")

    # 2. ALTIN.S1 Verisi (BIST Altın Sertifikası)
    try:
        import yfinance as yf
        # period="5d" yaparak en son kapanış fiyatını garantiye alıyoruz
        altin = yf.download("ALTINS1.IS", period="5d", progress=False)
        if not altin.empty:
            last_price = float(altin['Close'].iloc[-1])
            portfolio_data.append({'code': 'ALTIN.S1', 'price': last_price})
            print(f"✅ ALTIN.S1 eklendi: {last_price}")
    except Exception as e:
        print(f"ALTIN.S1 Çekilemedi: {e}")

    # 3. Discord Mesajı
    if portfolio_data:
        send_discord_message(portfolio_data)
    else:
        print("❌ Hiç veri bulunamadı!")

def send_discord_message(data_list):
    fields = []
    # Kodları alfabetik sırala
    sorted_data = sorted(data_list, key=lambda x: x['code'])
    for item in sorted_data:
        fields.append({
            "name": f"🔹 {item['code']}",
            "value": f"**Fiyat:** {item['price']:.4f} TL",
            "inline": True
        })

    payload = {
        "embeds": [{
            "title": f"📈 Portföy Özeti ({TODAY})",
            "color": 3066993,
            "description": "Ziraat ve Midas yatırımları için günlük takip.",
            "fields": fields,
            "footer": {"text": "Veriler TEFAS ve BIST üzerinden çekildi."}
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    main()
