import os
import time
import pandas as pd
import numpy as np
from datetime import datetime
import colorama
from colorama import Fore, Back, Style
import nice_funcs as n  # Import directly from the same directory
import argparse
import sys
import traceback
import random
from termcolor import colored
import schedule  # Add import for scheduler
import requests

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from api import MoonDevAPI  # Import MoonDevAPI from the root directory

# Initialize colorama for terminal colors
colorama.init(autoreset=True)

# Configure pandas to display numbers with commas and no scientific notation
pd.set_option('display.float_format', '{:.2f}'.format)  # No dollar sign
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# Nomad DevOPS ASCII Art Banner
NOMAD_BANNER_ALT = f"""
{Fore.CYAN}
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                         ┃
┃  ███╗   ██╗ ██████╗ ███╗   ███╗ █████╗ ██████╗                         ┃
┃  ████╗  ██║██╔═══██╗████╗ ████║██╔══██╗██╔══██╗                        ┃
┃  ██╔██╗ ██║██║   ██║██╔████╔██║███████║██║  ██║                        ┃
┃  ██║╚██╗██║██║   ██║██║╚██╔╝██║██╔══██║██║  ██║                        ┃
┃  ██║ ╚████║╚██████╔╝██║ ╚═╝ ██║██║  ██║██████╔╝                        ┃
┃  ╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═════╝                         ┃
┃                                                                         ┃
{Fore.MAGENTA}
┃  ██████╗ ███████╗██╗   ██╗      ██████╗ ██████╗ ███████╗               ┃
┃  ██╔══██╗██╔════╝██║   ██║     ██╔═══██╗██╔══██╗██╔════╝               ┃
┃  ██║  ██║█████╗  ██║   ██║     ██║   ██║██████╔╝███████╗               ┃
┃  ██║  ██║██╔══╝  ╚██╗ ██╔╝     ██║   ██║██╔═══╝ ╚════██║               ┃
┃  ██████╔╝███████╗ ╚████╔╝      ╚██████╔╝██║     ███████║               ┃
┃  ╚═════╝ ╚══════╝  ╚═══╝        ╚═════╝ ╚═╝     ╚══════╝               ┃
┃                                                                         ┃
{Fore.YELLOW}
┃  🚀 ₿ Hyperliquid Position Tracker API Edition 🌙 Ξ                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
{Style.RESET_ALL}
"""

# Fun Nomad DevOPS quotes
NOMAD_QUOTES = [
    "Tracking whales like a boss! 🐋",
    "Liquidations incoming... maybe! 💥",
    "Nomad DevOPS - making data fun again! 📊",
    "To the moon! 🚀 (not financial advice)",
    "Who needs sleep when you have APIs? 😴",
    "Whales move markets, so track the whales! 🐳",
    "Nomad sees all the positions... 👀",
    "Diamond hands or liquidation lands? 💎",
    "Watch the whales, follow the money! 💰",
    "API-powered alpha at your fingertips! ✨"
]

# ===== CONFIGURATION =====
DATA_DIR = "bots/hyperliquid/data/ppls_positions"  # Directory path, not file path
MIN_POSITION_VALUE = 5000  # Only track positions with value >= $5,000
TOP_N_POSITIONS = 30  # Number of top positions to display

# List of tokens to analyze for positions closest to liquidation
TOKENS_TO_ANALYZE = ['BTC', 'ETH', 'XRP', 'SOL']
TOKENS_TO_ANALYZE = ['BTC']  # Currently only analyzing BTC

# Highlight threshold for positions
HIGHLIGHT_THRESHOLD = 2000000  # $2 million

def get_random_quote():
    """Return a random Nomad DevOPS quote"""
    return random.choice(NOMAD_QUOTES)

def ensure_data_dir():
    """Ensure the data directory exists"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"{Fore.GREEN}✓ Data directory ready at {DATA_DIR}")
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ Error creating directory: {str(e)}")
        return False

def get_spot_position_usd(address):
    """Get USDC spot position for a given address"""
    try:
        # Get token balances from Hyperliquid API
        url = "https://api.hyperliquid.xyz/info"
        headers = {"Content-Type": "application/json"}
        balance_response = requests.post(url, headers=headers, json={
            "type": "spotClearinghouseState",
            "user": address
        })
        balance_data = balance_response.json()
        
        # Find USDC balance
        usdc_balance = 0
        for balance in balance_data['balances']:
            if balance['coin'] == 'USDC':
                usdc_balance = float(balance['total'])
                break
                
        return usdc_balance
        
    except Exception as e:
        print(f"{Fore.RED}✗ Error fetching USDC spot balance: {str(e)}")
        print(f"{Fore.RED}■ Stack trace:\n{traceback.format_exc()}")
        return 0

def spot_price_and_hoe_ass_spot_symbol(symbol):
    """Get spot price and symbol info from Hyperliquid"""
    try:
        url = "https://api.hyperliquid.xyz/info"
        headers = {"Content-Type": "application/json"}
        body = {"type": "spotMetaAndAssetCtxs"}
        
        # Make the request to the API
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract tokens and universe data
            tokens = data[0]['tokens']
            universe = data[0]['universe']
            asset_ctxs = data[1]
            
            # Find the symbol in the universe
            symbol_info = None
            for pair in universe:
                if pair['name'].split('/')[0] == symbol:
                    symbol_info = pair
                    break
                    
            if symbol_info:
                # Get the corresponding asset context
                ctx = asset_ctxs[symbol_info['index']]
                price = float(ctx['markPx']) if 'markPx' in ctx else None
                
                return {
                    'symbol': symbol,
                    'price': price,
                    'token_info': tokens[symbol_info['tokens'][0]],
                    'quote_info': tokens[symbol_info['tokens'][1]],
                    'is_canonical': symbol_info['isCanonical']
                }
            else:
                print(f"{Fore.RED}✗ Symbol {symbol} not found in universe")
                return None
        else:
            print(f"{Fore.RED}✗ Error: API returned status code {response.status_code}")
            return None
                
    except Exception as e:
        print(f"{Fore.RED}✗ Error fetching spot info: {str(e)}")
        print(f"{Fore.RED}■ Stack trace:\n{traceback.format_exc()}")
        return None

def display_top_individual_positions(df, n=TOP_N_POSITIONS):
    """
    Display top individual long and short positions
    """
    if df is None or df.empty:
        print(f"{Fore.RED}No positions to display!")
        return None, None
    
    # Create a copy to avoid modifying the original
    display_df = df.copy()
    
    # Validate position types for positions with valid liquidation prices
    valid_liq_df = display_df[display_df['liquidation_price'] > 0].copy()
    if not valid_liq_df.empty:
        # Verify if the position type matches the relationship between entry and liquidation price
        valid_liq_df['position_type_verified'] = np.where(
            valid_liq_df['is_long'],
            valid_liq_df['liquidation_price'] < valid_liq_df['entry_price'],  # Long should have liq price < entry
            valid_liq_df['liquidation_price'] > valid_liq_df['entry_price']   # Short should have liq price > entry
        )
        
        # Count inconsistencies
        inconsistent_positions = valid_liq_df[~valid_liq_df['position_type_verified']]
        
        if len(inconsistent_positions) > 0:
            print(f"{Fore.YELLOW}⚠ Note: Some positions have been reclassified based on their liquidation prices.")
            
        # Update the is_long column with corrected values
        # Note: The 'is_long_corrected' column is missing in the code - I'm inferring it should be:
        valid_liq_df['is_long_corrected'] = ~valid_liq_df['is_long'] if not valid_liq_df['position_type_verified'].all() else valid_liq_df['is_long']
        
        valid_liq_df['is_long'] = valid_liq_df['is_long_corrected']
        
        # Update the display dataframe with corrected position types
        display_df.loc[valid_liq_df.index, 'is_long'] = valid_liq_df['is_long']
    
    # Sort by position value
    longs = display_df[display_df['is_long']].sort_values('position_value', ascending=False)
    shorts = display_df[~display_df['is_long']].sort_values('position_value', ascending=False)
    
    # Display top long positions
    print(f"\n{Fore.GREEN}{Style.BRIGHT}🔹 TOP {n} INDIVIDUAL LONG POSITIONS 📈")
    print(f"{Fore.GREEN}{'-'*80}")
    
    if len(longs) > 0:
        for i, (_, row) in enumerate(longs.head(n).iterrows(), 1):
            liq_price = row['liquidation_price'] if row['liquidation_price'] > 0 else "N/A"
            liq_display = f"${liq_price:.2f}" if liq_price != "N/A" else "N/A"
            
            print(f"{Fore.GREEN}#{i} {Fore.YELLOW}{row['coin']} {Fore.GREEN}${row['position_value']:.2f} " +
                  f"{Fore.BLUE}| Entry: ${row['entry_price']:.2f} " +
                  f"{Fore.MAGENTA}| PnL: ${row['unrealized_pnl']:.2f} " +
                  f"{Fore.CYAN}| Leverage: {row['leverage']}x " +
                  f"{Fore.RED}| Liq: {liq_display}")
            print(f"{Fore.CYAN}    Address: {row['address']}")
    else:
        print(f"{Fore.YELLOW}No long positions found!")
        
     # Display top short positions
    print(f"\n{Fore.RED}{Style.BRIGHT}🔹 TOP {n} INDIVIDUAL SHORT POSITIONS 📉")
    print(f"{Fore.RED}{'-'*80}")
    
    if len(shorts) > 0:
        for i, (_, row) in enumerate(shorts.head(n).iterrows(), 1):
            liq_price = row['liquidation_price'] if row['liquidation_price'] > 0 else "N/A"
            liq_display = f"${liq_price:.2f}" if liq_price != "N/A" else "N/A"
            
            print(f"{Fore.RED}#{i} {Fore.YELLOW}{row['coin']} {Fore.RED}${row['position_value']:.2f} " +
                  f"{Fore.BLUE}| Entry: ${row['entry_price']:.2f} " +
                  f"{Fore.MAGENTA}| PnL: ${row['unrealized_pnl']:.2f} " +
                  f"{Fore.CYAN}| Leverage: {row['leverage']}x " +
                  f"{Fore.RED}| Liq: {liq_display}")
            print(f"{Fore.CYAN}    Address: {row['address']}")
    else:
        print(f"{Fore.YELLOW}No short positions found!")
    
    return longs.head(n), shorts.head(n)

def display_risk_metrics(df):
    """
    Display metrics for positions closest to liquidation
    """
    if df is None or df.empty:
        return None, None, None
    
    # Create a copy to avoid modifying the original
    risk_df = df.copy()
    
    # Filter out positions with invalid liquidation prices
    risk_df = risk_df[risk_df['liquidation_price'] > 0]
    
    if risk_df.empty:
        print(f"{Fore.YELLOW}No positions with valid liquidation prices found!")
        return None, None, None
    
    # Filter risk_df to only include tokens in TOKENS_TO_ANALYZE
    risk_df = risk_df[risk_df['coin'].isin(TOKENS_TO_ANALYZE)]
    
    # Fetch current prices for tokens in TOKENS_TO_ANALYZE once
    unique_coins = risk_df['coin'].unique()
    current_prices = {coin: n.get_current_price(coin) for coin in unique_coins}
    
    # Add current price to the DataFrame
    risk_df['current_price'] = risk_df['coin'].map(current_prices)
    
    # Calculate standardized distance to liquidation using current price
    risk_df['distance_to_liq_pct'] = np.where(
        risk_df['is_long'],
        abs(risk_df['current_price'] - risk_df['liquidation_price']) / risk_df['current_price'] * 100,
        abs(risk_df['liquidation_price'] - risk_df['current_price']) / risk_df['current_price'] * 100
    )
    
    # Correct position type based on liquidation price
    risk_df['is_long_corrected'] = risk_df['liquidation_price'] < risk_df['entry_price']
    risk_df['is_long'] = risk_df['is_long_corrected']
    
    # Sort by distance to liquidation (ascending)
    risk_df = risk_df.sort_values('distance_to_liq_pct')
    
    # Split into longs and shorts
    risky_longs = risk_df[risk_df['is_long']].sort_values('distance_to_liq_pct')
    risky_shorts = risk_df[~risk_df['is_long']].sort_values('distance_to_liq_pct')
    
    # Display positions closest to liquidation — LONGS
    print(f"\n{Fore.GREEN}{Style.BRIGHT}⚠ TOP {TOP_N_POSITIONS} LONG POSITIONS CLOSEST TO LIQUIDATION 🧨")
    print(f"{Fore.GREEN}{'-'*80}")
    
    if len(risky_longs) > 0:
        running_total_value = 0
        highest_distance = 0
        last_pct_threshold = 0
        
        for i, (_, row) in enumerate(risky_longs.head(TOP_N_POSITIONS).iterrows(), 1):
            highlight = row['position_value'] > HIGHLIGHT_THRESHOLD
            running_total_value += row['position_value']
            highest_distance = max(highest_distance, row['distance_to_liq_pct'])
            
            # Get USDC balance for top 2 positions
            usdc_balance = get_spot_position_usd(row['address']) if i <= 2 else 0
            
            display_text = f"{Fore.GREEN}#{i} {Fore.YELLOW}{row['coin']} {Fore.GREEN}${row['position_value']:.2f} " + \
                f"{Fore.BLUE}| Entry: ${row['entry_price']:.2f} " + \
                f"{Fore.RED}| Liq: ${row['liquidation_price']:.2f} " + \
                f"{Fore.MAGENTA}| Current: ${row['current_price']:.2f} " + \
                f"{Fore.MAGENTA}| Distance: {row['distance_to_liq_pct']:.2f}% " + \
                f"{Fore.CYAN}| Leverage: {row['leverage']}x"
                
            if i <= 2:
                display_text += f" {Fore.MAGENTA}| 💰 USDC: ${usdc_balance:.2f}"
                
            if highlight:
                display_text = colored(f"#{i} {row['coin']} ${row['position_value']:.2f} " + \
                    f"| Entry: ${row['entry_price']:.2f} " + \
                    f"| Liq: ${row['liquidation_price']:.2f} " + \
                    f"| Current: ${row['current_price']:.2f} " + \
                    f"| Distance: {row['distance_to_liq_pct']:.2f}% " + \
                    f"| Leverage: {row['leverage']}x" + \
                    (f" | 💰 USDC: ${usdc_balance:.2f}" if i <= 2 else ""), 'black', 'on_yellow')
                
            print(display_text)
            print(f"{Fore.CYAN}    Address: {row['address']}")
            
            if i % 10 == 0:
                agg_display = f"📊 AGGREGATE (1-{i}): Total Long Positions: ${running_total_value:.2f} | All Liquidated Within: {highest_distance:.2f}%"
                print(colored(agg_display, 'black', 'on_cyan'))
                print(f"{Fore.CYAN}{'-'*80}")
                
            current_pct_threshold = int(row['distance_to_liq_pct'] / 2) * 2
            if current_pct_threshold > last_pct_threshold:
                pct_agg_display = f"📊 LIQUIDATION THRESHOLD 0-{current_pct_threshold}%: Total Long Value: ${running_total_value:.2f}"
                print(colored(pct_agg_display, 'white', 'on_blue'))
                last_pct_threshold = current_pct_threshold
    else:
        print(f"{Fore.YELLOW}No long positions with liquidation prices found!")
    
    # Display positions closest to liquidation — SHORTS
    print(f"\n{Fore.RED}{Style.BRIGHT}★ TOP {TOP_N_POSITIONS} SHORT POSITIONS CLOSEST TO LIQUIDATION 🧨")
    print(f"{Fore.RED}{'-'*80}")
    
    if len(risky_shorts) > 0:
        running_total_value = 0
        highest_distance = 0
        last_pct_threshold = 0
        
        for i, (_, row) in enumerate(risky_shorts.head(TOP_N_POSITIONS).iterrows(), 1):
            highlight = row['position_value'] > HIGHLIGHT_THRESHOLD
            running_total_value += row['position_value']
            highest_distance = max(highest_distance, row['distance_to_liq_pct'])
            
            # Get USDC balance for top 2 positions
            usdc_balance = get_spot_position_usd(row['address']) if i <= 2 else 0
            
            display_text = f"{Fore.RED}#{i} {Fore.YELLOW}{row['coin']} {Fore.RED}${row['position_value']:.2f} " + \
                f"{Fore.BLUE}| Entry: ${row['entry_price']:.2f} " + \
                f"{Fore.RED}| Liq: ${row['liquidation_price']:.2f} " + \
                f"{Fore.MAGENTA}| Current: ${row['current_price']:.2f} " + \
                f"{Fore.MAGENTA}| Distance: {row['distance_to_liq_pct']:.2f}% " + \
                f"{Fore.CYAN}| Leverage: {row['leverage']}x"
                
            if i <= 2:
                display_text += f" {Fore.MAGENTA}| 💰 USDC: ${usdc_balance:.2f}"
                
            if highlight:
                display_text = colored(f"#{i} {row['coin']} ${row['position_value']:.2f} " + \
                    f"| Entry: ${row['entry_price']:.2f} " + \
                    f"| Liq: ${row['liquidation_price']:.2f} " + \
                    f"| Current: ${row['current_price']:.2f} " + \
                    f"| Distance: {row['distance_to_liq_pct']:.2f}% " + \
                    f"| Leverage: {row['leverage']}x" + \
                    (f" | 💰 USDC: ${usdc_balance:.2f}" if i <= 2 else ""), 'black', 'on_yellow')
                
            print(display_text)
            print(f"{Fore.CYAN}    Address: {row['address']}")
            
            if i % 10 == 0:
                agg_display = f"📊 AGGREGATE (1-{i}): Total Short Positions: ${running_total_value:.2f} | All Liquidated Within: {highest_distance:.2f}%"
                print(colored(agg_display, 'black', 'on_cyan'))
                print(f"{Fore.CYAN}{'-'*80}")
                
            current_pct_threshold = int(row['distance_to_liq_pct'] / 2) * 2
            if current_pct_threshold > last_pct_threshold:
                pct_agg_display = f"📊 LIQUIDATION THRESHOLD 0-{current_pct_threshold}%: Total Short Value: ${running_total_value:.2f}"
                print(colored(pct_agg_display, 'white', 'on_blue'))
                last_pct_threshold = current_pct_threshold
    else:
        print(f"{Fore.YELLOW}No short positions with liquidation prices found!")
        
    return risky_longs.head(TOP_N_POSITIONS), risky_shorts.head(TOP_N_POSITIONS), current_prices

def save_liquidation_risk_to_csv(risky_longs_df, risky_shorts_df):
    """
    Save positions closest to liquidation to a CSV file
    """
    if risky_longs_df is None and risky_shorts_df is None:
        print(f"{Fore.RED}🔴 Nomad DevOPS says: No positions with liquidation data to save! 😢")
        return
    
    # Save risky long positions
    if risky_longs_df is not None and not risky_longs_df.empty:
        # Add a direction column
        risky_longs_df = risky_longs_df.copy()
        risky_longs_df['direction'] = 'LONG'
        
        # Save to CSV
        longs_file = os.path.join(DATA_DIR, "liquidation_closest_long_positions.csv")
        risky_longs_df.to_csv(longs_file, index=False, float_format='%.2f')
    
    # Save risky short positions
    if risky_shorts_df is not None and not risky_shorts_df.empty:
        # Add a direction column
        risky_shorts_df = risky_shorts_df.copy()
        risky_shorts_df['direction'] = 'SHORT'
        
        # Save to CSV
        shorts_file = os.path.join(DATA_DIR, "liquidation_closest_short_positions.csv")
        risky_shorts_df.to_csv(shorts_file, index=False, float_format='%.2f')
    
    # Combine risky long and short positions into a single file
    if (risky_longs_df is not None and not risky_longs_df.empty) or (risky_shorts_df is not None and not risky_shorts_df.empty):
        # Create combined DataFrame
        combined_df = pd.concat([risky_longs_df, risky_shorts_df]) if risky_longs_df is not None and risky_shorts_df is not None else (risky_longs_df if risky_longs_df is not None else risky_shorts_df)
        
        # Sort by distance to liquidation
        combined_df = combined_df.sort_values('distance_to_liq_pct')
        
        # Save to CSV
        combined_file = os.path.join(DATA_DIR, "liquidation_closest_positions.csv")
        combined_df.to_csv(combined_file, index=False, float_format='%.2f')
        
        # Create a combined message about all files saved
        long_count = 0 if risky_longs_df is None else len(risky_longs_df)
        short_count = 0 if risky_shorts_df is None else len(risky_shorts_df)
        print(f"{Fore.GREEN}🟢 Nomad DevOPS says: Saved {long_count} long and {short_count} short positions closest to liquidation to CSV files ✅")

def save_top_whale_positions_to_csv(longs_df, shorts_df):
    """
    Save top whale positions to a CSV file
    """
    if longs_df is None and shorts_df is None:
        print(f"{Fore.RED}🔴 Nomad DevOPS says: No top whale positions to save! 😢")
        return
    
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save top long positions
    if longs_df is not None and not longs_df.empty:
        # Add a direction column
        longs_df = longs_df.copy()
        longs_df['direction'] = 'LONG'
        
        # Save to CSV
        longs_file = os.path.join(DATA_DIR, "top_whale_long_positions.csv")
        longs_df.to_csv(longs_file, index=False, float_format='%.2f')
        
    # Save top short positions
    if shorts_df is not None and not shorts_df.empty:
        # Add a direction column
        shorts_df = shorts_df.copy()
        shorts_df['direction'] = 'SHORT'
        
        # Save to CSV
        shorts_file = os.path.join(DATA_DIR, "top_whale_short_positions.csv")
        shorts_df.to_csv(shorts_file, index=False, float_format='%.2f')

    # Combine long and short positions into a single file
    if (longs_df is not None and not longs_df.empty) or (shorts_df is not None and not shorts_df.empty):
        # Create combined DataFrame
        combined_df = pd.concat([longs_df, shorts_df]) if longs_df is not None and shorts_df is not None else (longs_df if longs_df is not None else shorts_df)
        
        # Sort by position value
        combined_df = combined_df.sort_values('position_value', ascending=False)
        
        # Save to CSV
        combined_file = os.path.join(DATA_DIR, "top_whale_positions.csv")
        combined_df.to_csv(combined_file, index=False, float_format='%.2f')
        print(f"{Fore.GREEN}🟢 Nomad DevOPS says: Saved {len(combined_df)} combined top whale positions to {combined_file} ✨")

def process_positions(df, coin_filter=None):
    """
    Process the position data into a more usable format, filtering positions below min value
    and optionally by coin
    """
    if df is None or df.empty:
        print(f"{Fore.RED}No positions data to process!")
        return pd.DataFrame()
    
    print(f"{Fore.CYAN}🔍 Processing {len(df)} positions...")
    
    # Filter positions below minimum value threshold
    filtered_df = df[df['position_value'] >= MIN_POSITION_VALUE].copy()
    
    # Make sure numeric columns are the right type
    numeric_cols = ['entry_price', 'position_value', 'unrealized_pnl', 'liquidation_price', 'leverage']
    for col in numeric_cols:
        if col in filtered_df.columns:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')
    
    # Convert boolean columns if needed
    if 'is_long' in filtered_df.columns and filtered_df['is_long'].dtype != bool:
        filtered_df['is_long'] = filtered_df['is_long'].map({'True': True, 'False': False})
    
    # Validate position types for positions with valid liquidation prices
    valid_liq_df = filtered_df[filtered_df['liquidation_price'] > 0].copy()
    if not valid_liq_df.empty:
        # Verify if the position type matches the relationship between entry and liquidation price
        valid_liq_df['position_type_verified'] = np.where(
            valid_liq_df['is_long'],
            valid_liq_df['liquidation_price'] < valid_liq_df['entry_price'],  # Long should have liq price < entry
            valid_liq_df['liquidation_price'] > valid_liq_df['entry_price']   # Short should have liq price > entry
        )
        
        # Count inconsistencies
        inconsistent_positions = valid_liq_df[~valid_liq_df['position_type_verified']]
        
        if len(inconsistent_positions) > 0:
            print(f"{Fore.RED}⚠ WARNING: Found {len(inconsistent_positions)} positions with inconsistent position types!")
            print(f"{Fore.YELLOW}↺ Correcting position types based on liquidation vs. entry price relationships...")
            
            # Create a corrected position type column based on liquidation vs entry price
            valid_liq_df['is_long_corrected'] = valid_liq_df['liquidation_price'] < valid_liq_df['entry_price']
            
            # Update the is_long column with corrected values
            valid_liq_df['is_long'] = valid_liq_df['is_long_corrected']
            
            # Update the filtered dataframe with corrected position types
            filtered_df.loc[valid_liq_df.index, 'is_long'] = valid_liq_df['is_long']
            
            print(f"{Fore.GREEN}✓ Position types corrected!")
    
    # Filter by coin if specified
    if coin_filter:
        coin_filter = coin_filter.upper()  # Convert to uppercase for case-insensitive matching
        filtered_df = filtered_df[filtered_df['coin'] == coin_filter]
        print(f"{Fore.MAGENTA}🪙 Filtering for {coin_filter} positions only")
    
    print(f"{Fore.GREEN}✓ Processed {len(filtered_df)} positions after filtering (min value: ${MIN_POSITION_VALUE})")
    return filtered_df

def save_positions_to_csv(df, current_prices=None, quiet=False):
    """
    Save all positions to a CSV file and create aggregated views
    """
    if df is None or df.empty:
        print(f"{Fore.RED}🔴 Nomad DevOPS says: No positions found to save! 😢")
        return None, None
    
    # Format numeric columns
    numeric_cols = ['entry_price', 'position_value', 'unrealized_pnl', 'liquidation_price', 'leverage']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Save all positions
    positions_file = os.path.join(DATA_DIR, "all_positions.csv")
    df.to_csv(positions_file, index=False, float_format='%.2f')
    
    # Create and save aggregated view
    agg_df = df.groupby(['coin', 'is_long']).agg({
        'position_value': 'sum',
        'unrealized_pnl': 'sum',
        'address': 'count',
        'leverage': 'mean',  # Average leverage
        'liquidation_price': lambda x: np.nan if all(pd.isna(x)) else np.nanmean(x)  # Average liquidation price, ignoring NaN values
    }).reset_index()
    
    # Add direction and rename columns
    agg_df['direction'] = agg_df['is_long'].apply(lambda x: 'LONG' if x else 'SHORT')
    agg_df = agg_df.rename(columns={
        'address': 'num_traders',
        'position_value': 'total_value',
        'unrealized_pnl': 'total_pnl',
        'leverage': 'avg_leverage',
        'liquidation_price': 'avg_liquidation_price'
    })
    
    # Calculate average value per trader
    agg_df['avg_value_per_trader'] = agg_df['total_value'] / agg_df['num_traders']
    
    # Sort by total value
    agg_df = agg_df.sort_values('total_value', ascending=False)
    
    # Save aggregated view
    agg_file = os.path.join(DATA_DIR, "aggregated_positions.csv")
    agg_df.to_csv(agg_file, index=False, float_format='%.2f')
    
    # Display summaries (for terminal display only, not affecting CSV output)
    print(f"\n{Fore.CYAN}{'-'*30} POSITION SUMMARY {'-'*30}")
    display_cols = ['coin', 'direction', 'total_value', 'num_traders', 'avg_value_per_trader', 'avg_leverage']
    
    # Temporarily format numbers with commas for display only
    with pd.option_context('display.float_format', '{:,.2f}'.format):
        print(f"{Fore.WHITE}{agg_df[display_cols]}")
    
    print(f"\n{Fore.GREEN}★ TOP LONG POSITIONS (AGGREGATED):")
    print(f"{Fore.GREEN}{agg_df[agg_df['is_long']][display_cols].head()}")
    
    print(f"\n{Fore.RED}★ TOP SHORT POSITIONS (AGGREGATED):")
    print(f"{Fore.RED}{agg_df[~agg_df['is_long']][display_cols].head()}")
    
    # Display top individual positions and get the dataframes
    longs_df, shorts_df = display_top_individual_positions(df)
    
    # Save top whale positions to CSV
    save_top_whale_positions_to_csv(longs_df, shorts_df)
    
    # Display risk metrics and get risky positions
    risky_longs_df, risky_shorts_df, fetched_prices = display_risk_metrics(df)
    
    # Save liquidation risk positions to CSV
    save_liquidation_risk_to_csv(risky_longs_df, risky_shorts_df)
    
    # Check if we have current prices from the risk metrics function
    if current_prices is None:
        current_prices = fetched_prices
    
    # Check if we still need to get prices (should never happen as display_risk_metrics has already fetched them)
    if current_prices is None:
        # Fetch current prices for tokens in TOKENS_TO_ANALYZE only if needed
        unique_coins = df[df['coin'].isin(TOKENS_TO_ANALYZE)]['coin'].unique()
        current_prices = {coin: n.get_current_price(coin) for coin in unique_coins}
    
    # Use current prices for liquidation impact analysis
    print(f"\n{Fore.CYAN}{'-'*80}")
    print(f"{Fore.CYAN}{'-'*20} ★ LIQUIDATION IMPACT FOR 3% PRICE MOVE ★ {'-'*20}")
    print(f"{Fore.CYAN}{'-'*80}")
    
    # Initialize dictionaries to track liquidation values
    total_long_liquidations = {}
    total_short_liquidations = {}
    all_long_liquidations = 0
    all_short_liquidations = 0
    
    for coin in TOKENS_TO_ANALYZE:
        if coin not in current_prices:
            continue
            
        # Filter positions for the current coin
        coin_positions = df[df['coin'] == coin].copy()
        if coin_positions.empty:
            continue
            
        # Add current price to the coin positions DataFrame
        current_price = current_prices[coin]
        coin_positions['current_price'] = current_price
        
        # Calculate price levels for 3% moves
        price_3pct_down = current_price * 0.97
        price_3pct_up = current_price * 1.03
        
        # Calculate potential liquidations for long positions
        long_liquidations = coin_positions[(coin_positions['is_long']) & 
                                        (coin_positions['liquidation_price'] >= price_3pct_down) & 
                                        (coin_positions['liquidation_price'] <= current_price)]
        
        total_long_liquidation_value = long_liquidations['position_value'].sum()
        
        # Calculate potential liquidations for short positions
        short_liquidations = coin_positions[(~coin_positions['is_long']) & 
                                         (coin_positions['liquidation_price'] <= price_3pct_up) & 
                                         (coin_positions['liquidation_price'] >= current_price)]
        
        total_short_liquidation_value = short_liquidations['position_value'].sum()
        
        # Store liquidation values in dictionary
        total_long_liquidations[coin] = total_long_liquidation_value
        total_short_liquidations[coin] = total_short_liquidation_value
        
        # Add to total liquidations
        all_long_liquidations += total_long_liquidation_value
        all_short_liquidations += total_short_liquidation_value
    
        # Display results (only if not in quiet mode)
        if not quiet:
            print(f"{Fore.GREEN}{coin} Long Liquidations (3% move DOWN to ${price_3pct_down:.2f}): ${total_long_liquidation_value:.2f}")
            print(f"{Fore.RED}{coin} Short Liquidations (3% move UP to ${price_3pct_up:.2f}): ${total_short_liquidation_value:.2f}")
    
    # Display summary of total liquidations
    print(f"\n{Fore.CYAN}{'-'*80}")
    print(f"{Fore.CYAN}{'-'*25} 💰 TOTAL LIQUIDATION SUMMARY 💰 {'-'*25}")
    print(f"{Fore.CYAN}{'-'*80}")
    print(f"{Fore.GREEN}Total Long Liquidations (3% move DOWN): ${all_long_liquidations:.2f}")
    print(f"{Fore.RED}Total Short Liquidations (3% move UP): ${all_short_liquidations:.2f}")
    
    # Generate trading recommendations based on liquidation imbalance
    print(f"\n{Fore.CYAN}{'-'*80}")
    print(f"{Fore.CYAN}{'-'*20} 🔮 MARKET DIRECTION (NFA) 🚀 {'-'*20}")
    print(f"{Fore.CYAN}{'-'*80}")
    
    # Overall market direction
    if all_long_liquidations > all_short_liquidations:
        direction = f"MARKET DIRECTION (NFA): SHORT THE MARKET (${all_long_liquidations:.2f} long liquidations at risk within a 3% move of current price)"
        print(f"{Back.GREEN}{Fore.BLACK}{Style.BRIGHT}{direction}{Style.RESET_ALL}")
    else:
        direction = f"MARKET DIRECTION (NFA): LONG THE MARKET (${all_short_liquidations:.2f} short liquidations at risk within a 3% move of current price)"
        print(f"{Back.GREEN}{Fore.BLACK}{Style.BRIGHT}{direction}{Style.RESET_ALL}")
    
    # Individual coin directions
    print(f"\n{Fore.CYAN}{'-'*30} INDIVIDUAL COIN DIRECTION (NFA) {'-'*30}")
    
    # Sort coins by liquidation imbalance (largest difference first)
    liquidation_imbalance = {}
    for coin in total_long_liquidations.keys():
        if coin in total_short_liquidations:
            liquidation_imbalance[coin] = abs(total_long_liquidations[coin] - total_short_liquidations[coin])
            
    sorted_coins = sorted(liquidation_imbalance.keys(), key=lambda x: liquidation_imbalance[x], reverse=True)
    
    for coin in sorted_coins:
        long_liq = total_long_liquidations[coin]
        short_liq = total_short_liquidations[coin]
        
        # Only show directions for coins with significant liquidation risk
        if long_liq < 10000 and short_liq < 10000:
            continue
            
        if long_liq > short_liq:
            rec = f"{coin}: SHORT (${long_liq:.2f} long liquidations vs ${short_liq:.2f} short within a 3% move)"
            print(f"{Back.GREEN}{Fore.BLACK}{Style.BRIGHT}{rec}{Style.RESET_ALL}")
        else:
            rec = f"{coin}: LONG (${short_liq:.2f} short liquidations vs ${long_liq:.2f} long within a 3% move)"
            print(f"{Back.GREEN}{Fore.BLACK}{Style.BRIGHT}{rec}{Style.RESET_ALL}")
    
    print(f"\n{Fore.MAGENTA}↓ Trading strategy: Target coins with largest liquidation imbalance for potential cascade liquidations")
    print(f"{Fore.YELLOW}⚠ NFA: This analysis is NOT financial advice. Always do your own research! 🧠")
    
    # Create liquidation thresholds table
    create_liquidation_thresholds_table(df, current_prices, quiet)
    
    # Combine the save notifications and execution time in one summary line
    long_count = len(longs_df) if longs_df is not None else 0
    short_count = len(shorts_df) if shorts_df is not None else 0
    print(f"{Fore.GREEN}🟢 Nomad DevOPS saved {long_count} long and {short_count} short positions to CSV files in {DATA_DIR} 📊")
    
    return df, agg_df

def display_highlighted_positions(df):
    """
    Display a table of highlighted positions (value > $2M) from the top 30 positions closest to liquidation
    """
    if df is None or df.empty:
        return
    
    # Filter for positions with value > $2M and only for tokens we analyze
    highlighted_df = df[
        (df['position_value'] > HIGHLIGHT_THRESHOLD) &
        (df['coin'].isin(TOKENS_TO_ANALYZE))
    ].copy()
    
    if highlighted_df.empty:
        return
    
    # Get current prices only for tokens we have highlighted positions for
    unique_coins = highlighted_df['coin'].unique()
    current_prices = {coin: n.get_current_price(coin) for coin in unique_coins}
    
    # Add current price to the DataFrame
    highlighted_df['current_price'] = highlighted_df['coin'].map(current_prices)
    
    # Calculate distance to liquidation percentage
    highlighted_df['distance_to_liq_pct'] = np.where(
        highlighted_df['is_long'],
        abs((highlighted_df['current_price'] - highlighted_df['liquidation_price']) / highlighted_df['current_price'] * 100),
        abs((highlighted_df['liquidation_price'] - highlighted_df['current_price']) / highlighted_df['current_price'] * 100)
    )
    
    # Split into longs and shorts
    highlighted_longs = highlighted_df[highlighted_df['is_long']].sort_values('distance_to_liq_pct')
    highlighted_shorts = highlighted_df[~highlighted_df['is_long']].sort_values('distance_to_liq_pct')
    
    # Get top 2 for each
    top_longs = highlighted_longs.head(2)
    top_shorts = highlighted_shorts.head(2)
    
    # Only proceed if we have any highlighted positions
    if top_longs.empty and top_shorts.empty:
        return
    
    print(f"\n{Fore.CYAN}{'-'*140}")
    print(f"{Fore.CYAN}{'-'*15} 💰 POSITIONS CLOSEST TO LIQUIDATION (>${HIGHLIGHT_THRESHOLD:,}) 💰 {'-'*15}")
    print(f"{Fore.CYAN}{'-'*140}")
    
    # Create header with fixed widths
    header = f"{Fore.YELLOW}{'Position':<10} | {'Coin':<4} | {'Value':>17} | " + \
             f"{'Entry':>12} | {'Liq':>12} | {'Distance':>9} | {'Leverage':>8} | {'Address':>42} | {'USDC':>12}"
    separator = f"{Fore.CYAN}{'-'*10}--{'-'*4}--{'-'*17}--{'-'*12}--{'-'*12}--{'-'*9}--{'-'*8}--{'-'*42}--{'-'*12}"
    
    print(header)
    print(separator)
    
    # Display long positions
    for i, (_, row) in enumerate(top_longs.iterrows(), 1):
        usdc_balance = get_spot_position_usd(row['address'])
        print(f"{Fore.GREEN}{'LONG #' + str(i):<10} | " +
              f"{Fore.YELLOW}{row['coin']:<4} | " +
              f"{Fore.GREEN}${row['position_value']:>15,.2f} | " +
              f"{Fore.BLUE}${row['entry_price']:>10,.2f} | " +
              f"{Fore.RED}${row['liquidation_price']:>10,.2f} | " +
              f"{Fore.MAGENTA}{row['distance_to_liq_pct']:>7.2f}% | " +
              f"{Fore.CYAN}{row['leverage']:>3}x".ljust(8) + " | " +
              f"{Fore.BLUE}{row['address']} | " +
              f"{Fore.MAGENTA}${usdc_balance:>10,.2f}")
    
    # Display short positions
    for i, (_, row) in enumerate(top_shorts.iterrows(), 1):
        usdc_balance = get_spot_position_usd(row['address'])
        print(f"{Fore.RED}{'SHORT #' + str(i):<10} | " +
              f"{Fore.YELLOW}{row['coin']:<4} | " +
              f"{Fore.RED}${row['position_value']:>15,.2f} | " +
              f"{Fore.BLUE}${row['entry_price']:>10,.2f} | " +
              f"{Fore.RED}${row['liquidation_price']:>10,.2f} | " +
              f"{Fore.MAGENTA}{row['distance_to_liq_pct']:>7.2f}% | " +
              f"{Fore.CYAN}{row['leverage']:>3}x".ljust(8) + " | " +
              f"{Fore.BLUE}{row['address']} | " +
              f"{Fore.MAGENTA}${usdc_balance:>10,.2f}")
              
    print(f"{Fore.CYAN}{'-'*140}")

def display_market_metrics():
    """
    Display market metrics (funding rates) in a compact format
    """
    try:
        print(f"\n{Fore.CYAN}{'-'*80}")
        print(f"{Fore.CYAN}{'-'*15} 📊 MARKET METRICS 📊 {'-'*15}")
        print(f"{Fore.CYAN}{'-'*80}")
        
        # Get Binance funding rates directly
        binance_funding_rates = {}
        for token in TOKENS_TO_ANALYZE:
            try:
                url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={token}USDT"
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
                # Get the raw funding rate from the API and calculate annualized rate
                raw_funding_rate = float(data['lastFundingRate'])
                funding_rate_pct = raw_funding_rate * 100
                yearly_rate = funding_rate_pct * 3 * 365  # 3 times a day, 365 days
                binance_funding_rates[token] = yearly_rate
                
            except Exception as e:
                print(f"{Fore.RED}✗ Error fetching Binance funding rate for {token}: {str(e)}")
                binance_funding_rates[token] = None
        
        # Get Hyperliquid funding data
        try:
            url = "https://api.hyperliquid.xyz/info"
            headers = {"Content-Type": "application/json"}
            body = {"type": "metaAndAssetCtxs"}
            
            # Make the request to the API
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            hl_data = response.json()
            
            # Create a mapping of coins to their funding rates
            hl_funding_rates = {}
            for i, asset in enumerate(hl_data[0]['universe']):
                if asset['name'] in TOKENS_TO_ANALYZE:
                    funding_rate = float(hl_data[1][i]['funding'])
                    # Convert hourly rate to yearly (24 hours * 365 days)
                    yearly_rate = funding_rate * 24 * 365 * 100  # Convert to percentage
                    hl_funding_rates[asset['name']] = yearly_rate
                    
        except Exception as e:
            print(f"{Fore.RED}✗ Error fetching Hyperliquid funding rates: {str(e)}")
            hl_funding_rates = {}
        
        # Create header row
        header = f"{Fore.CYAN}{'Metric':<12} | "
        for token in TOKENS_TO_ANALYZE:
            header += f"{Fore.WHITE}{token:<25} | "
        
        # Create separator
        separator = f"{Fore.CYAN}{'-'*12} | " + f"{'-'*25} | " * len(TOKENS_TO_ANALYZE)
        
        # Create Binance funding rate row
        b_funding_row = f"{Fore.YELLOW}{'BNB Funding':<12} | "
        for token in TOKENS_TO_ANALYZE:
            if token in binance_funding_rates and binance_funding_rates[token] is not None:
                funding_value = f"{binance_funding_rates[token]:.2f}%"
                # Color code funding rates
                funding_color = Fore.GREEN if binance_funding_rates[token] < 0 else Fore.RED
                b_funding_row += f"{funding_color}{funding_value:<25} | "
            else:
                b_funding_row += f"{Fore.RED}{'N/A':<25} | "
        
        # Create Hyperliquid funding rate row
        hl_funding_row = f"{Fore.YELLOW}{'HL Funding':<12} | "
        for token in TOKENS_TO_ANALYZE:
            if token in hl_funding_rates:
                funding_value = f"{hl_funding_rates[token]:.2f}%"
                # Color code funding rates
                funding_color = Fore.GREEN if hl_funding_rates[token] < 0 else Fore.RED
                hl_funding_row += f"{funding_color}{funding_value:<25} | "
            else:
                hl_funding_row += f"{Fore.RED}{'N/A':<25} | "
        
        # Print the table
        print(f"\n{Fore.CYAN}{'-'*120}")
        print(header)
        print(separator)
        print(b_funding_row)
        print(hl_funding_row)
        print(f"{Fore.CYAN}{'-'*120}")
        
    except Exception as e:
        print(f"{Fore.RED}✗ Error displaying market metrics: {str(e)}")
        print(f"{Fore.RED}■ Stack trace:\n{traceback.format_exc()}")

def create_liquidation_thresholds_table(df, current_prices, quiet=False):
    """
    Create and display a table of liquidation thresholds at different price move percentages
    """
    # Display market metrics first
    display_market_metrics()
    
    # Display highlighted positions table second
    display_highlighted_positions(df)
    
    # Display liquidation thresholds table last
    print(f"\n{Fore.CYAN}{'-'*80}")
    print(f"{Fore.CYAN}{'-'*15} 🧨 PENDING LIQUIDATIONS BY PERCENTAGE MOVE 🧨 {'-'*15}")
    print(f"{Fore.CYAN}{'-'*80}")
    
    # Define thresholds to analyze - small ranges first, then larger ranges
    small_thresholds = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0]
    large_thresholds = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    all_thresholds = small_thresholds + large_thresholds
    
    # Initialize data structures for the table
    table_data = {
        'Threshold': [f"0-{t}%" for t in all_thresholds],
        'Long Liquidations ($)': [],
        'Short Liquidations ($)': [],
        'Total Liquidations ($)': [],
        'Imbalance (%)': [],
        'Direction': []
    }
    
    # Calculate liquidations for each threshold
    for threshold in all_thresholds:
        total_long_liquidations = 0
        total_short_liquidations = 0
        
        for coin in TOKENS_TO_ANALYZE:
            if coin not in current_prices:
                continue
                
            # Filter positions for the current coin
            coin_positions = df[df['coin'] == coin].copy()
            if coin_positions.empty:
                continue
                
            # Get current price and calculate threshold prices
            current_price = current_prices[coin]
            price_down = current_price * (1 - threshold/100)
            price_up = current_price * (1 + threshold/100)
            
            # Calculate liquidations for long positions
            long_liquidations = coin_positions[(coin_positions['is_long']) & 
                                            (coin_positions['liquidation_price'] >= price_down) & 
                                            (coin_positions['liquidation_price'] <= current_price)]
            
            long_value = long_liquidations['position_value'].sum()
            
            # Calculate liquidations for short positions
            short_liquidations = coin_positions[(~coin_positions['is_long']) & 
                                             (coin_positions['liquidation_price'] <= price_up) & 
                                             (coin_positions['liquidation_price'] >= current_price)]
            
            short_value = short_liquidations['position_value'].sum()
            
            # Add to totals
            total_long_liquidations += long_value
            total_short_liquidations += short_value
        
        # Add data to table
        total_liquidations = total_long_liquidations + total_short_liquidations
        
        # Calculate imbalance as percentage
        if total_liquidations > 0:
            imbalance_pct = ((total_long_liquidations - total_short_liquidations) / total_liquidations) * 100
        else:
            imbalance_pct = 0
            
        # Determine direction based on imbalance percentage
        if total_liquidations == 0:
            direction = ""  # Empty string for no liquidations
        elif abs(imbalance_pct) < 5:  # Less than 5% imbalance
            direction = "NEUTRAL"
        elif imbalance_pct > 0:
            direction = "SHORT"
        else:
            direction = "LONG"
            
        table_data['Long Liquidations ($)'].append(total_long_liquidations)
        table_data['Short Liquidations ($)'].append(total_short_liquidations)
        table_data['Total Liquidations ($)'].append(total_liquidations)
        table_data['Imbalance (%)'].append(imbalance_pct)
        table_data['Direction'].append(direction)
    
    # Create and display the overall table
    table_df = pd.DataFrame(table_data)
    
    # Format numeric columns with commas and percentages
    for col in ['Long Liquidations ($)', 'Short Liquidations ($)', 'Total Liquidations ($)']:
        table_df[col] = table_df[col].apply(lambda x: f"${x:,.2f}")
    
    # Format Imbalance as percentage with sign
    table_df['Imbalance (%)'] = table_df['Imbalance (%)'].apply(lambda x: f"{x:+.2f}%")
    
    # Create a styled string representation of the table
    styled_table = f"\n{Fore.CYAN}{'-'*120}\n"
    styled_table += f"{Fore.YELLOW}{'Threshold':<12} | {'Long Liquidations':<25} | {'Short Liquidations':<25} | {'Total Liquidations':<25} | {'Imbalance':<15} | {'Direction':<15}\n"
    styled_table += f"{Fore.CYAN}{'-'*120}\n"
    
    for i, row in table_df.iterrows():
        direction = row['Direction']
        if direction:  # Only set color if there's a direction
            direction_color = Fore.GREEN if direction == "LONG" else (Fore.RED if direction == "SHORT" else Fore.YELLOW)
        else:
            direction_color = Fore.WHITE  # Default color for empty direction
        
        # Determine imbalance color based on value
        imbalance_value = float(row['Imbalance (%)'].strip('%+'))
        imbalance_color = Fore.GREEN if imbalance_value < 0 else (Fore.RED if imbalance_value > 0 else Fore.YELLOW)
        
        styled_table += f"{Fore.WHITE}{row['Threshold']:<12} | " + \
                      f"{Fore.GREEN}{row['Long Liquidations ($)']:<25} | " + \
                      f"{Fore.RED}{row['Short Liquidations ($)']:<25} | " + \
                      f"{Fore.CYAN}{row['Total Liquidations ($)']:<25} | " + \
                      f"{imbalance_color}{row['Imbalance (%)']:<15} | " + \
                      f"{direction_color}{direction:<15}\n"
    
    styled_table += f"{Fore.CYAN}{'-'*120}"
    
    print(styled_table)
    
    # Save the table to CSV
    table_file = os.path.join(DATA_DIR, "liquidation_thresholds_table.csv")
    table_df.to_csv(table_file, index=False)

'''This section uses MoonDevs proprietary API to fetch positions data
If you dont have the key simply use:
pd.read_csv to load your own data
Im going to comment out this section and keep it just for posterity
'''
def fetch_positions_from_api():
    """
    Fetch positions from Nomad DevOPS API
    """
    try:
        # Initialize the API silently
        api = MoonDevAPI()  # Changed from NomadDevAPI to MoonDevAPI to match the import
        
        # Get positions data from the API
        positions_df = api.get_positions_hlp()
        
        if positions_df is None or positions_df.empty:
            print(f"{Fore.YELLOW}⚠ No positions data received from API, using mock data for testing!")
            
            # Create mock data for testing
            mock_data = {
                'address': [f'wallet_{i}' for i in range(50)],
                'coin': np.random.choice(['BTC', 'ETH', 'SOL', 'XRP'], 50),
                'is_long': np.random.choice([True, False], 50),
                'entry_price': np.random.uniform(10000, 60000, 50),
                'position_value': np.random.uniform(5000, 5000000, 50),
                'unrealized_pnl': np.random.uniform(-500000, 500000, 50),
                'liquidation_price': np.random.uniform(1000, 70000, 50),
                'leverage': np.random.uniform(1, 20, 50)
            }
            
            positions_df = pd.DataFrame(mock_data)
            
            # Ensure the liquidation prices make sense relative to entry prices
            for i, row in positions_df.iterrows():
                if row['is_long']:
                    positions_df.at[i, 'liquidation_price'] = row['entry_price'] * 0.8  # 20% below entry
                else:
                    positions_df.at[i, 'liquidation_price'] = row['entry_price'] * 1.2  # 20% above entry
            
            print(f"{Fore.GREEN}🟢 Nomad DevOPS says: Created mock data with {len(positions_df)} positions for testing! ✨")
        
        return positions_df
        
    except Exception as e:
        print(f"{Fore.RED}✗ Error fetching positions: {str(e)}")
        print(f"{Fore.RED}■ Stack trace:\n{traceback.format_exc()}")
        return None

def fetch_aggregated_positions_from_api():
    """
    Fetch aggregated positions from Nomad DevOPS API
    """
    try:
        # Initialize the API silently
        api = MoonDevAPI()
        
        # Get aggregated positions data from the API
        agg_positions_df = api.get_agg_positions_hlp()
        
        if agg_positions_df is None or agg_positions_df.empty:
            print(f"{Fore.YELLOW}⚠ No aggregated positions data received from API, using mock data for testing!")
            
            # Create mock aggregated data
            mock_data = {
                'coin': ['BTC', 'ETH', 'SOL', 'XRP', 'BTC', 'ETH', 'SOL', 'XRP'],
                'is_long': [True, True, True, True, False, False, False, False],
                'total_value': np.random.uniform(1000000, 30000000, 8),
                'num_traders': np.random.randint(50, 500, 8),
                'avg_liquidation_price': [30000, 2000, 80, 0.5, 50000, 3500, 120, 0.8]
            }
            
            agg_positions_df = pd.DataFrame(mock_data)
            
            print(f"{Fore.GREEN}🟢 Nomad DevOPS says: Created mock aggregated data with {len(agg_positions_df)} rows for testing! ✨")
        
        return agg_positions_df
        
    except Exception as e:
        print(f"{Fore.RED}✗ Error fetching aggregated positions: {str(e)}")
        print(f"{Fore.RED}■ Stack trace:\n{traceback.format_exc()}")
        
        # Create mock aggregated data in case of error
        print(f"{Fore.YELLOW}⚠ Creating mock aggregated data due to error...")
        mock_data = {
            'coin': ['BTC', 'ETH', 'SOL', 'XRP', 'BTC', 'ETH', 'SOL', 'XRP'],
            'is_long': [True, True, True, True, False, False, False, False],
            'total_value': np.random.uniform(1000000, 30000000, 8),
            'num_traders': np.random.randint(50, 500, 8),
            'avg_liquidation_price': [30000, 2000, 80, 0.5, 50000, 3500, 120, 0.8]
        }
        
        agg_positions_df = pd.DataFrame(mock_data)
        
        print(f"{Fore.GREEN}🟢 Nomad DevOPS says: Created mock aggregated data with {len(agg_positions_df)} rows for testing! ✨")
        return agg_positions_df

def bot():
    """Main function to run the position tracker (renamed from main to bot)"""
    # Use global configuration variables
    global MIN_POSITION_VALUE, TOP_N_POSITIONS
    
    # Display Nomad DevOPS banner
    print(NOMAD_BANNER_ALT)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="🔍 Nomad DevOPS's Hyperliquid Whale Position Tracker (API Version)")
    parser.add_argument('--min-value', type=int, default=MIN_POSITION_VALUE,
                      help=f'Minimum position value to consider (default: {MIN_POSITION_VALUE})')
    parser.add_argument('--top-n', type=int, default=TOP_N_POSITIONS,
                      help=f'Number of top positions to display (default: {TOP_N_POSITIONS})')
    parser.add_argument('--agg-only', action='store_true',
                      help='Only show aggregated data (faster, less detailed)')
    parser.add_argument('--coin', type=str, default=None,
                      help='Filter positions by coin (e.g., BTC, ETH, SOL)')
    parser.add_argument('--verify-positions', action='store_true',
                      help='Verify and correct position types based on liquidation prices')
    parser.add_argument('--quiet', action='store_true', default=False,
                      help='Reduce verbosity of output')
    parser.add_argument('--no-symbol-debug', action='store_true', default=True,
                      help='Disable printing of individual symbols during analysis')
    args = parser.parse_args()
    
    # Update configuration based on arguments
    MIN_POSITION_VALUE = args.min_value
    TOP_N_POSITIONS = args.top_n
    
    start_time = time.time()
    
    # Ensure data directory exists
    ensure_data_dir()
    
    # Fetch aggregated positions data first (this is faster)
    agg_df = fetch_aggregated_positions_from_api()
    
    if agg_df is not None:
        # Save aggregated positions
        agg_file = os.path.join(DATA_DIR, "aggregated_positions_from_api.csv")
        agg_df.to_csv(agg_file, index=False, float_format='%.2f')
        
        # Add direction column
        agg_df['direction'] = agg_df['is_long'].apply(lambda x: 'LONG' if x else 'SHORT')
        
        # Filter by coin if specified
        if args.coin:
            coin = args.coin.upper()
            agg_df = agg_df[agg_df['coin'] == coin]
        
        if not args.quiet:
            # Display aggregated summaries
            print(f"\n{Fore.CYAN}{'-'*30} AGGREGATED POSITION SUMMARY {'-'*30}")
            display_cols = ['coin', 'direction', 'total_value', 'num_traders', 'liquidation_price']
            
            # Temporarily format numbers with commas for display only
            with pd.option_context('display.float_format', '{:,.2f}'.format):
                print(f"{Fore.WHITE}{agg_df[display_cols]}")
            
            print(f"\n{Fore.GREEN}★ TOP LONG POSITIONS (AGGREGATED):")
            print(f"{Fore.GREEN}{agg_df[agg_df['is_long']][display_cols].head()}")
            
            print(f"\n{Fore.RED}★ TOP SHORT POSITIONS (AGGREGATED):")
            print(f"{Fore.RED}{agg_df[~agg_df['is_long']][display_cols].head()}")
    
    # If not only showing aggregated data, fetch and process detailed positions
    if not args.agg_only:
        # Fetch detailed positions data
        positions_df = fetch_positions_from_api()
        
        if positions_df is not None:
            # Process positions (filter by min value, etc.)
            processed_df = process_positions(positions_df, args.coin)
            
            if not processed_df.empty:
                # Display top individual positions and get the dataframes
                longs_df, shorts_df = display_top_individual_positions(processed_df)
                
                # Save top whale positions to CSV
                save_top_whale_positions_to_csv(longs_df, shorts_df)
                
                # Get risk metrics and current prices in one step
                risky_longs_df, risky_shorts_df, current_prices = display_risk_metrics(processed_df)
                
                # Save liquidation risk positions to CSV
                save_liquidation_risk_to_csv(risky_longs_df, risky_shorts_df)
                
                # Pass the already fetched current prices to save_positions_to_csv
                positions_df, _ = save_positions_to_csv(processed_df, current_prices, quiet=args.quiet)
            else:
                print(f"{Fore.RED}⚠ No positions found after filtering! Try adjusting your filters.")
    
    # Calculate and display execution time
    execution_time = time.time() - start_time
    print(f"\n{Fore.CYAN}⏱ Analysis completed in {execution_time:.2f} seconds")

if __name__ == "__main__":
    # Initial run
    bot()
    
    # Schedule the main function to run every minute
    schedule.every(1).minutes.do(bot)
    
    while True:
        try:
            # Run pending scheduled tasks
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"{Fore.RED}Encountered an error: {e}")
            print(f"{Fore.RED}■ Stack trace:\n{traceback.format_exc()}")
            # Wait before retrying to avoid rapid error logging
            time.sleep(10)