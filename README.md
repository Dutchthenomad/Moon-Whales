# HyperLiquid Whale Position Tracker & Dashboard

![Screenshot 2025-04-14 152828](https://github.com/user-attachments/assets/08d8f8e5-4219-4f42-a1e6-2faf50e47916)




## Credits and Acknowledgements

This code was pulled from the 'Day 46' video from the MoonDev Course and all credit must go to him, despite anything referencing Moon Dev in the script being changed to 'Nomad Dev OPS'.

### MoonDev Credits

All credit for this project goes to MoonDev who can be found here:

- Project updates will be posted in Discord, join here: [moondev.com](https://moondev.com)
- Free Algo Trading Roadmap: [moondev.com](https://moondev.com)
- Algo Trading Education: [algotradecamp.com](https://algotradecamp.com)
- Business Contact: moon@algotradecamp.com

MoonDev offers a high quality boot camp and group, and I credit his courses for everything I've done.

The screenshots in this repository are from the `dashboard_3per.py` terminal interface.

## Project Overview

This project fetches and analyzes open positions for a list of specified wallet addresses on the HyperLiquid DEX.

It consists of two main components:

1. **`ppls_pos_server.py`**: Fetches position data from the HyperLiquid API for addresses listed in `whale_addresses.txt`, filters them based on minimum value, and saves the raw and aggregated data to CSV files.
2. **`dashboard_3per.py`**: Reads the generated CSV files and displays a terminal-based dashboard with:
   - Top individual long/short positions.
   - Aggregated long/short exposure per coin.
   - Positions closest to liquidation.
   - Market funding rates.
   - Liquidation threshold analysis.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Create a Python environment (optional but recommended):**
    ```bash
    python -m venv venv
    # Activate the environment (Windows)
    .\venv\Scripts\activate
    # Activate the environment (macOS/Linux)
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Prepare `whale_addresses.txt`:**
    *   Navigate to the `bots/hyperliquid/data/ppls_positions/` directory.
    *   Rename `whale_addresses.txt.sample` to `whale_addresses.txt`.
    *   Edit `whale_addresses.txt` and replace the sample addresses with the actual HyperLiquid wallet addresses you want to track (one address per line).

## Usage

1.  **Fetch Position Data:**
    Run the server script first to gather the latest position data. This will create/update `positions_on_hlp.csv` and `agg_positions_on_hlp.csv` in the `bots/hyperliquid/data/ppls_positions/` directory.
    ```bash
    python ppls_pos_server.py
    ```
    *Note: This can take some time depending on the number of addresses.*

2.  **View the Dashboard:**
3.  ![Screenshot 2025-04-14 152925](https://github.com/user-attachments/assets/988c3d9d-2409-4d8b-b9a5-9cb5074e3d36)
![Screenshot 2025-04-14 152911](https://github.com/user-attachments/assets/970bfb28-c47d-44fb-b3d3-f5dc862fa2c1)

    After the server script finishes, run the dashboard script:
    ```bash
    python dashboard_3per.py
    ```
    The dashboard will automatically refresh the data periodically (currently set to every 5 minutes).

## Files

*   `ppls_pos_server.py`: Data fetching script.
*   `dashboard_3per.py`: Terminal dashboard display script.
*   `nice_funcs.py`: Helper functions used by the dashboard.
*   `requirements.txt`: Python package dependencies.
*   `bots/hyperliquid/data/ppls_positions/`: Directory for data files.
    *   `whale_addresses.txt`: Your list of addresses to track (ignored by git).
    *   `whale_addresses.txt.sample`: Sample file format.
    *   `positions_on_hlp.csv`: Raw position data (ignored by git).
    *   `agg_positions_on_hlp.csv`: Aggregated position data (ignored by git).
*   `.gitignore`: Specifies files/directories for Git to ignore.
*   `README.md`: This file.
