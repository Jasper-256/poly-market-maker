import subprocess
import time
import signal
import os
import json
import math
from dotenv import load_dotenv
from datetime import datetime, timezone
import poly_market_maker.events.get_top_events as get_top_events
from poly_market_maker.utils import setup_web3
from poly_market_maker.clob_api import ClobApi

load_dotenv()

json_file_path = "markets.json"
num_markets_to_make = 2
processes = []

def start_commands(condition_ids):
    """Start all terminal commands."""
    global processes

    refresh_frequency = len(condition_ids) * 6
    port = 9001
    commands = []
    for id in condition_ids:
        commands.append(f'CONDITION_ID="{id}" METRICS_SERVER_PORT="{port}" REFRESH_FREQUENCY="{refresh_frequency}" ./run-local.sh')
        port += 1
    print(commands)

    for command in commands:
        try:
            process = subprocess.Popen(command, shell=True)
            processes.append(process)
            print(f"Started command: {command} with PID {process.pid}")
        except Exception as e:
            print(f"Failed to start command: {command}: {e}")
        wait(6)

def terminate_commands():
    """Terminate all running commands."""
    global processes
    for process in processes:
        try:
            print(f"Terminating PID {process.pid}")
            process.terminate()
        except Exception as e:
            print(f"Failed to terminate process {process.pid}: {e}")

    processes = []

def signal_handler(sig, frame):
    """Handle termination signals to clean up properly."""
    print("Termination signal received. Cleaning up...")
    terminate_commands()
    exit(0)

def get_markets_to_make_json():
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    return data

def overwrite_markets_to_make_json(new_markets):
    try:
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        data = new_markets

        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error: {e}")

def select_and_save_markets():
    account_balance = 200 # Get acount balance here
    num_markets = math.floor(account_balance / 100)

    top_ids = get_top_events.get_top_events(num_markets_to_make)
    overwrite_markets_to_make_json(top_ids)

def cancel_all_orders():
    private_key = os.getenv('PRIVATE_KEY')
    rpc_url = os.getenv('RPC_URL')
    clob_api_url = os.getenv('CLOB_API_URL')
    web3 = setup_web3(rpc_url, private_key)

    clob_api = ClobApi(
        host=clob_api_url,
        chain_id=web3.eth.chain_id,
        private_key=private_key,
    )
    clob_api.cancel_all_orders()

def wait(secs):
    try:
        time.sleep(secs)
    except KeyboardInterrupt:
        # Allow Ctrl+C to terminate
        signal_handler(None, None)

if __name__ == "__main__":
    # Register signal handlers for graceful termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Get existing markets, or fetch new ones if needed
    markets = get_markets_to_make_json()
    if markets == []:
        print("Getting new markets to make...")
        select_and_save_markets()
        markets = get_markets_to_make_json()

    print("Starting to make these markets:")
    print(markets)
    start_commands(markets)

    while True:
        # Cancel all orders every hour for more optimal order placement
        wait(60 * 60)
        cancel_all_orders()

        # current_time_utc = datetime.now(timezone.utc)
        # hour = current_time_utc.hour
        # minute = current_time_utc.minute

        # if hour == 23 and minute >= 55:
        #     print("Ending all commands...")
        #     terminate_commands()
        #     wait(5 * 60)

        #     # Sell everything

        #     print("Getting new markets to make...")
        #     select_and_save_markets()
        #     markets = get_markets_to_make_json()

        #     print("Starting to make these markets:")
        #     print(markets)
        #     start_commands(markets)
