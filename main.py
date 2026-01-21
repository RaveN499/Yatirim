import os
import requests
import pandas as pd
from tefas import Crawler
from datetime import datetime
import yfinance as yf
import sys

# Ayarlar
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
# ZPX yerine ZBB eklendi
FUNDS = ["TTE", "ITP", "ZBB", "TZL"]
TODAY = datetime.now().strftime("%Y-%m-%d")

def main():
    print(f"Python Versiyonu: {sys.version}")
    tefas = Crawler()
    
    # 1. TEFAS Verilerini Çek
    try:
        # Tüm fonları çekip listedekileri filtrelemek daha garantidir
        data = tefas.fetch(start=TODAY)
        my_funds_data = data[data['code'].isin(FUNDS)][['date', 'code', 'price']]
        print(f"TEFAS'tan çekilen fonlar: {my_funds_data['code'].tolist()}")
    except Exception as e:
        print(f"TEFAS Hatası: {e}")
        my_funds_data = pd.DataFrame()

    # 2. ALTIN.S1 Verisini Çek (Yahoo Finance)
    try:
        print("ALTIN.S1 verisi çekiliyor...")
        # 'period="1d"' bazen boş dönebilir, '5d' alıp en sonuncuyu seçiyoruz
        altin_df = yf.download("ALTINS1.IS", period="5d", progress=False)
        if not altin_df.empty:
            last_price = float(altin_df['Close'].iloc[-1].iloc[0] if isinstance(altin_df['Close'].iloc[-1], pd.Series) else altin_df['Close'].iloc[-1])
            altin_row = pd.DataFrame([{'date': TODAY, 'code': 'ALTIN.S1', 'price': last_price}])
            my_funds_data = pd.concat([my_funds_data, altin_row], ignore_index=True)
            print(f"ALTIN.S1 başarıyla eklendi: {last_price}")
    except Exception as e:
        print(f"ALTIN.S1 Hatası: {e}")

    # 3. Discord Mesajı Gönder
    if not my_funds_data.empty:
        send_discord_message(my_funds_data)
    else:
        print("Gönderilecek veri bulunamadı!")

def send_discord_message(df):
    fields = []
    for _, row in df.iterrows():
        # Fiyatı sayıya çevir ve formatla
        price_val = float(row['price'])
        fields.append({
            "name": f"🔹 {row['code']}",
            "value": f"**Fiyat:** {price_val:.4f} TL",
            "inline": True
        })

    payload = {
        "embeds": [{
            "title": f"📈 Portföy Günlük Verileri ({TODAY})",
            "color": 3066993, # Yeşil tonu
            "fields": fields,
            "footer": {"text": "Üniversite öğrencisi portföy takip sistemi"}
        }]
    }
    
    res = requests.post(WEBHOOK_URL, json=payload)
    if res.status_code == 204:
        print("Discord mesajı gönderildi!")
    else:
        print(f"Discord Hatası: {res.status_code}")

if __name__ == "__main__":
    main()
