import os
import requests
from tefas import Crawler
import pandas as pd
from datetime import datetime
import yfinance as yf

# Ayarlar
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL") # GitHub Secrets'tan alacak
FUNDS = ["TTE", "ITP", "ZPX", "TZL"]
TODAY = datetime.now().strftime("%Y-%m-%d")

def send_discord_message(data_df):
    if data_df.empty:
        return

    # Discord için mesaj içeriği oluşturma
    fields = []
    for _, row in data_df.iterrows():
        fields.append({
            "name": f"🔹 {row['code']}",
            "value": f"**Fiyat:** {row['price']:.4f} TL",
            "inline": True
        })

    payload = {
        "username": "Portföy Takip Botu",
        "embeds": [{
            "title": f"📊 Günlük Fon Verileri ({TODAY})",
            "color": 3447003, # Mavi renk kodu
            "fields": fields,
            "footer": {"text": "TEFAS ve BIST üzerinden otomatik çekildi."}
        }]
    }

    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("✅ Discord mesajı başarıyla gönderildi.")
    else:
        print(f"❌ Hata oluştu: {response.status_code}, {response.text}")

def main():
    tefas = Crawler()
    
    # 1. TEFAS Verileri
    data = tefas.fetch(start=TODAY)
    my_funds_data = data[data['code'].isin(FUNDS)][['date', 'code', 'price']]
    my_funds_data['price'] = pd.to_numeric(my_funds_data['price'])

    # 2. ALTIN.S1 Verisi (Yahoo Finance)
    altin_s1 = yf.download("ALTINS1.IS", period="1d")
    if not altin_s1.empty:
        altin_price = float(altin_s1['Close'].iloc[-1])
        altin_row = pd.DataFrame([{'date': TODAY, 'code': 'ALTIN.S1', 'price': altin_price}])
        my_funds_data = pd.concat([my_funds_data, altin_row], ignore_index=True)

    # 3. Discord'a Gönder
    send_discord_message(my_funds_data)

    # 4. Geçmişi Saklamak için CSV (Opsiyonel)
    try:
        existing_df = pd.read_csv("portfolio_history.csv")
        pd.concat([existing_df, my_funds_data]).drop_duplicates().to_csv("portfolio_history.csv", index=False)
    except FileNotFoundError:
        my_funds_data.to_csv("portfolio_history.csv", index=False)

if __name__ == "__main__":
    main()
