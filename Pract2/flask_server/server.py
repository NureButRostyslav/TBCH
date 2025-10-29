import json
import os
from flask import Flask, request, jsonify
from web3 import Web3
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure provider to point to local hardhat node
# Default: http://127.0.0.1:8545
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# load deployed ABI & addresses
BASE = os.path.join(os.path.dirname(__file__), "contract_info")
def load_contract(name):
    p = os.path.join(BASE, f"{name}.json")
    with open(p) as f:
        data = json.load(f)
    return w3.eth.contract(address=w3.to_checksum_address(data["address"]), abi=data["abi"])

UserRegistry = load_contract("UserRegistry")
code = w3.eth.get_code(UserRegistry.address)
if code == b"0x" or code == b"":
    raise Exception(f"Contract not deployed at {UserRegistry.address}")

DataStore = load_contract("DataStore")
ConditionalExecutor = load_contract("ConditionalExecutor")

# use first local account as default sender (Hardhat provides unlocked accounts)
DEFAULT_ACCOUNT = w3.eth.accounts[0] if w3.eth.accounts else None

# ------------------------------
# Register user
# ------------------------------
@app.route("/register", methods=["POST"])
def register():
    payload = request.json
    username = payload.get("username")
    account = payload.get("account") or DEFAULT_ACCOUNT

    try:
        # Build tx
        tx = UserRegistry.functions.register(username).build_transaction({
            "from": account,
            "nonce": w3.eth.get_transaction_count(account),
            "gas": 3000000,
            "gasPrice": w3.to_wei("1", "gwei")
        })

        # Send transaction
        tx_hash = w3.eth.send_transaction({
            "from": account,
            "to": UserRegistry.address,
            "data": tx["data"],
            "gas": tx["gas"]
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        registered = UserRegistry.functions.isRegistered(account).call()

        return jsonify({
            "txHash": receipt.transactionHash.hex(),
            "registered": registered
        })

    except ValueError as e:
        # Catch revert errors
        err_msg = str(e)
        if "Already registered" in err_msg:
            return jsonify({"error": "User already registered"}), 400
        else:
            return jsonify({"error": "Transaction failed", "details": err_msg}), 500


# ------------------------------
# Save data
# ------------------------------
@app.route("/save_data", methods=["POST"])
def save_data():
    payload = request.json
    data = payload.get("data")
    account = payload.get("account") or DEFAULT_ACCOUNT

    tx = DataStore.functions.save(data).build_transaction({
        "from": account,
        "nonce": w3.eth.get_transaction_count(account),
        "gas": 3000000,
        "gasPrice": w3.to_wei("1", "gwei")
    })

    tx_hash = w3.eth.send_transaction({
        "from": account,
        "to": DataStore.address,
        "data": tx["data"],
        "gas": tx["gas"]
    })
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Verify last saved data
    items = DataStore.functions.getItemsOf(account).call()
    last_item_id = items[-1] if items else None
    last_item = None
    if last_item_id is not None:
        it = DataStore.functions.getItem(last_item_id).call()
        last_item = {
            "id": it[0],
            "owner": it[1],
            "data": it[2],
            "createdAt": it[3]
        }

    return jsonify({
        "txHash": receipt.transactionHash.hex(),
        "lastItem": last_item
    })


# ------------------------------
# Get items of owner
# ------------------------------
@app.route("/items/<owner>", methods=["GET"])
def items_of(owner):
    try:
        owner = w3.to_checksum_address(owner)
    except:
        return jsonify({"error": "invalid address"}), 400

    ids = DataStore.functions.getItemsOf(owner).call()
    items = []
    for i in ids:
        it = DataStore.functions.getItem(i).call()
        items.append({
            "id": it[0],
            "owner": it[1],
            "data": it[2],
            "createdAt": it[3]
        })
    return jsonify(items)


# ------------------------------
# Deposit conditional
# ------------------------------
@app.route("/deposit_conditional", methods=["POST"])
def deposit_conditional():
    payload = request.json
    account = payload.get("account") or DEFAULT_ACCOUNT
    value_eth = payload.get("value_eth", 0)

    tx_hash = w3.eth.send_transaction({
        "from": account,
        "to": ConditionalExecutor.address,
        "value": w3.to_wei(value_eth, "ether"),
        "gas": 2000000,
        "nonce": w3.eth.get_transaction_count(account),
        "gasPrice": w3.to_wei("1", "gwei")
    })
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    executed = ConditionalExecutor.functions.executed().call()

    return jsonify({
        "txHash": receipt.transactionHash.hex(),
        "executed": executed
    })


# ------------------------------
# Get contract addresses
# ------------------------------
@app.route("/contract_addresses", methods=["GET"])
def get_contract_addresses():
    return jsonify({
        "UserRegistry": UserRegistry.address,
        "DataStore": DataStore.address,
        "ConditionalExecutor": ConditionalExecutor.address
    })

if __name__ == "__main__":
    print("Web3 connected:", w3.is_connected())
    print("Default account:", DEFAULT_ACCOUNT)
    app.run(host="0.0.0.0", port=5000, debug=True)
