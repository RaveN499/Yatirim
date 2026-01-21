from tefas import Crawler
import pandas as pd
from datetime import datetime
import yfinance as yf

tefas = Crawler()
funds = ["TTE", "ITP", "ZPX", "TZL"]
today = datetime.now().strftime("%Y-%m-%d")

# 1. TEFAS Verilerini Çek
data = tefas.fetch(start=today, name=None) # Tüm fonları çekip sonra filtrelemek daha hızlı olabilir
my_funds_data = data[data['code'].isin(funds)][['date', 'code', 'price']]

# 2. ALTIN.S1 Verisini Çek
altin_s1 = yf.download("ALTINS1.IS", start=today)
if not altin_s1.empty:
    altin_price = altin_s1['Close'].iloc[-1]
    altin_row = pd.DataFrame([{'date': today, 'code': 'ALTIN.S1', 'price': altin_price}])
    my_funds_data = pd.concat([my_funds_data, altin_row], ignore_index=True)

# 3. Dosyaya Kaydet (Üstüne ekleyerek devam eder)
try:
    existing_df = pd.read_csv("portfolio_history.csv")
    final_df = pd.concat([existing_df, my_funds_data]).drop_duplicates()
    final_df.to_csv("portfolio_history.csv", index=False)
except FileNotFoundError:
    my_funds_data.to_csv("portfolio_history.csv", index=False)
