import os
import requests
import pandas as pd
from tefas import Crawler
from datetime import datetime, timedelta
import yfinance as yf

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TEFAS_FUNDS = ["TTE", "ITP", "TZL"]
TODAY = datetime.now().strftime("%Y-%m-%d")
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
WEEK_AGO = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

def fetch_tefas_data():
    """TEFAS fonlarını çek"""
    results = []
    print("📊 TEFAS fonları çekiliyor...")
    
    try:
        tefas = Crawler()
        # Son 7 günün verisini çek (daha geniş aralık)
        data = tefas.fetch(start=WEEK_AGO, end=TODAY)
        
        # ZBB'yi de kontrol et
        all_funds = TEFAS_FUNDS + ["ZBB"]
        
        for fund in all_funds:
            fund_data = data[data['code'] == fund]
            if not fund_data.empty:
                # En son tarihi al
                latest = fund_data.sort_values('date', ascending=False).iloc[0]
                results.append({
                    "code": latest['code'], 
                    "price": float(latest['price']),
                    "date": latest['date']
                })
                print(f"  ✓ {fund}: {latest['price']:.4f} TL ({latest['date']})")
            else:
                print(f"  ✗ {fund}: TEFAS'ta bulunamadı")
                
    except Exception as e:
        print(f"  ✗ TEFAS hatası: {e}")
        import traceback
        traceback.print_exc()
    
    return results

def fetch_yfinance_symbol(symbol, name):
    """yfinance'den sembol çek"""
    try:
        print(f"  Deneniyor: {symbol}")
        df = yf.download(symbol, period="5d", progress=False, timeout=15)
        
        if df.empty:
            print(f"    ✗ Veri boş")
            return None
            
        price = float(df['Close'].iloc[-1])
        date = df.index[-1].strftime('%Y-%m-%d')
        
        print(f"    ✓ Başarılı: {price:.4f} TL ({date})")
        return {"code": name, "price": price, "date": date, "symbol": symbol}
        
    except Exception as e:
        print(f"    ✗ Hata: {str(e)[:70]}")
        return None

def fetch_zbb():
    """ZBB'yi farklı kaynaklardan dene"""
    print("\n📈 ZBB çekiliyor...")
    
    # Önce TEFAS'tan bakalım (belki vardır)
    try:
        tefas = Crawler()
        data = tefas.fetch(start=WEEK_AGO, end=TODAY)
        zbb_data = data[data['code'] == 'ZBB']
        
        if not zbb_data.empty:
            latest = zbb_data.sort_values('date', ascending=False).iloc[0]
            print(f"  ✓ ZBB TEFAS'ta bulundu: {latest['price']:.4f} TL")
            return {"code": "ZBB", "price": float(latest['price']), "date": latest['date']}
    except Exception as e:
        print(f"  TEFAS'ta arama hatası: {e}")
    
    # BIST'ten dene
    zbb_symbols = [
        ("ZBB.IS", "ZBB"),
        ("ZPBBB.IS", "ZBB"),  # Alternatif ticker
    ]
    
    for symbol, name in zbb_symbols:
        result = fetch_yfinance_symbol(symbol, name)
        if result:
            return result
    
    print("  ⚠️ ZBB hiçbir kaynaktan alınamadı")
    return None

def fetch_gold():
    """Altın fiyatını çek"""
    print("\n🥇 Altın çekiliyor...")
    
    gold_symbols = [
        ("GLDGR.IS", "ALTIN.S1", 2000, 4000),  # Gram altın, beklenen aralık
        ("ALTIN.IS", "ALTIN.S1", 2000, 4000),
        ("GAU.IS", "ALTIN.S1", 2000, 4000),
        ("XAU=F", "ALTIN.S1", 2000, 2800),      # Uluslararası
        ("GC=F", "ALTIN.S1", 2000, 2800),       # Gold futures
    ]
    
    for symbol, name, min_price, max_price in gold_symbols:
        result = fetch_yfinance_symbol(symbol, name)
        if result:
            price = result['price']
            # Fiyat makul aralıkta mı?
            if min_price <= price <= max_price:
                print(f"    ✓ Fiyat geçerli: {price:.2f} TL")
                return result
            else:
                print(f"    ⚠️ Fiyat aralık dışı: {price:.2f} TL (Beklenen: {min_price}-{max_price})")
                continue
    
    # Hiçbiri çalışmadıysa manuel API dene
    print("  Alternatif API deneniyor...")
    try:
        # Doviz.com API (public)
        response = requests.get("https://api.genelpara.com/embed/altin.json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'GA' in data:
                price = float(data['GA']['satis'])
                print(f"    ✓ API'den alındı: {price:.2f} TL")
                return {"code": "ALTIN.S1", "price": price, "date": TODAY, "symbol": "API"}
    except Exception as e:
        print(f"    ✗ API hatası: {e}")
    
    print("  ⚠️ Altın hiçbir kaynaktan alınamadı")
    return None

def main():
    results = []
    
    # 1. TEFAS fonları
    tefas_results = fetch_tefas_data()
    results.extend(tefas_results)
    
    # 2. ZBB
    zbb_result = fetch_zbb()
    if zbb_result:
        # ZBB zaten TEFAS'tan geldiyse tekrar ekleme
        if not any(r['code'] == 'ZBB' for r in results):
            results.append(zbb_result)
    
    # 3. Altın
    gold_result = fetch_gold()
    if gold_result:
        results.append(gold_result)
    
    # 4. Discord'a gönder
    print(f"\n📤 Discord'a gönderiliyor...")
    if results:
        send_to_discord(results)
        print(f"✅ {len(results)} ürün başarıyla gönderildi!")
        
        print("\n📋 Özet:")
        for item in results:
            symbol_info = f" [{item.get('symbol', 'TEFAS')}]" if 'symbol' in item else ""
            print(f"  • {item['code']}: {item['price']:.4f} TL{symbol_info}")
    else:
        print("❌ Hiç veri bulunamadı!")

def send_to_discord(data):
    fields = []
    for item in sorted(data, key=lambda x: x['code']):
        # Kaynak bilgisi ekle
        source = ""
        if 'symbol' in item:
            source = f"\n_{item['symbol']}_"
        elif 'date' in item:
            source = f"\n_{item['date']}_"
            
        fields.append({
            "name": f"🔹 {item['code']}",
            "value": f"**Fiyat:** {item['price']:.4f} TL{source}",
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
