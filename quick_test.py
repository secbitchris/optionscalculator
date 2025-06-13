import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.environ.get('POLYGON_API_KEY')
print(f'🔑 Testing new API key: {api_key[:8]}...{api_key[-4:]}')

# Quick SPY test
url = f'https://api.polygon.io/v2/aggs/ticker/SPY/prev?adjusted=true&apikey={api_key}'
response = requests.get(url, timeout=10)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    if 'results' in data and data['results']:
        close = data['results'][0].get('c', 'Unknown')
        print(f'✅ SPY Previous Close: ${close}')
    else:
        print('✅ API works but no data')
else:
    print(f'❌ Error: {response.text[:100]}') 