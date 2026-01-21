import os
import requests
import pandas as pd
from tefas import Crawler
from datetime import datetime, timedelta
import re

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TEFAS_FUNDS = ["TTE", "ITP", "TZL"]
TODAY = datetime.now().strftime("%Y-%m-%d")
WEEK_AGO = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

def fetch_tefas_data():
    """TEFAS fonlarını çek"""
    results = []
    print("📊 TEFAS fonları çekiliyor...")
    
    try:
        tefas = Crawler()
        data = tefas.fetch(start=WEEK_AGO, end=TODAY)
        
        for fund in TEFAS_FUNDS:
            fund_data = data[data['code'] == fund]
            if not fund_data.empty:
                latest = fund_data.sort_values('date', ascending=False).iloc[0]
                results.append({
                    "code": fund, 
                    "price": float(latest['price']),
                    "source": "TEFAS"
                })
                print(f"  ✓ {fund}: {latest['price']:.4f} TL")
            else:
                print(f"  ✗ {fund}: Bulunamadı")
                
    except Exception as e:
        print(f"  ✗ TEFAS hatası: {e}")
    
    return results

def fetch_from_ziraat_portfoy():
    """Ziraat Portföy sitesinden ZPX30 ve Altın verilerini çek"""
    print("\n🏦 Ziraat Portföy sitesinden veri çekiliyor...")
    results = []
    
    try:
        url = "https://www.ziraatportfoy.com.tr/tr"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            html = response.text
            
            # ZPX30
            zpx30_match = re.search(r'ZPX30[^0-9]*([0-9,\.]+)', html)
            if zpx30_match:
                price_str = zpx30_match.group(1).replace(',', '.')
                # Eğer nokta binlik ayracıysa düzelt
                if price_str.count('.') > 1:
                    price_str = price_str.replace('.', '', price_str.count('.')-1)
                price = float(price_str)
                results.append({
                    "code": "ZPX30",
                    "price": price,
                    "source": "Ziraat Portföy"
                })
                print(f"  ✓ ZPX30: {price:.4f} TL")
            else:
                print(f"  ✗ ZPX30 bulunamadı")
            
            # ALTIN GRAM - Piyasa fiyatı
            altin_gram_match = re.search(r'ALTIN GRAM - TL[^0-9]*([0-9,\.]+)', html)
            if altin_gram_match:
                price_str = altin_gram_match.group(1).replace(',', '.')
                if price_str.count('.') > 1:
                    price_str = price_str.replace('.', '', price_str.count('.')-1)
                price = float(price_str)
                results.append({
                    "code": "ALTIN GRAM",
                    "price": price,
                    "source": "Ziraat Portföy"
                })
                print(f"  ✓ ALTIN GRAM: {price:.4f} TL")
            else:
                print(f"  ✗ ALTIN GRAM bulunamadı")
            
            # ZGOLD (Altın Katılım Fonu) - 10 gram fiyatı
            zgold_match = re.search(r'ZGOLD[^0-9]*([0-9,\.]+)', html)
            if zgold_match:
                price_str = zgold_match.group(1).replace(',', '.')
                if price_str.count('.') > 1:
                    price_str = price_str.replace('.', '', price_str.count('.')-1)
                price = float(price_str)
                
                # ZGOLD 10 gram altın fiyatı olduğu için gram fiyatına çevir
                gram_price = price / 10
                results.append({
                    "code": "ZGOLD (Gram)",
                    "price": gram_price,
                    "source": "Ziraat (ZGOLD÷10)"
                })
                print(f"  ✓ ZGOLD: {price:.4f} TL (Gram: {gram_price:.4f} TL)")
            else:
                print(f"  ✗ ZGOLD bulunamadı")
                
        else:
            print(f"  ✗ HTTP hatası: {response.status_code}")
            
    except Exception as e:
        print(f"  ✗ Ziraat Portföy hatası: {e}")
        import traceback
        traceback.print_exc()
    
    return results

def fetch_altin_s1():
    """ALTIN.S1 (Midas altın fonu) fiyatını çek"""
    print("\n💰 ALTIN.S1 (Midas) fiyatı çekiliyor...")
    
    # 1. yfinance ile dene
    try:
        import yfinance as yf
        symbols = ["ALTINS1.IS", "GLDGR.IS", "ALTIN.IS"]
        
        for symbol in symbols:
            try:
                print(f"  yfinance: {symbol}")
                df = yf.download(symbol, period="5d", progress=False, timeout=10)
                if not df.empty:
                    price = float(df['Close'].iloc[-1])
                    # ALTIN.S1 genelde 60-90 TL arası (10 gram)
                    if 50 < price < 100:
                        print(f"    ✓ {price:.4f} TL")
                        return {"code": "ALTIN.S1", "price": price, "source": symbol}
            except Exception as e:
                print(f"    ✗ {str(e)[:50]}")
                continue
    except Exception as e:
        print(f"  yfinance hatası: {e}")
    
    print("  ⚠️ ALTIN.S1 bulunamadı")
    return None

def main():
    results = []
    
    # 1. TEFAS fonları (TTE, ITP, TZL)
    tefas_results = fetch_tefas_data()
    results.extend(tefas_results)
    
    # 2. Ziraat Portföy'den ZPX30, ALTIN GRAM ve ZGOLD
    ziraat_results = fetch_from_ziraat_portfoy()
    results.extend(ziraat_results)
    
    # 3. ALTIN.S1 (Midas altın fonu)
    altin_s1_result = fetch_altin_s1()
    if altin_s1_result:
        results.append(altin_s1_result)
    
    # 4. Discord'a gönder
    print(f"\n{'='*60}")
    if results:
        print(f"✅ {len(results)} ürün bulundu")
        send_to_discord(results)
        
        print("\n📋 Özet:")
        for item in results:
            print(f"  • {item['code']}: {item['price']:.4f} TL [{item['source']}]")
    else:
        print("❌ Hiç veri bulunamadı!")

def send_to_discord(data):
    fields = []
    for item in sorted(data, key=lambda x: x['code']):
        # Kaynak bilgisini sadece TEFAS dışındakiler için göster
        source_text = ""
        if item['source'] != 'TEFAS':
            source_text = f"\n_{item['source']}_"
            
        fields.append({
            "name": f"🔹 {item['code']}",
            "value": f"**Fiyat:** {item['price']:.4f} TL{source_text}",
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
        print("📤 Discord'a gönderildi!")
    except Exception as e:
        print(f"❌ Discord hatası: {e}")

if __name__ == "__main__":
    main()
