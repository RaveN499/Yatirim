import os
import requests
from datetime import datetime
import re

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TODAY = datetime.now().strftime("%Y-%m-%d")

# Fintables'tan çekilecek tüm ürünler
PRODUCTS = {
    "ITP": {"url": "https://fintables.com/fonlar/ITP", "name": "ITP"},
    "TTE": {"url": "https://fintables.com/fonlar/TTE", "name": "TTE"},
    "TZL": {"url": "https://fintables.com/fonlar/TZL", "name": "TZL"},
    "ZPX30": {"url": "https://fintables.com/fonlar/ZPX30", "name": "ZPX30"},
    "ALTIN.S1": {"url": "https://fintables.com/sertifikalar/ALTIN.S1", "name": "ALTIN.S1"},
    "GRAM_ALTIN": {"url": "https://fintables.com/emtia/altin", "name": "GRAM ALTIN"},
}

def fetch_from_fintables(url, name):
    """Fintables'tan veri çek"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://fintables.com/',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        if response.status_code == 200:
            html = response.text
            
            # Çoklu fiyat pattern'leri (Fintables'ın farklı sayfaları için)
            patterns = [
                r'<span[^>]*class="[^"]*price[^"]*"[^>]*>[\s]*([0-9.,]+)[\s]*</span>',
                r'data-price="([0-9.,]+)"',
                r'"price"[:\s]+([0-9.,]+)',
                r'"lastPrice"[:\s]+([0-9.,]+)',
                r'Fiyat[^0-9]*([0-9.,]+)',
                r'Son Fiyat[^0-9]*([0-9.,]+)',
                r'class="text-[^"]*"[^>]*>([0-9.,]+)</.*?>.*?TL',
                r'>([0-9.,]+)\s*₺',
                r'>([0-9.,]+)\s*TL',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                if matches:
                    # İlk bulunan sayıyı al
                    price_str = matches[0].replace(',', '.')
                    # Binlik ayraç varsa düzelt
                    if price_str.count('.') > 1:
                        price_str = price_str.replace('.', '', price_str.count('.')-1)
                    
                    try:
                        price = float(price_str)
                        # Mantıklı fiyat kontrolü
                        if 0.01 < price < 100000:
                            return price
                    except ValueError:
                        continue
            
            print(f"    ⚠️ HTML'de fiyat bulunamadı, ilk 500 karakter:")
            print(f"    {html[:500]}...")
        else:
            print(f"    ✗ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"    ✗ Hata: {str(e)[:70]}")
    
    return None

def main():
    results = []
    
    print("🌐 Fintables'tan tüm veriler çekiliyor...\n")
    
    for code, info in PRODUCTS.items():
        print(f"📊 {info['name']} çekiliyor...")
        print(f"   URL: {info['url']}")
        
        price = fetch_from_fintables(info['url'], info['name'])
        
        if price:
            results.append({
                "code": info['name'],
                "price": price,
                "source": "Fintables"
            })
            print(f"   ✓ {info['name']}: {price:.4f} TL\n")
        else:
            print(f"   ✗ {info['name']}: Alınamadı\n")
    
    # Sonuçları göster ve Discord'a gönder
    print(f"{'='*60}")
    if results:
        print(f"✅ {len(results)}/{len(PRODUCTS)} ürün bulundu")
        send_to_discord(results)
        
        print("\n📋 Özet:")
        for item in sorted(results, key=lambda x: x['code']):
            print(f"  • {item['code']}: {item['price']:.4f} TL")
    else:
        print("❌ Hiç veri bulunamadı!")
        print("\nℹ️  Fintables siteye erişim engellenmiş olabilir.")
        print("   Alternatif: TEFAS + Ziraat Portföy kombinasyonunu kullanın.")

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
            "footer": {"text": "Fintables - Ziraat & Midas Yatırım Takibi"}
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
