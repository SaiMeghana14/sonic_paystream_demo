import streamlit as st 
from web3 import Web3
import json
import time
import pandas as pd
import plotly.express as px
from streamlit_lottie import st_lottie
from streamlit_javascript import st_javascript
import requests

# =======================
# GLOBALS
# =======================
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
# Wallet Connection
# =======================
st.sidebar.title("Wallet Connection")
st.sidebar.markdown("Connect your MetaMask wallet to interact on-chain.")

try:
    connected_wallet = st_javascript("""
    () => {
        return new Promise((resolve, reject) => {
            ethereum.request({ method: 'eth_requestAccounts' })
            .then(accounts => resolve(accounts[0]))
            .catch(err => resolve(null));
        });
    }
    """)
except:
    connected_wallet = None

if connected_wallet:
    st.sidebar.success(f"Wallet connected: {connected_wallet}")
else:
    connected_wallet = st.sidebar.text_input("Manual Wallet Address (fallback):")
    if connected_wallet:
        st.sidebar.info(f"Using manual wallet: {connected_wallet}")
    else:
        st.sidebar.warning("⚠️ Please connect MetaMask or enter manually.")

# =======================
# Main Tabs
# =======================
st_lottie(landing_lottie, height=250, key="landing")
st.title("⚡ Sonic PayStream – Real-Time Micro-Payments")
st.markdown("🚀 Stream money in real-time. Pay per second for services, freelancers, IoT devices, or gaming.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["💳 Start Stream", "📊 Dashboard", "📈 Analytics", "📤 Export", "🌍 Use Cases"])

# --- Tab 1: Start Stream ---
with tab1:
    st.subheader("Create a Payment Stream")
    stream_id = st.number_input("Stream ID (Unique)", min_value=1, value=len(active_streams)+1, step=1)
    receiver_address = st.text_input("Receiver Wallet")
    deposit_amount = st.number_input("Deposit Amount (ETH)", min_value=0.001, value=0.01, step=0.001)
    rate_per_second = st.number_input("Rate per Second (ETH)", min_value=0.000001, value=0.00001, step=0.000001)

    if st.button("🚀 Start Stream") and connected_wallet and receiver_address:
        active_streams[stream_id] = {
            "sender": connected_wallet,
            "receiver": receiver_address,
            "rate": rate_per_second,
            "deposit": deposit_amount,
            "start_time": time.time(),
            "running": True
        }
        st.success(f"✅ Stream {stream_id} started: {connected_wallet} → {receiver_address} at {rate_per_second} ETH/sec")

# --- Tab 2: Dashboard ---
with tab2:
    st.subheader("Active Streams Dashboard")
    if active_streams:
        df = pd.DataFrame.from_dict(active_streams, orient="index")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No active streams yet.")

# --- Tab 3: Analytics ---
with tab3:
    st.subheader("Streaming Analytics")
    if active_streams:
        for sid, stream in active_streams.items():
            elapsed = time.time() - stream["start_time"]
            total_received = elapsed * stream["rate"]
            remaining = stream["deposit"] - total_received
            chart_df = pd.DataFrame({
                "Time (s)": [elapsed],
                "Withdrawn (ETH)": [total_received],
                "Remaining (ETH)": [remaining]
            })
            fig = px.bar(chart_df, x=["Withdrawn (ETH)", "Remaining (ETH)"], y=[elapsed], orientation="h", title=f"Stream {sid} Balance")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No streams to analyze.")

# --- Tab 4: Export ---
with tab4:
    st.subheader("Export Stream Data")
    if active_streams:
        df = pd.DataFrame.from_dict(active_streams, orient="index")
        st.download_button("📥 Download CSV", df.to_csv(index=False), "streams.csv", "text/csv")
    else:
        st.warning("No data available to export.")

# --- Tab 5: Use Cases ---
with tab5:
    st.subheader("🌍 Real-World Applications of Sonic PayStream")
    st.markdown("""
    - 🎬 **Content Platforms** → Pay per minute for video/music instead of subscriptions.  
    - 👨‍💻 **Freelancers** → Get paid per second of work instantly.  
    - 🔌 **IoT Devices** → EV charging, cloud compute, smart meters billed per second.  
    - 🎮 **Gaming/Metaverse** → Pay as you play, per level or hour.  
    """)

# =======================
# Footer
# =======================
st.markdown("---")
st.markdown("Made with ❤️ for **Sonic S Tier Hackathon** ⚡")
