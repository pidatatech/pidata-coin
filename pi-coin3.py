import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def get_crypto_data(crypto_ids):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'ids': ','.join(crypto_ids),
        'order': 'market_cap_desc'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    crypto_list = []
    for coin in data:
        high_24h = coin['high_24h']
        low_24h = coin['low_24h']
        volatility = ((high_24h - low_24h) / low_24h) * 100
        
        if volatility > 5:
            vol_status = "HIGH"
        elif volatility > 2:
            vol_status = "MEDIUM"
        else:
            vol_status = "LOW"
        
        crypto_list.append({
            'symbol': coin['symbol'].upper(),
            'name': coin['name'],
            'price': coin['current_price'],
            'change_24h': coin['price_change_percentage_24h'],
            'market_cap': coin['market_cap'],
            'volatility': volatility,
            'vol_status': vol_status
        })
    
    return crypto_list

def get_fear_greed_index():
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url)
        data = response.json()
        value = int(data['data'][0]['value'])
        
        if value >= 75:
            sentiment = "Extreme Greed"
        elif value >= 55:
            sentiment = "Greed"
        elif value >= 45:
            sentiment = "Neutral"
        elif value >= 25:
            sentiment = "Fear"
        else:
            sentiment = "Extreme Fear"
        
        return value, sentiment
    except:
        return 50, "Neutral"

def get_forex_data(pairs):
    forex_list = []
    base_url = "https://api.exchangerate-api.com/v4/latest/"
    
    for pair in pairs:
        parts = pair.split('/')
        if len(parts) != 2:
            continue
        
        base, target = parts
        
        try:
            response = requests.get(f"{base_url}{base}")
            data = response.json()
            
            if target in data['rates']:
                rate = data['rates'][target]
                
                change = 0
                volatility = "Normal"
                
                forex_list.append({
                    'pair': pair,
                    'rate': rate,
                    'change': change,
                    'volatility': volatility
                })
        except:
            continue
    
    return forex_list

def generate_html_report(crypto_data, forex_data, fg_value, fg_sentiment):
    now = datetime.utcnow().strftime('%B %d, %Y')
    
    crypto_sorted = sorted(crypto_data, key=lambda x: x['change_24h'], reverse=True)
    top_gainers = [c for c in crypto_sorted if c['change_24h'] > 0][:3]
    top_losers = [c for c in crypto_sorted if c['change_24h'] < 0][-3:]
    high_vol_assets = [c for c in crypto_data if c['vol_status'] == 'HIGH']
    
    market_trend = "Bullish 📈" if fg_value > 50 else "Bearish 📉"
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }}
            .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; margin-bottom: 20px; }}
            .section {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background-color: #f8f9fa; padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6; font-size: 12px; }}
            td {{ padding: 10px; border-bottom: 1px solid #e9ecef; font-size: 13px; }}
            .positive {{ color: #28a745; font-weight: bold; }}
            .negative {{ color: #dc3545; font-weight: bold; }}
            .high-vol {{ background-color: #fff3cd; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
            .sentiment {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
            .alert-box {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 10px 0; }}
            .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🪙 Daily Crypto & Forex Market Report</h1>
            <p>{now}</p>
        </div>
        
        <div class="section">
            <h2>Market Sentiment</h2>
            <div class="sentiment">Fear & Greed Index: {fg_value} ({fg_sentiment})</div>
            <p><strong>Overall Market:</strong> {market_trend}</p>
        </div>
        
        <div class="section">
            <h2>Cryptocurrency Summary</h2>
            <table>
                <tr>
                    <th>Coin</th>
                    <th>Price</th>
                    <th>24h Change</th>
                    <th>Volatility</th>
                    <th>Market Cap</th>
                </tr>
    """
    
    for crypto in crypto_data:
        change_class = 'positive' if crypto['change_24h'] >= 0 else 'negative'
        change_sign = '+' if crypto['change_24h'] >= 0 else ''
        
        if crypto['market_cap'] >= 1_000_000_000:
            market_cap_str = f"${crypto['market_cap'] / 1_000_000_000:.1f}B"
        else:
            market_cap_str = f"${crypto['market_cap'] / 1_000_000:.1f}M"
        
        price_str = f"${crypto['price']:,.2f}" if crypto['price'] >= 1 else f"${crypto['price']:.4f}"
        
        vol_display = f"<span class='high-vol'>{crypto['vol_status']} ({crypto['volatility']:.1f}%)</span>" if crypto['vol_status'] == 'HIGH' else f"{crypto['vol_status']} ({crypto['volatility']:.1f}%)"
        
        html += f"""
                <tr>
                    <td><strong>{crypto['symbol']}</strong></td>
                    <td>{price_str}</td>
                    <td class="{change_class}">{change_sign}{crypto['change_24h']:.2f}%</td>
                    <td>{vol_display}</td>
                    <td>{market_cap_str}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
    """
    
    if top_gainers:
        html += """
        <div class="section">
            <h2>Top Crypto Gainers (24h)</h2>
            <table>
        """
        for crypto in top_gainers:
            price_str = f"${crypto['price']:,.2f}" if crypto['price'] >= 1 else f"${crypto['price']:.4f}"
            html += f"""
                <tr>
                    <td>🟢 <strong>{crypto['symbol']}</strong></td>
                    <td class="positive">+{crypto['change_24h']:.2f}%</td>
                    <td>{price_str}</td>
                </tr>
            """
        html += """
            </table>
        </div>
        """
    
    if top_losers:
        html += """
        <div class="section">
            <h2>Top Crypto Losers (24h)</h2>
            <table>
        """
        for crypto in top_losers:
            price_str = f"${crypto['price']:,.2f}" if crypto['price'] >= 1 else f"${crypto['price']:.4f}"
            html += f"""
                <tr>
                    <td>🔴 <strong>{crypto['symbol']}</strong></td>
                    <td class="negative">{crypto['change_24h']:.2f}%</td>
                    <td>{price_str}</td>
                </tr>
            """
        html += """
            </table>
        </div>
        """
    
    if forex_data:
        html += """
        <div class="section">
            <h2>Forex Market Overview</h2>
            <table>
                <tr>
                    <th>Pair</th>
                    <th>Rate</th>
                    <th>Change</th>
                    <th>Volatility</th>
                </tr>
        """
        for forex in forex_data:
            change_class = 'positive' if forex['change'] >= 0 else 'negative'
            change_sign = '+' if forex['change'] >= 0 else ''
            html += f"""
                <tr>
                    <td><strong>{forex['pair']}</strong></td>
                    <td>{forex['rate']:.4f}</td>
                    <td class="{change_class}">{change_sign}{forex['change']:.2f}%</td>
                    <td>{forex['volatility']}</td>
                </tr>
            """
        html += """
            </table>
        </div>
        """
    
    if high_vol_assets:
        html += """
        <div class="section">
            <h2>High Volatility Alert</h2>
            <div class="alert-box">
        """
        for asset in high_vol_assets:
            html += f"<p>⚠ <strong>{asset['symbol']}</strong>: {asset['volatility']:.1f}% daily range - expect large swings</p>"
        html += """
            </div>
        </div>
        """
    
    html += f"""
        <div class="footer">
            <p>Report generated at {datetime.utcnow().strftime('%I:%M %p')} UTC</p>
            <p>Markets trade 24/7 - This is educational content, not financial advice.</p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email_report(html_content, recipient_email):
    sender_email = os.getenv('SENDER_EMAIL', 'your_email@gmail.com')
    sender_password = os.getenv('SENDER_PASSWORD', 'your_app_password')
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🪙 Daily Crypto & Forex Report - {datetime.utcnow().strftime('%B %d, %Y')}"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

print("Crypto & Forex Market Report Generator")
print("=======================================\n")

crypto_input = input("Enter crypto IDs (comma-separated, or press Enter for default): ")
if not crypto_input.strip():
    crypto_ids = ['bitcoin', 'ethereum', 'solana', 'binancecoin', 'ripple']
else:
    crypto_ids = [c.strip().lower() for c in crypto_input.split(',')]

forex_input = input("Enter forex pairs (comma-separated, or press Enter for default): ")
if not forex_input.strip():
    forex_pairs = ['USD/EUR', 'USD/JPY', 'GBP/USD', 'USD/CHF']
else:
    forex_pairs = [f.strip().upper() for f in forex_input.split(',')]

recipient = input("Recipient email: ")

print("\nGenerating daily market report...\n")

crypto_data = get_crypto_data(crypto_ids)
print(f"✓ Fetched crypto data ({len(crypto_data)} coins)")

forex_data = get_forex_data(forex_pairs)
print(f"✓ Fetched forex data ({len(forex_data)} pairs)")

fg_value, fg_sentiment = get_fear_greed_index()
print(f"✓ Calculated Fear & Greed Index: {fg_value} ({fg_sentiment})")

high_vol = sum(1 for c in crypto_data if c['vol_status'] == 'HIGH')
print(f"✓ Identified {high_vol} high volatility assets")

html_report = generate_html_report(crypto_data, forex_data, fg_value, fg_sentiment)
print(f"✓ Generated HTML report ({len(html_report) / 1024:.1f} KB)")

print(f"✓ Sending email to {recipient}...\n")

if send_email_report(html_report, recipient):
    print("✅ Email sent successfully!\n")
    
    print("Report Summary:")
    print("─" * 45)
    print(f"Crypto Assets: {len(crypto_data)}")
    
    if crypto_data:
        top_gainer = max(crypto_data, key=lambda x: x['change_24h'])
        top_loser = min(crypto_data, key=lambda x: x['change_24h'])
        print(f"Top Gainer: {top_gainer['symbol']} (+{top_gainer['change_24h']:.2f}%)")
        print(f"Top Loser: {top_loser['symbol']} ({top_loser['change_24h']:.2f}%)")
    
    print(f"High Volatility Assets: {high_vol}")
    print(f"Market Sentiment: {fg_sentiment} ({fg_value})")
    
    next_report = datetime.utcnow().replace(hour=9, minute=0, second=0)
    print(f"\nNext report scheduled for: {next_report.strftime('%Y-%m-%d %I:%M %p UTC')}")
else:
    print("✗ Email failed. Check your .env configuration.")
