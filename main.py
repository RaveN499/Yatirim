import os
import requests
from tefas import Crawler
from datetime import datetime, timedelta

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

FUNDS = ["TTE", "ITP", "TZL"]  # ZBB'yi özel alacağız
TODAY = datetime.now().strftime("%Y-%m-%d")

def main():
    if not WEBHOOK_URL:
        print("WEBHOOK BOS")
        return

    results = []
    tefas = Crawler()

    # ===== TEFAS =====
    try:
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        data = tefas.fetch(start=start_date)

        if not data.empty:
            data = data.sort_values("date")

            # Normal fonlar
            for code in FUNDS:
                df = data[data["code"] == code]
                if not df.empty:
                    results.append(f"{code}: {float(df.iloc[-1]['price']):.4f} TL")

            # ZBB (ZB* olarak yakala)
            zbb_df = data[data["code"].str.startswith("ZB")]
            if not zbb_df.empty:
                zbb_price = float(zbb_df.iloc[-1]["price"])
                results.append(f"ZBB: {zbb_price:.4f} TL")

    except Exception as e:
        results.append(f"TEFAS HATA: {e}")

    # ===== ALTIN.S1 =====
    try:
        import yfinance as yf

        df = yf.download("ALTINS1.IS", period="15d", progress=False)
        if df.empty:
            df = yf.download("ALTINS1", period="15d", progress=False)

        if not df.empty:
            price = df["Close"].dropna().iloc[-1]
            results.append(f"ALTIN.S1: {float(price):.4f} TL")

    except Exception as e:
        results.append(f"ALTIN HATA: {e}")

    # ===== DISCORD (DÜZ METİN) =====
    message = f"📈 Günlük Portföy ({TODAY})\n\n" + "\n".join(results)

    r = requests.post(WEBHOOK_URL, json={"content": message})
    print("Discord status:", r.status_code)

if __name__ == "__main__":
    main()
