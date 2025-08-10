# SOL Transfer Monitor - Binance ↔ Wintermute

This application monitors SOL transfers between Binance and Wintermute wallets in real-time.

## Monitored Wallets

### Binance
- `5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9` (Binance Hot Wallet)

### Wintermute
- `77DXFZnMebramt4dXfdwem1AjnfNnVnG8FkcVWpSwdjB` (Gate.io Deposit Wintermute)
- `ApQnTEGUNsKsM48AjFLy1yDukBwk8WgjorYe6KduVmnr` (Backpack Exchange Deposit Wintermute)
- `44P5Ct5JkPz76Rs2K6juC65zXMpFRDrHatxcASJ4Dyra` (Wintermute Hot Wallet)
- `42nh6ig8ADj87iLpqtn7EzXk4yVg1X2LZtCJdaabHMEw` (KuCoin Wintermute Deposit)
- `4DTTpRo9BtATsVgxtiLtnFRLxiYGhCtuXrJ2njs2tgJC` (OKX Deposit Wintermute)
- `BFAcmjQFzvxL1xEejUHVUcnAqq5yWhmKUyh3uSeTRoCz` (Bitvavo Wintermute)

## Features

- ✅ Real-time monitoring every 90 seconds
- ✅ Detects transfers in both directions
- ✅ Uses free Solana Public RPC
- ✅ Outputs transfer data to CSV
- ✅ Prevents duplicate processing
- ✅ Console alerts for new transfers

## Deployment

This app is configured for Railway deployment. Simply:

1. Fork this repository
2. Connect to Railway
3. Deploy automatically

## Output

The monitor creates `sol_transfers.csv` with columns:
- timestamp
- unix_timestamp  
- signature
- from_wallet
- to_wallet
- amount_sol
- direction
- wintermute_wallet_type
