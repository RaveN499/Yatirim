import os
import requests
import pandas as pd
from tefas import Crawler
from datetime import datetime, timedelta

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
# TEFAS'ta aktif fonlar
TEFAS_FUNDS = ["TTE", "ITP", "TZL"]
# ZBB artık TEFAS'ta işlem görmüyor, yfinance'den alınacak
BIST_SYMBOLS = {
    "ZBB": "ZBB.IS",  # Ziraat Portföy BIST 30
    "ALTIN": ["GLDGR.IS", "ALTIN.IS", "GAU.IS"]  # Altın alternatifleri
}

TODAY = datetime.now().strftime("%Y-%m-%d")
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def main():
    results = []

    # 1. TEFAS FONLARI (TTE, ITP, TZL)
    print("📊 TEFAS fonları çekiliyor...")
    try:
        tefas = Crawler()
        data = tefas.fetch(start=TODAY)
        if data.empty or not any(f in data['code'].values for f in TEFAS_FUNDS):
            print("  ⏳ Bugünün verisi eksik, dünün verisi çekiliyor...")
            data = tefas.fetch(start=YESTERDAY)
        
        filtered = data[data['code'].isin(TEFAS_FUNDS)]
        for _, row in filtered.iterrows():
            results.append({"code": row['code'], "price": float(row['price'])})
            print(f"  ✓ {row['code']}: {row['price']:.4f} TL")
    except Exception as e:
        print(f"  ✗ TEFAS hatası: {e}")

    # 2. ZBB - BIST üzerinden
    print("\n📈 ZBB (BIST 30 ETF) çekiliyor...")
    try:
        import yfinance as yf
        zbb_ticker = BIST_SYMBOLS["ZBB"]
        print(f"  Deneniyor: {zbb_ticker}")
        
        zbb_df = yf.download(zbb_ticker, period="5d", progress=False, timeout=10)
        if not zbb_df.empty:
            price = float(zbb_df['Close'].iloc[-1])
            results.append({"code": "ZBB", "price": price})
            print(f"  ✓ ZBB: {price:.4f} TL")
        else:
            print(f"  ✗ ZBB verisi boş döndü")
    except Exception as e:
        print(f"  ✗ ZBB hatası: {e}")

    # 3. ALTIN - Farklı semboller deneniyor
    print("\n🥇 Altın fiyatı çekiliyor...")
    altin_symbols = BIST_SYMBOLS["ALTIN"]
    
    for symbol in altin_symbols:
        try:
            import yfinance as yf
            print(f"  Deneniyor: {symbol}")
            
            altin_df = yf.download(symbol, period="5d", progress=False, timeout=10)
            if not altin_df.empty:
                price = float(altin_df['Close'].iloc[-1])
                
                # Fiyat kontrolü (gram altın 1500-6000 TL arası olmalı)
                if 1500 < price < 6000:
                    results.append({"code": "ALTIN.S1", "price": price})
                    print(f"  ✓ ALTIN.S1: {price:.4f} TL ({symbol})")
                    break
                else:
                    print(f"  ⚠️ Fiyat aralık dışı: {price:.2f} TL")
        except Exception as e:
            print(f"  ✗ {symbol} hatası: {str(e)[:60]}")
            continue
    
    if not any("ALTIN" in r['code'] for r in results):
        print("  ⚠️ Altın hiçbir kaynaktan alınamadı!")

    # 4. DISCORD'A GONDER
    print(f"\n📤 Discord'a gönderiliyor...")
    if results:
        send_to_discord(results)
        print(f"✅ {len(results)} ürün başarıyla gönderildi!")
        
        # Özet
        print("\n📋 Gönderilen veriler:")
        for item in results:
            print(f"  • {item['code']}: {item['price']:.4f} TL")
    else:
        print("❌ Hiç veri bulunamadı, Discord'a gönderim yapılmadı!")

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
