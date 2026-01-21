import os
import requests
import pandas as pd
from tefas import Crawler
from datetime import datetime, timedelta

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
# Ziraat ve diger fonlarin
FUNDS = ["TTE", "ITP", "ZBB", "TZL"]
TODAY = datetime.now().strftime("%Y-%m-%d")
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
WEEK_AGO = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

def main():
    tefas = Crawler()
    results = []

    # 1. TEFAS FONLARI (TTE, ITP, ZBB, TZL)
    try:
        # Son 7 günün verisini çek (daha geniş aralık)
        print(f"TEFAS verisi çekiliyor: {WEEK_AGO} - {TODAY}")
        data = tefas.fetch(start=WEEK_AGO, end=TODAY)
        
        print(f"Toplam {len(data)} kayıt geldi")
        
        # Tüm ZBB içeren fonları bul
        zbb_check = data[data['code'].str.contains('ZBB', case=False, na=False)]
        print(f"\n🔍 ZBB araması - Bulunan: {len(zbb_check)} adet")
        if not zbb_check.empty:
            print(zbb_check[['code', 'title']].drop_duplicates().to_string())
        
        # Her fon için en son fiyatı al
        for fund in FUNDS:
            fund_data = data[data['code'] == fund]
            if not fund_data.empty:
                # En son tarihi al
                latest = fund_data.sort_values('date', ascending=False).iloc[0]
                results.append({
                    "code": latest['code'], 
                    "price": float(latest['price']),
                    "date": latest['date']
                })
                print(f"✓ {fund}: {latest['price']} TL ({latest['date']})")
            else:
                print(f"✗ {fund}: Veri bulunamadı!")
                
                # ZBB için özel arama
                if fund == "ZBB":
                    # Alternatif kodlar
                    alternatives = ["ZPK", "ZRHBBB", "ZRH", "ZRHBBF"]
                    for alt in alternatives:
                        alt_data = data[data['code'] == alt]
                        if not alt_data.empty:
                            latest = alt_data.sort_values('date', ascending=False).iloc[0]
                            results.append({
                                "code": f"ZBB ({alt})", 
                                "price": float(latest['price']),
                                "date": latest['date']
                            })
                            print(f"✓ ZBB alternatif bulundu: {alt}")
                            break
                    
    except Exception as e:
        print(f"TEFAS hatasi: {e}")
        import traceback
        traceback.print_exc()

    # 2. ALTIN.S1 (Tüm olası formatlar)
    altin_symbols = [
        "GLDGR.IS",      # Gram Altın
        "ALTIN.IS",      
        "ALTINS1.IS",    
        "GAU.IS",        # Gram Altın ETF
        "TRYXAU",        # TRY/XAU
    ]
    
    print("\n🔍 Altın fiyatı aranıyor...")
    for symbol in altin_symbols:
        try:
            import yfinance as yf
            print(f"  Deneniyor: {symbol}")
            altin_df = yf.download(symbol, period="5d", progress=False, timeout=10)
            
            if not altin_df.empty and len(altin_df) > 0:
                price = float(altin_df['Close'].iloc[-1])
                date = altin_df.index[-1].strftime('%Y-%m-%d')
                
                # Fiyat mantıklı mı kontrol et (gram altın 2000-5000 TL arası olmalı)
                if 1000 < price < 10000:
                    results.append({
                        "code": f"ALTIN.S1 ({symbol})", 
                        "price": price,
                        "date": date
                    })
                    print(f"✓ Altın bulundu: {symbol} = {price:.2f} TL")
                    break
                else:
                    print(f"  ⚠️ Fiyat şüpheli: {price}")
        except Exception as e:
            print(f"  ✗ {symbol} hata: {str(e)[:50]}")
            continue
    
    # Altın hiç bulunamadıysa manuel ekleme talimatı
    if not any("ALTIN" in r['code'] for r in results):
        print("\n⚠️ Altın otomatik alınamadı. Manuel fiyat girmek için:")
        print("   results.append({'code': 'ALTIN.S1', 'price': MANUEL_FIYAT, 'date': TODAY})")

    # 3. DISCORD'A GONDER
    print(f"\n📤 Discord'a gönderiliyor: {len(results)} ürün")
    if results:
        send_to_discord(results)
        print("✓ Gönderim başarılı")
    else:
        print("⚠️ Hiç veri bulunamadı, Discord'a gönderim yapılmadı!")

def send_to_discord(data):
    fields = []
    for item in sorted(data, key=lambda x: x['code']):
        # Tarih bilgisi varsa ekle
        date_info = f" ({item.get('date', 'tarih yok')})" if 'date' in item else ""
        fields.append({
            "name": f"🔹 {item['code']}",
            "value": f"**Fiyat:** {item['price']:.4f} TL{date_info}",
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
