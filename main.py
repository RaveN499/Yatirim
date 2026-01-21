import os
import requests
from tefas import Crawler
import pandas as pd
from datetime import datetime

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
FUNDS = ["TTE", "ITP", "ZPX", "TZL"]
TODAY = datetime.now().strftime("%Y-%m-%d")

def main():
    tefas = Crawler()
    print(f"--- {TODAY} için veri çekme işlemi başladı ---")
    
    # 1. TEFAS Verileri
    try:
        data = tefas.fetch(start=TODAY)
        # Sadece bizim fonları filtrele
        my_funds_data = data[data['code'].isin(FUNDS)][['date', 'code', 'price']]
        print(f"TEFAS'tan gelen fonlar: {my_funds_data['code'].tolist()}")
    except Exception as e:
        print(f"TEFAS Hatası: {e}")
        my_funds_data = pd.DataFrame()

    # 2. ALTIN.S1 Verisi (Hata almamak için importu buraya aldık)
    try:
        import yfinance as yf
        print("ALTIN.S1 çekiliyor...")
        altin_s1 = yf.download("ALTINS1.IS", period="1d")
        if not altin_s1.empty:
            altin_price = float(altin_s1['Close'].iloc[-1])
            altin_row = pd.DataFrame([{'date': TODAY, 'code': 'ALTIN.S1', 'price': altin_price}])
            my_funds_data = pd.concat([my_funds_data, altin_row], ignore_index=True)
            print("ALTIN.S1 eklendi.")
    except Exception as e:
        print(f"Altın Verisi Çekilemedi (Muhtemelen Python sürüm hatası): {e}")

    # 3. Discord'a Gönder
    if not my_funds_data.empty:
        send_discord_message(my_funds_data)
    else:
        print("Gönderilecek veri bulunamadı.")

def send_discord_message(df):
    fields = []
    for _, row in df.iterrows():
        fields.append({
            "name": f"🔹 {row['code']}",
            "value": f"**Fiyat:** {float(row['price']):.4f} TL",
            "inline": True
        })

    payload = {
        "embeds": [{
            "title": f"📊 Portföy Özeti ({TODAY})",
            "color": 3447003,
            "fields": fields
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    main()
