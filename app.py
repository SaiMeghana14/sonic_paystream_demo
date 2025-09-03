import streamlit as st
from web3 import Web3
import json
import time
import pandas as pd
import plotly.express as px
from streamlit_lottie import st_lottie
from streamlit_javascript import st_javascript
import requests

# Dictionary to store all active streams
active_streams = {}  # key: stream_id, value: dict(sender, receiver, rate, deposit, start_time, running)

# =======================
# CONFIG
# =======================
st.set_page_config(
    page_title="Sonic PayStream 🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =======================
# Load secrets safely
# =======================
RPC_URL = st.secrets.get("SONIC_RPC", "https://rpc.sonicchain.io")
CONTRACT_ADDRESS = st.secrets.get("CONTRACT_ADDRESS", "0x0000000000000000000000000000000000000000")
PRIVATE_KEY = st.secrets.get("PRIVATE_KEY", None)  # optional

# =======================
# Web3 Setup (Sonic Testnet)
# =======================
w3 = Web3(Web3.HTTPProvider(RPC_URL))

with open("sonic_contract.json") as f:
    contract_abi = json.load(f)

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

# =======================
# Lottie Loader
# =======================
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

landing_lottie = load_lottie_url("https://assets9.lottiefiles.com/packages/lf20_touohxv0.json")
stream_lottie = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_jbrw3hcz.json")
success_lottie = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_u4yrau.json")

# =======================
# Coin Animation HTML
# =======================
def coin_animation_html():
    return """
    <style>
    .coin-container {
        position: relative;
        height: 150px;
        overflow: hidden;
        margin-bottom: 10px;
    }
    .coin {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: gold;
        position: absolute;
        top: 50%;
        animation: moveCoin 3s linear infinite;
    }
    @keyframes moveCoin {
        0% { left: 0%; transform: translateY(-50%) rotate(0deg); }
        50% { left: 50%; transform: translateY(-50%) rotate(180deg); }
        100% { left: 100%; transform: translateY(-50%) rotate(360deg); }
    }
    </style>
    <div class="coin-container">
        <div class="coin"></div>
        <div class="coin" style="animation-delay: 0.5s;"></div>
        <div class="coin" style="animation-delay: 1s;"></div>
        <div class="coin" style="animation-delay: 1.5s;"></div>
    </div>
    """

# =======================
# Landing Page
# =======================
st_lottie(landing_lottie, height=300, key="landing")
st.title("Sonic PayStream 💸")
st.markdown("Stream money in real-time 🚀 Pay per second for services, freelancers, or IoT devices.")

# =======================
# MetaMask Wallet Connect
# =======================
st.sidebar.title("Wallet Connection")
st.sidebar.markdown("Connect your MetaMask wallet to interact on-chain.")

connected_wallet = st_javascript(
    "async () => { const accounts = await ethereum.request({ method: 'eth_requestAccounts' }); return accounts[0]; }"
)

if connected_wallet:
    st.sidebar.success(f"Wallet connected: {connected_wallet}")
else:
    st.sidebar.warning("Please connect MetaMask.")

# =======================
# Stream Controls
# =======================
st.sidebar.subheader("Start a New Stream")

# Generate a unique Stream ID
stream_id = st.sidebar.number_input("Stream ID (Unique)", min_value=1, value=len(active_streams)+1, step=1)
receiver_address = st.sidebar.text_input("Receiver Wallet")
deposit_amount = st.sidebar.number_input("Deposit Amount (ETH)", min_value=0.001, value=0.01, step=0.001)
rate_per_second = st.sidebar.number_input("Rate per Second (ETH)", min_value=0.000001, value=0.00001, step=0.000001)

if st.sidebar.button("Start Stream") and connected_wallet and receiver_address:
    # Store stream in active_streams
    active_streams[stream_id] = {
        "sender": connected_wallet,
        "receiver": receiver_address,
        "rate": rate_per_second,
        "deposit": deposit_amount,
        "start_time": time.time(),
        "running": True
    }
    st.success(f"Stream {stream_id} started: {connected_wallet} → {receiver_address} at {rate_per_second} ETH/sec")

    # Loop through all active streams
for sid, stream in active_streams.items():
    if stream["running"]:
        st.subheader(f"Stream ID: {sid} → {stream['sender']} → {stream['receiver']}")
        st_lottie(stream_lottie, height=150, key=f"lottie_{sid}")
        st.markdown(coin_animation_html(), unsafe_allow_html=True)

        progress_bar = st.progress(0, key=f"progress_{sid}")
        balance_text = st.empty()
        df = pd.DataFrame(columns=["Time (s)", "Balance (ETH)"])
        stop_btn = st.empty()

        # Inner loop for each stream
        while stream["running"]:
            elapsed = time.time() - stream["start_time"]
            total_received = elapsed * stream["rate"]
            balance_text.text(f"Receiver Balance: {total_received:.6f} ETH")
            progress_bar.progress(min(int((total_received/stream["deposit"])*100), 100))

            df = pd.concat([df, pd.DataFrame([[elapsed, total_received]], columns=["Time (s)", "Balance (ETH)"])], ignore_index=True)
            fig = px.line(df, x="Time (s)", y="Balance (ETH)", title=f"Streaming Balance Over Time (ID {sid})", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

            # Cancel button per stream
            if stop_btn.button(f"Cancel Stream {sid}"):
                stream["running"] = False
                st.warning(f"Stream {sid} cancelled ⏹️")
                break

            if total_received >= stream["deposit"]:
                stream["running"] = False
                st.success(f"Stream {sid} completed! 🎉")
                st_lottie(success_lottie, height=150, key=f"success_{sid}")

            time.sleep(1)

    # Coin animation
    st.markdown(coin_animation_html(), unsafe_allow_html=True)

    start_time = time.time()
    progress_bar = st.progress(0)
    balance_text = st.empty()
    df = pd.DataFrame(columns=["Time (s)", "Balance (ETH)"])
    running = True
    stop_stream_btn = st.empty()

      
# =======================
# Withdraw Funds/Stop Stream On-chain
# =======================
st.sidebar.subheader("Withdraw Funds / Stop Stream")
stream_id_action = st.sidebar.number_input("Stream ID", min_value=1, step=1)

if st.sidebar.button("Withdraw Stream"):
    try:
        tx = contract.functions.withdraw(int(stream_id_action)).buildTransaction({
            "from": connected_wallet,
            "gas": 200000
        })
        st.success(f"Withdrawn from Stream ID: {stream_id_action} 🚀")
    except Exception as e:
        st.error(f"Error: {e}")

if st.sidebar.button("Stop Stream On-chain"):
    try:
        tx = contract.functions.stopStream(int(stream_id_action)).buildTransaction({
            "from": connected_wallet,
            "gas": 200000
        })
        st.success(f"Stream ID {stream_id_action} stopped ⏹️")
        # Also stop local dashboard
        if stream_id_action in active_streams:
            active_streams[stream_id_action]["running"] = False
    except Exception as e:
        st.error(f"Error: {e}")

# =======================
# Footer
# =======================
st.markdown("---")
st.markdown("Made with ❤️ for Sonic S Tier Hackathon")
