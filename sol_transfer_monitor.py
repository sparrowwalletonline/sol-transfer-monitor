#!/usr/bin/env python3
"""
Solana Transfer Monitor for TradingView
Monitors SOL transfers between Binance and Wintermute wallets
Outputs data compatible with TradingView custom indicators
"""

import requests
import json
import time
import csv
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

class SolanaTransferMonitor:
    def __init__(self):
        # Solana Public RPC endpoint (free)
        self.rpc_url = "https://api.mainnet-beta.solana.com"
        
        # Wallet addresses
        self.binance_wallet = "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9"
        
        self.wintermute_wallets = [
            "77DXFZnMebramt4dXfdwem1AjnfNnVnG8FkcVWpSwdjB",  # Gate.io Deposit
            "ApQnTEGUNsKsM48AjFLy1yDukBwk8WgjorYe6KduVmnr",  # Backpack Exchange Deposit
            "44P5Ct5JkPz76Rs2K6juC65zXMpFRDrHatxcASJ4Dyra",  # Hot Wallet
            "42nh6ig8ADj87iLpqtn7EzXk4yVg1X2LZtCJdaabHMEw",  # KuCoin Deposit
            "4DTTpRo9BtATsVgxtiLtnFRLxiYGhCtuXrJ2njs2tgJC",  # OKX Deposit
            "BFAcmjQFzvxL1xEejUHVUcnAqq5yWhmKUyh3uSeTRoCz"   # Bitvavo
        ]
        
        # All monitored wallets
        self.all_wallets = [self.binance_wallet] + self.wintermute_wallets
        
        # File to store transfer data for TradingView
        self.output_file = "sol_transfers.csv"
        self.processed_signatures = set()
        self.load_processed_signatures()
        
        # Initialize CSV file
        self.init_csv_file()
    
    def load_processed_signatures(self):
        """Load previously processed transaction signatures to avoid duplicates"""
        try:
            if os.path.exists("processed_signatures.txt"):
                with open("processed_signatures.txt", "r") as f:
                    self.processed_signatures = set(line.strip() for line in f)
        except Exception as e:
            print(f"Error loading processed signatures: {e}")
    
    def save_processed_signature(self, signature: str):
        """Save processed signature to avoid reprocessing"""
        self.processed_signatures.add(signature)
        try:
            with open("processed_signatures.txt", "a") as f:
                f.write(f"{signature}\n")
        except Exception as e:
            print(f"Error saving signature: {e}")
    
    def init_csv_file(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.output_file):
            with open(self.output_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "unix_timestamp", "signature", "from_wallet", 
                    "to_wallet", "amount_sol", "direction", "wintermute_wallet_type"
                ])
    
    def make_rpc_request(self, method: str, params: List) -> Optional[Dict]:
        """Make RPC request to Solana node"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            response = requests.post(self.rpc_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"RPC request error: {e}")
            return None
    
    def get_wallet_transactions(self, wallet_address: str, limit: int = 50) -> List[Dict]:
        """Get recent transactions for a wallet"""
        params = [
            wallet_address,
            {
                "limit": limit,
                "commitment": "confirmed"
            }
        ]
        
        result = self.make_rpc_request("getSignaturesForAddress", params)
        if result and "result" in result:
            return result["result"]
        return []
    
    def get_transaction_details(self, signature: str) -> Optional[Dict]:
        """Get detailed transaction information"""
        params = [
            signature,
            {
                "encoding": "json",
                "commitment": "confirmed",
                "maxSupportedTransactionVersion": 0
            }
        ]
        
        result = self.make_rpc_request("getTransaction", params)
        if result and "result" in result:
            return result["result"]
        return None
    
    def parse_sol_transfer(self, tx_details: Dict, signature: str) -> Optional[Dict]:
        """Parse SOL transfer from transaction details"""
        try:
            if not tx_details or "meta" not in tx_details:
                return None
            
            meta = tx_details["meta"]
            if meta.get("err"):  # Skip failed transactions
                return None
            
            # Get account keys
            message = tx_details["transaction"]["message"]
            account_keys = message["accountKeys"]
            
            # Get pre and post balances
            pre_balances = meta["preBalances"]
            post_balances = meta["postBalances"]
            
            # Find transfers between our monitored wallets
            for i, account in enumerate(account_keys):
                if account in self.all_wallets:
                    balance_change = post_balances[i] - pre_balances[i]
                    
                    if abs(balance_change) > 0:  # There was a balance change
                        # Find the counterpart wallet
                        for j, other_account in enumerate(account_keys):
                            if (other_account in self.all_wallets and 
                                other_account != account and
                                abs(post_balances[j] - pre_balances[j]) > 0):
                                
                                # Determine direction
                                if balance_change < 0:  # This wallet sent SOL
                                    from_wallet = account
                                    to_wallet = other_account
                                    amount = abs(balance_change) / 1e9  # Convert lamports to SOL
                                else:  # This wallet received SOL
                                    from_wallet = other_account
                                    to_wallet = account
                                    amount = balance_change / 1e9
                                
                                # Check if this is a Binance <-> Wintermute transfer
                                if ((from_wallet == self.binance_wallet and to_wallet in self.wintermute_wallets) or
                                    (from_wallet in self.wintermute_wallets and to_wallet == self.binance_wallet)):
                                    
                                    return {
                                        "signature": signature,
                                        "from_wallet": from_wallet,
                                        "to_wallet": to_wallet,
                                        "amount_sol": amount,
                                        "timestamp": tx_details["blockTime"]
                                    }
            
            return None
            
        except Exception as e:
            print(f"Error parsing transaction {signature}: {e}")
            return None
    
    def get_wallet_type(self, wallet_address: str) -> str:
        """Get descriptive name for wallet"""
        wallet_types = {
            "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9": "Binance Hot Wallet",
            "77DXFZnMebramt4dXfdwem1AjnfNnVnG8FkcVWpSwdjB": "Gate.io Deposit Wintermute",
            "ApQnTEGUNsKsM48AjFLy1yDukBwk8WgjorYe6KduVmnr": "Backpack Exchange Deposit Wintermute",
            "44P5Ct5JkPz76Rs2K6juC65zXMpFRDrHatxcASJ4Dyra": "Wintermute Hot Wallet",
            "42nh6ig8ADj87iLpqtn7EzXk4yVg1X2LZtCJdaabHMEw": "KuCoin Wintermute Deposit",
            "4DTTpRo9BtATsVgxtiLtnFRLxiYGhCtuXrJ2njs2tgJC": "OKX Deposit Wintermute",
            "BFAcmjQFzvxL1xEejUHVUcnAqq5yWhmKUyh3uSeTRoCz": "Bitvavo Wintermute"
        }
        return wallet_types.get(wallet_address, "Unknown Wallet")
    
    def save_transfer(self, transfer: Dict):
        """Save transfer to CSV file"""
        try:
            # Determine direction
            if transfer["from_wallet"] == self.binance_wallet:
                direction = "Binance_to_Wintermute"
                wintermute_wallet = self.get_wallet_type(transfer["to_wallet"])
            else:
                direction = "Wintermute_to_Binance"
                wintermute_wallet = self.get_wallet_type(transfer["from_wallet"])
            
            # Convert timestamp
            dt = datetime.fromtimestamp(transfer["timestamp"], tz=timezone.utc)
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # Write to CSV
            with open(self.output_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp_str,
                    transfer["timestamp"],
                    transfer["signature"],
                    transfer["from_wallet"],
                    transfer["to_wallet"],
                    f"{transfer['amount_sol']:.6f}",
                    direction,
                    wintermute_wallet
                ])
            
            print(f"✅ NEW TRANSFER: {direction}")
            print(f"   Amount: {transfer['amount_sol']:.6f} SOL")
            print(f"   Time: {timestamp_str}")
            print(f"   Wintermute Wallet: {wintermute_wallet}")
            print(f"   Signature: {transfer['signature']}")
            print("-" * 60)
            
        except Exception as e:
            print(f"Error saving transfer: {e}")
    
    def monitor_transfers(self):
        """Main monitoring loop"""
        print("🚀 Starting SOL Transfer Monitor")
        print(f"📊 Monitoring Binance ↔ Wintermute transfers")
        print(f"💾 Output file: {self.output_file}")
        print(f"🔄 Checking every 90 seconds...")
        print("-" * 60)
        
        while True:
            try:
                print(f"🔍 Checking for new transfers... {datetime.now().strftime('%H:%M:%S')}")
                
                # Check all wallets for new transactions
                for wallet in self.all_wallets:
                    transactions = self.get_wallet_transactions(wallet, limit=20)
                    
                    for tx in transactions:
                        signature = tx["signature"]
                        
                        # Skip if already processed
                        if signature in self.processed_signatures:
                            continue
                        
                        # Get transaction details
                        tx_details = self.get_transaction_details(signature)
                        if not tx_details:
                            continue
                        
                        # Parse for SOL transfers
                        transfer = self.parse_sol_transfer(tx_details, signature)
                        if transfer:
                            self.save_transfer(transfer)
                        
                        # Mark as processed
                        self.save_processed_signature(signature)
                
                # Wait before next check
                time.sleep(90)  # 1.5 minutes
                
            except KeyboardInterrupt:
                print("\n⏹️  Monitor stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                print("⏳ Waiting 30 seconds before retry...")
                time.sleep(30)

def main():
    monitor = SolanaTransferMonitor()
    monitor.monitor_transfers()

if __name__ == "__main__":
    main()
