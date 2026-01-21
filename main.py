import os
import requests
from tefas import Crawler
from datetime import datetime, timedelta

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Ana fon listesi
FUNDS = ["TTE", "ITP", "TZL"]

TODAY = datetime.now().strftime("%Y-%m-%d")

def main():
    if not WEBHOOK_URL:
        return

    tefas = Crawler()
    results = []

    # ======================
    # 1️⃣ TEFAS (ZBB dahil)
    # ======================
    try:
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        data = tefas.fetch(start=start_date)

        if not data.empty:
            data = data.sort_values("date")

            # Normal fonlar
            for code in FUNDS:
                df = data[data["code"] == code]
                if not df.empty:
                    results.append({
                        "code": code,
                        "price": float(df.iloc[-1]["price"])
                    })

            # 🔥 ZBB FIX (kod varyasyonlu)
            zbb_df = data[data["code"].str.startswith("ZB")]
            if not zbb_df.empty:
                zbb_latest = zbb_df.iloc[-1]
                results.append({
                    "code": "ZBB",
                    "price": float(zbb_latest["price"])
                })

    except Exception as e:
        results.append({"code": "TEFAS_HATA", "price": 0})

    # ======================
    # 2️⃣ ALTIN.S1 FIX
    # ======================
    try:
        import yfinance as yf

        price = None

        # 1. deneme
        df = yf.download("ALTINS1.IS", period="15d", progress=False)
        if not df.empty:
            closes = df["Close"].dropna()
            if not closes.empty:
                price = float(closes.iloc[-1])

        # 2. deneme (fallback)
        if price is None:
            df = yf.download("ALTINS1", period="15d", progress=False)
            if not df.empty:
                closes = df["Close"].dropna()
                if not closes.empty:
                    price = float(closes.iloc[-1])

        if price is not None:
            results.append({
                "code": "ALTIN.S1",
                "price": price
            })

    except Exception:
        pass

    # ======================
    # 3️⃣ DISCORD
    # ======================
    send_to_discord(results)

def send_to_discord(data):
    if not data:
        return

    fields = []
    for item in sorted(data, key=lambda x: x["code"]):
        fields.append({
            "name": f"🔹 {item['code']}",
            "value": f"{item['price']:.4f} TL",
            "inline": True
        })

    payload = {
        "embeds": [{
            "title": f"📈 Günlük Portföy ({TODAY})",
            "color": 3447003,
            "fields": fields,
            "footer": {"text": "Yatırım Takip Botu"}
        }]
    }

    r = requests.post(WEBHOOK_URL, json=payload)

    # embed fail olursa text at
    if r.status_code != 204:
        requests.post(WEBHOOK_URL, json={
            "content": str(data)
        })

if __name__ == "__main__":
    main()
