#!/usr/bin/env python3
"""
Telegram Crypto Price Bot
Fetches cryptocurrency prices and sends updates to Telegram
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CryptoPriceBot:
    def __init__(self, telegram_token: str, chat_id: str, cache_file: str = "price_cache.json"):
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.cache_file = cache_file
        self.telegram_url = f"https://api.telegram.org/bot{telegram_token}"
        
        # Default cryptocurrencies to track (can be modified)
        self.default_coins = [
            "bitcoin",      # BTC  
            "ethereum",     # ETH
            "solana",       # SOL
            "cardano",      # ADA
            "dogecoin",     # DOGE
            "monero",       # XMR - NUEVO
            "ripple",       # XRP - NUEVO
            "litecoin"      # LTC - NUEVO
        ]
        
    def send_telegram_message(self, message: str) -> bool:
        """Send message to Telegram chat"""
        try:
            url = f"{self.telegram_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Message sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def fetch_price_data(self, coin_id: str) -> Optional[Dict]:
        """Fetch current price and historical data from CoinGecko"""
        try:
            # CoinGecko API endpoint
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; CryptoBot/1.0)"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            market_data = data.get("market_data", {})
            current_price = market_data.get("current_price", {}).get("usd")
            
            # Get price changes
            price_change_1h = market_data.get("price_change_percentage_1h_in_currency", {}).get("usd")
            price_change_24h = market_data.get("price_change_percentage_24h")
            price_change_7d = market_data.get("price_change_percentage_7d")
            
            # Get historical prices for 7 days ago (as fallback if API doesn't provide)
            if price_change_7d is None:
                historical_price = self.fetch_historical_price(coin_id, 7)
                if historical_price and current_price:
                    price_change_7d = ((current_price - historical_price) / historical_price) * 100
            
            return {
                "name": data.get("name", coin_id.title()),
                "symbol": data.get("symbol", coin_id[:3]).upper(),
                "current_price": current_price,
                "price_change_1h": price_change_1h,
                "price_change_24h": price_change_24h,
                "price_change_7d": price_change_7d,
                "last_updated": market_data.get("last_updated"),
                "market_cap": market_data.get("market_cap", {}).get("usd"),
                "volume_24h": market_data.get("total_volume", {}).get("usd")
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {coin_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing data for {coin_id}: {e}")
            return None
    
    def fetch_historical_price(self, coin_id: str, days_ago: int) -> Optional[float]:
        """Fetch historical price from X days ago"""
        try:
            # Calculate date for X days ago
            date = (datetime.now() - timedelta(days=days_ago)).strftime("%d-%m-%Y")
            
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
            params = {
                "date": date,
                "localization": "false"
            }
            
            headers = {"User-Agent": "Mozilla/5.0 (compatible; CryptoBot/1.0)"}
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            market_data = data.get("market_data", {})
            return market_data.get("current_price", {}).get("usd")
            
        except Exception as e:
            logger.error(f"Failed to fetch historical price for {coin_id}: {e}")
            return None

    def fetch_monero_price(self) -> Optional[Dict]:
    """Fetch Monero price specifically using /simple/price endpoint"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "monero",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_7d_change": "true"
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "monero" in data:
            return {
                "name": "Monero",
                "symbol": "xmr",
                "current_price": data["monero"].get("usd"),
                "price_change_1h": None,  # 1h no disponible en simple/price
                "price_change_24h": data["monero"].get("usd_24h_change"),
                "price_change_7d": data["monero"].get("usd_7d_change")
            }
        return None
    except Exception as e:
        logger.error(f"Failed to fetch Monero: {e}")
        return None
    
    def format_price_message(self, coin_data: Dict) -> str:
        """Format price data into a nice Telegram message"""
        if not coin_data or not coin_data.get("current_price"):
            return f"❌ <b>{coin_data.get('name', 'Unknown')}</b>: Failed to fetch data"
        
        # Format price with appropriate decimals
        price = coin_data["current_price"]
        if price < 0.01:
            price_str = f"${price:.8f}"
        elif price < 1:
            price_str = f"${price:.4f}"
        else:
            price_str = f"${price:,.2f}"
        
        # Format percentage changes with colors
        def format_change(change):
            if change is None:
                return "N/A"
            symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            color = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
            return f"{color} {symbol} {change:+.2f}%"
        
        message = f"""
<b>💰 {coin_data['name']} ({coin_data['symbol'].upper()})</b>
<b>Price:</b> {price_str}

<b>📊 Changes:</b>
• 1h: {format_change(coin_data.get('price_change_1h'))}
• 24h: {format_change(coin_data.get('price_change_24h'))}
• 7d: {format_change(coin_data.get('price_change_7d'))}
"""
        
        # Add market cap if available
        if coin_data.get("market_cap"):
            market_cap = coin_data["market_cap"]
            if market_cap > 1_000_000_000:
                market_cap_str = f"${market_cap / 1_000_000_000:.2f}B"
            elif market_cap > 1_000_000:
                market_cap_str = f"${market_cap / 1_000_000:.2f}M"
            else:
                market_cap_str = f"${market_cap:,.0f}"
            message += f"\n<b>Market Cap:</b> {market_cap_str}"
        
        return message.strip()
    
    def save_to_cache(self, data: Dict) -> None:
        """Save current prices to cache file for reference"""
        try:
            cache = {
                "timestamp": datetime.now().isoformat(),
                "prices": data
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            logger.info(f"Saved {len(data)} coins to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def run(self, coins: Optional[List[str]] = None) -> bool:
    if coins is None:
        coins = self.default_coins
    
    logger.info(f"Fetching prices for {len(coins)} cryptocurrencies...")
    
    successful = 0
    messages = []
    
    for coin in coins:
        logger.info(f"Fetching data for {coin}...")
        
        # Monero necesita tratamiento especial
        if coin == "monero":
            data = self.fetch_monero_price()
        else:
            data = self.fetch_price_data(coin)
        
        if data and data.get("current_price"):
            message = self.format_price_message(data)
            messages.append(message)
            successful += 1
            logger.info(f"✓ Successfully fetched {coin}")
        else:
            messages.append(f"❌ Failed to fetch data for {coin}")
            logger.error(f"✗ Failed to fetch {coin}")
        
        import time
        time.sleep(1)
    
    # ... resto del código igual
        
        # Combine all messages
        full_message = "🚀 <b>Crypto Price Update</b>\n" + "-" * 30 + "\n\n"
        full_message += "\n\n" + "-" * 30 + "\n\n".join(messages)
        full_message += f"\n\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        # Send the combined message
        success = self.send_telegram_message(full_message)
        
        if success:
            logger.info(f"Successfully sent {successful}/{len(coins)} prices")
        else:
            logger.error("Failed to send message")
        
        return success

def main():
    """Main entry point"""
    # Get configuration from environment variables
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not telegram_token or not chat_id:
        logger.error("Missing required environment variables")
        logger.error("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
        sys.exit(1)
    
    # Optional: Get custom coins from environment
    custom_coins = os.getenv("CRYPTO_COINS")
    coins = None
    if custom_coins:
        coins = [coin.strip().lower() for coin in custom_coins.split(",")]
        logger.info(f"Using custom coin list: {coins}")
    
    try:
        bot = CryptoPriceBot(telegram_token, chat_id)
        success = bot.run(coins)
        
        if success:
            logger.info("Bot execution completed successfully")
            sys.exit(0)
        else:
            logger.error("Bot execution failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
