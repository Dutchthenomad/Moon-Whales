# HyperLiquid Whale Position Tracker - Getting Started Guide

## Introduction

Welcome to the HyperLiquid Whale Position Tracker! This tool allows you to monitor the trading positions of "whale" wallets (large holders) on the HyperLiquid DEX, providing valuable insights into market trends and potential trading opportunities.

### Credits

This project was originally created by [MoonDev](https://moondev.com) as part of the 'Day 46' video from the MoonDev Course. All credit for this incredible tool goes to MoonDev, who offers high-quality algorithmic trading education and resources:

- Project updates: [moondev.com](https://moondev.com)
- Free Algo Trading Roadmap: [moondev.com](https://moondev.com)
- Algo Trading Education: [algotradecamp.com](https://algotradecamp.com)
- Business Contact: moon@algotradecamp.com

We highly recommend checking out MoonDev's courses and community if you're interested in algorithmic trading and crypto market analysis.

## Quick Setup

### 1. Directory Structure

Before running the scripts, you need to set up the correct directory structure. The project expects the following structure:

```
(project root)/
├── ppls_pos_server.py
├── dashboard_3per.py
├── requirements.txt
├── bots/
│   └── hyperliquid/
│       └── data/
│           └── ppls_positions/
│               └── whale_addresses.txt
```

Create these directories with the following command:

```bash
mkdir -p bots/hyperliquid/data/ppls_positions
```

### 2. Wallet Addresses

You need to create a `whale_addresses.txt` file with the Ethereum addresses you want to track. A sample file is provided as `whale_addresses.txt.sample`. To use it:

```bash
cp bots/hyperliquid/data/ppls_positions/whale_addresses.txt.sample bots/hyperliquid/data/ppls_positions/whale_addresses.txt
```

You can then edit this file to add or remove addresses as needed.

### 3. Finding More Whale Wallets

To find more whale wallets to track, you can use the following resources:

- [HyperLiquid Explorer](https://app.hyperliquid.xyz/explorer) - Official explorer showing recent trades
- [Hypurrscan Dashboard](https://hypurrscan.io/dashboard) - Community-built analytics dashboard
- [Dune Analytics](https://dune.com) - Search for HyperLiquid dashboards
- [Coinglass](https://www.coinglass.com) - For general crypto whale activity

Look for addresses with large position sizes or frequent trading activity.

## For Newcomers to Coding

If you're new to coding or find this setup process intimidating, don't worry! You can leverage AI tools to help you get started:

1. Copy this entire repository into your favorite AI LLM or AI-powered IDE
2. Ask the AI to help you set up and run the project

If you haven't heard of AI coding assistants such as Windsurf, Cursor, Roo Code, etc., I highly recommend you learn how to "vibe code" with these tools. They can significantly reduce the learning curve and help you understand the codebase more quickly.

These AI tools can:

 
- Explain complex parts of the code
- Help troubleshoot errors
- Guide you through the setup process step-by-step
- Suggest modifications based on your specific needs

## Performance Tuning

### Parallel Processing

The `ppls_pos_server.py` script uses parallel processing to fetch data for multiple wallet addresses simultaneously. This significantly improves performance but may cause issues on systems with limited resources.

You can adjust the `MAX_WORKERS` parameter in the script based on your system specifications:

- **Low-end systems** (2 cores/4GB RAM): Set `MAX_WORKERS = 3-5`
- **Mid-range systems** (4 cores/8GB RAM): Set `MAX_WORKERS = 5-8`
- **High-end systems** (8+ cores/16GB+ RAM): Set `MAX_WORKERS = 10-15`

To change this setting, open `ppls_pos_server.py` and look for this section:

```python
# Parallel Processing Configuration
# ---------------------------------
MAX_WORKERS = 10  # Adjust this number based on your system's capabilities
```

## Common Issues and Troubleshooting

### API Rate Limiting

If you experience API rate limiting or connection errors, try:

1. Reducing the `MAX_WORKERS` value
2. Increasing the `API_REQUEST_DELAY` value (default is 0.1 seconds)

### Missing Data

If the dashboard shows incomplete data:

1. Make sure the server script has run successfully at least once
2. Check the data directory for CSV files
3. Verify that your `whale_addresses.txt` file contains valid Ethereum addresses

## Next Steps

After setting up the project:

1. Run the server script to collect data: `python ppls_pos_server.py`
2. Run the dashboard to visualize the data: `python dashboard_3per.py`
3. The dashboard will automatically refresh every 5 minutes

Happy whale tracking!
