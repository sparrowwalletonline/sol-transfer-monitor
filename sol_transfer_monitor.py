#!/usr/bin/env python3
"""
Solana Transfer Monitor for TradingView - DEBUG VERSION
Monitors SOL transfers between Binance and Wintermute wallets
Includes test mode and enhanced debugging
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
        # Helius RPC endpoint - REPLACE WITH YOUR ACTUAL API KEY
        self.rpc_url = "https://mainnet.helius-rpc.com/?api-key=77ef3d2b-8a69-4c84-ba27-94e8b3fb4a10"
        
        # Webhook URL for real-time notifications
        self.webhook_url = "https://webhook.site/88e50446-696a-4776-ab3f-8e0f4804cffb"
        
        # TEST MODE - Set to True to send fake transfers every 2 minutes
        self.test_mode = False
        self.test_counter = 0
        
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
    
    def send_test_webhook(self):
        """Send test webhook to verify connection"""
        self.test_counter += 1
        
        # Fake test transfers
        test_transfers = [
            {
                "signature": f"TEST_SIGNATURE_{self.test_counter}",
                "from_wallet": self.binance_wallet,
                "to_wallet": "42nh6ig8ADj87iLpqtn7EzXk4yVg1X2LZtCJdaabHMEw",  # KuCoin
                "from_wallet_name": "Binance Hot Wallet",
                "to_wallet_name": "KuCoin Wintermute Deposit",
                "amount_sol": 750.5 + (self.test_counter * 10),
                "direction": "Binance_to_Wintermute",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "unix_timestamp": int(time.time()),
                "wintermute_wallet": "KuCoin Wintermute Deposit"
            },
            {
                "signature": f"TEST_SIGNATURE_MEGA_{self.test_counter}",
                "from_wallet": self.binance_wallet,
                "to_wallet": "4DTTpRo9BtATsVgxtiLtnFRLxiYGhCtuXrJ2njs2tgJC",  # OKX
                "from_wallet_name": "Binance Hot Wallet",
                "to_wallet_name": "OKX Deposit Wintermute",
                "amount_sol": 1250.0 + (self.test_counter * 50),
                "direction": "Binance_to_Wintermute",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "unix_timestamp": int(time.time()),
                "wintermute_wallet": "OKX Deposit Wintermute"
            }
        ]
        
        # Send one of the test transfers
        test_transfer = test_transfers[self.test_counter % 2]
        
        try:
            webhook_payload = {
                "event": "whale_transfer",
                "timestamp": datetime.now().isoformat(),
                "transfer": test_transfer,
                "alert_level": "MEGA_WHALE" if test_transfer["amount_sol"] >= 1000 else "WHALE",
                "test_mode": True
            }
            
            response = requests.post(
                self.webhook_url,
                json=webhook_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"🧪 TEST WEBHOOK SENT: {test_transfer['amount_sol']} SOL")
                print(f"   Direction: {test_transfer['direction']}")
                print(f"   Wallet: {test_transfer['wintermute_wallet']}")
                print(f"   Status: ✅ SUCCESS")
            else:
                print(f"❌ TEST WEBHOOK FAILED: {response.status_code}")
                
        except Exception as e:
            print(f"❌ TEST WEBHOOK ERROR: {e}")
    
    def load_processed_signatures(self):
        """Load previously processed transaction signatures to avoid duplicates"""
        try:
            if os.path.exists("processed_signatures.txt"):
                with open("processed_signatures.txt", "r") as f:
                    self.processed_signatures = set(line.strip() for line in f)
                    print(f"📝 Loaded {len(self.processed_signatures)} processed signatures")
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
        """Make RPC request to Solana node with enhanced error handling"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            print(f"🔍 Making RPC request: {method}")
            response = requests.post(self.rpc_url, json=payload, timeout=30)
            
            if response.status_code == 429:
                print("⚠️  Rate limited - waiting 10 seconds...")
                time.sleep(10)
                return None
            
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                print(f"❌ RPC Error: {result['error']}")
                return None
                
            return result
            
        except requests.exceptions.Timeout:
            print("⏰ RPC request timed out")
            return None
        except Exception as e:
            print(f"❌ RPC request error: {e}")
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
            transactions = result["result"]
            print(f"📊 Found {len(transactions)} transactions for wallet {wallet_address[:8]}...")
            return transactions
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
        """Parse SOL transfer from transaction details with enhanced debugging"""
        try:
            if not tx_details or "meta" not in tx_details:
                print(f"⚠️  No meta data for transaction {signature[:8]}...")
                return None
            
            meta = tx_details["meta"]
            if meta.get("err"):  # Skip failed transactions
                print(f"❌ Failed transaction {signature[:8]}...")
                return None
            
            # Get account keys
            message = tx_details["transaction"]["message"]
            account_keys = message["accountKeys"]
            
            # Get pre and post balances
            pre_balances = meta["preBalances"]
            post_balances = meta["postBalances"]
            
            print(f"🔍 Analyzing transaction {signature[:8]}... with {len(account_keys)} accounts")
            
            # Find transfers between our monitored wallets
            for i, account in enumerate(account_keys):
                if account in self.all_wallets:
                    balance_change = post_balances[i] - pre_balances[i]
                    
                    if abs(balance_change) > 0:  # There was a balance change
                        amount_sol = abs(balance_change) / 1e9
                        print(f"💰 Balance change detected: {amount_sol:.6f} SOL for {account[:8]}...")
                        
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
                                    
                                    print(f"🎯 FOUND BINANCE ↔ WINTERMUTE TRANSFER!")
                                    print(f"   From: {from_wallet[:8]}...")
                                    print(f"   To: {to_wallet[:8]}...")
                                    print(f"   Amount: {amount:.6f} SOL")
                                    
                                    return {
                                        "signature": signature,
                                        "from_wallet": from_wallet,
                                        "to_wallet": to_wallet,
                                        "amount_sol": amount,
                                        "timestamp": tx_details["blockTime"]
                                    }
            
            return None
            
        except Exception as e:
            print(f"❌ Error parsing transaction {signature}: {e}")
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
    
    def send_webhook(self, transfer_data: Dict):
        """Send transfer data to webhook for real-time notifications"""
        try:
            # Prepare webhook payload
            webhook_payload = {
                "event": "whale_transfer",
                "timestamp": datetime.now().isoformat(),
                "transfer": transfer_data,
                "alert_level": "MEGA_WHALE" if transfer_data["amount_sol"] >= 1000 else "WHALE",
                "test_mode": False
            }
            
            # Send webhook
            response = requests.post(
                self.webhook_url,
                json=webhook_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"🔗 REAL WEBHOOK SENT SUCCESSFULLY!")
            else:
                print(f"⚠️  Webhook failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Webhook error: {e}")

    def save_transfer(self, transfer: Dict):
        """Save transfer to CSV file and send webhook"""
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
            
            # Prepare transfer data for webhook
            transfer_data = {
                "signature": transfer["signature"],
                "from_wallet": transfer["from_wallet"],
                "to_wallet": transfer["to_wallet"],
                "from_wallet_name": self.get_wallet_type(transfer["from_wallet"]),
                "to_wallet_name": self.get_wallet_type(transfer["to_wallet"]),
                "amount_sol": round(transfer["amount_sol"], 6),
                "direction": direction,
                "timestamp": timestamp_str,
                "unix_timestamp": transfer["timestamp"],
                "wintermute_wallet": wintermute_wallet
            }
            
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
            
            # Send webhook notification
            self.send_webhook(transfer_data)
            
            # Console output
            print(f"🐋 NEW WHALE TRANSFER: {direction}")
            print(f"   💰 Amount: {transfer['amount_sol']:.6f} SOL")
            print(f"   ⏰ Time: {timestamp_str}")
            print(f"   🏦 Wintermute Wallet: {wintermute_wallet}")
            print(f"   📝 Signature: {transfer['signature']}")
            print(f"   🔗 Webhook: Sent to TradingView")
            print("-" * 60)
            
        except Exception as e:
            print(f"Error saving transfer: {e}")
    
    def monitor_transfers(self):
        """Main monitoring loop with test mode"""
        print("🚀 Starting SOL Transfer Monitor - DEBUG VERSION")
        print(f"📊 Monitoring Binance ↔ Wintermute transfers")
        print(f"💾 Output file: {self.output_file}")
        print(f"🔗 Webhook URL: {self.webhook_url}")
        print(f"🧪 Test Mode: {'ENABLED' if self.test_mode else 'DISABLED'}")
        print(f"🔄 Checking every 90 seconds...")
        print("-" * 60)
        
        # Send initial test webhook
        if self.test_mode:
            print("🧪 Sending initial test webhook...")
            self.send_test_webhook()
        
        while True:
            try:
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"🔍 Checking for new transfers... {current_time}")
                
                # Send test webhook every 2 minutes in test mode
                if self.test_mode and int(time.time()) % 120 < 90:
                    self.send_test_webhook()
                
                # Check all wallets for new transactions
                for wallet in self.all_wallets:
                    wallet_name = self.get_wallet_type(wallet)
                    print(f"🔍 Checking {wallet_name}...")
                    
                    transactions = self.get_wallet_transactions(wallet, limit=10)
                    
                    for tx in transactions:
                        signature = tx["signature"]
                        
                        # Skip if already processed
                        if signature in self.processed_signatures:
                            continue
                        
                        print(f"🆕 New transaction found: {signature[:8]}...")
                        
                        # Get transaction details
                        tx_details = self.get_transaction_details(signature)
                        if not tx_details:
                            print(f"⚠️  Could not get details for {signature[:8]}...")
                            continue
                        
                        # Parse for SOL transfers
                        transfer = self.parse_sol_transfer(tx_details, signature)
                        if transfer:
                            self.save_transfer(transfer)
                        
                        # Mark as processed
                        self.save_processed_signature(signature)
                
                # Wait before next check
                print(f"⏳ Waiting 90 seconds before next check...")
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
