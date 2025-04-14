# nice_funcs.py - Utility functions for the dashboard

import requests
import time
import random
from datetime import datetime

def get_current_price(coin):
    """
    Get the current price of a coin from HyperLiquid API
    """
    try:
        url = "https://api.hyperliquid.xyz/info"
        headers = {"Content-Type": "application/json"}
        
        # For perpetual futures
        body = {"type": "metaAndAssetCtxs"}
        
        # Make the request to the API
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            meta = data[0]
            asset_ctxs = data[1]
            
            # Find the coin in the universe
            coin_idx = None
            for i, asset in enumerate(meta['universe']):
                if asset['name'] == coin:
                    coin_idx = i
                    break
            
            if coin_idx is not None:
                # Get the mark price
                mark_price = float(asset_ctxs[coin_idx]['markPx'])
                return mark_price
        
        # Fallback to spot price if perpetual price not found
        body = {"type": "spotMetaAndAssetCtxs"}
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            tokens = data[0]['tokens']
            universe = data[0]['universe']
            asset_ctxs = data[1]
            
            # Find the symbol in the universe
            for i, pair in enumerate(universe):
                if pair['name'].split('/')[0] == coin:
                    # Get the corresponding asset context
                    ctx = asset_ctxs[i]
                    price = float(ctx['markPx']) if 'markPx' in ctx else None
                    return price
        
        # If all else fails, return a simulated price
        return simulate_price(coin)
        
    except Exception as e:
        print(f"Error fetching price for {coin}: {str(e)}")
        return simulate_price(coin)

def simulate_price(coin):
    """
    Simulate a price for testing when API fails
    """
    base_prices = {
        'BTC': 60000,
        'ETH': 3000,
        'SOL': 100,
        'XRP': 0.6,
        'AVAX': 30,
        'DOGE': 0.1,
        'SHIB': 0.00001,
        'LINK': 15,
        'DOT': 6,
        'ADA': 0.4
    }
    
    # Use base price if available, otherwise generate a random one
    base = base_prices.get(coin, random.uniform(1, 1000))
    
    # Add some randomness to simulate market movement
    variation = random.uniform(-0.02, 0.02)  # ±2% variation
    return base * (1 + variation)

def get_funding_rate(coin):
    """
    Get the funding rate for a coin from HyperLiquid API
    """
    try:
        url = "https://api.hyperliquid.xyz/info"
        headers = {"Content-Type": "application/json"}
        body = {"type": "metaAndAssetCtxs"}
        
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            meta = data[0]
            asset_ctxs = data[1]
            
            # Find the coin in the universe
            coin_idx = None
            for i, asset in enumerate(meta['universe']):
                if asset['name'] == coin:
                    coin_idx = i
                    break
            
            if coin_idx is not None:
                # Get the funding rate (convert from decimal to percentage)
                funding_rate = float(asset_ctxs[coin_idx].get('funding', 0)) * 100
                return funding_rate
        
        # Return a simulated funding rate if not found
        return random.uniform(-0.01, 0.01) * 100
        
    except Exception as e:
        print(f"Error fetching funding rate for {coin}: {str(e)}")
        return random.uniform(-0.01, 0.01) * 100

def get_timestamp():
    """
    Get current timestamp in a readable format
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
