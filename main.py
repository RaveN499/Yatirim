import os
import requests
import pandas as pd
from tefas import Crawler
from datetime import datetime, timedelta

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Ziraat ve diger fonlar
FUNDS = ["TTE", "ITP", "ZBB", "TZL"]

TODAY = datetime.now().strftime("%Y-%m-%d")

def main():
    if not WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL tanimli degil!")
        return

    tefas = Crawler()
    results = []

    # 1️⃣ TEFAS FONLARI (son 5 gun, en guncel veri)
    try:
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        data = tefas.fetch(start=start_date)

        if not data.empty:
            filtered = (
                data[data['code'].isin(FUNDS)]
                .sort_values("date")
                .groupby("code")
                .tail(1)
            )

            for _, row in filtered.iterrows():
                results.append({
                    "code": row["code"],
                    "price": float(row["price"])
                })
    except Exception as e:
        print(f"TEFAS hatasi: {e}")

    # 2️⃣ ALTIN.S1 (NaN ve kapali gun guvenli)
    try:
        import yfinance as yf

        altin_df = yf.download("ALTINS1.IS", period="10d", progress=False)

        if not altin_df.empty:
            last_price = altin_df["Close"].dropna().iloc[-1]
            results.append({
                "code": "ALTIN.S1",
                "price": float(last_price)
            })
    except Exception as e:
        print(f"ALTIN.S1 hatasi: {e}")

    # 3️⃣ DISCORD'A GONDER
    if results:
        send_to_discord(results)
    else:
        print("Gonderilecek veri yok.")

def send_to_discord(data):
    fields = []

    for item in sorted(data, key=lambda x: x["code"]):
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
            "footer": {
                "text": "Ziraat & Midas Yatırım Takibi"
            }
        }]
    }

    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print("Discord gonderim hatasi:", response.text)

if __name__ == "__main__":
    main()
