import streamlit as st
from web3 import Web3
import json
import time
import pandas as pd
import plotly.express as px
from streamlit_lottie import st_lottie
import requests

# =======================
# CONFIG
# =======================
st.set_page_config(
    page_title="Sonic PayStream 🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Connect to Sonic Testnet RPC
RPC_URL = "https://rpc.sonicchain.io"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Load contract ABI
with open("sonic_contract.json") as f:
    contract_abi = json.load(f)

CONTRACT_ADDRESS = "0xYourDeployedContractAddressHere"  # Replace with deployed contract
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

# =======================
# Lottie Animation Loader
# =======================
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Example: You can replace this with your own animation
landing_lottie = load_lottie_url("https://assets9.lottiefiles.com/packages/lf20_touohxv0.json")

# =======================
# Landing Page
# =======================
st_lottie(landing_lottie, height=300, key="landing")
st.title("Sonic PayStream 💸")
st.markdown("""
Pay per second. Stream money in real-time.  
Freelancers, content creators, and IoT services rejoice! 🚀
""")

st.sidebar.title("Stream Controls")

# =======================
# User Inputs
# =======================
sender_address = st.sidebar.text_input("Sender Wallet Address")
receiver_address = st.sidebar.text_input("Receiver Wallet Address")
deposit_amount = st.sidebar.number_input("Deposit Amount (in ETH)", min_value=0.001, value=0.01, step=0.001)
rate_per_second = st.sidebar.number_input("Rate per Second (in ETH)", min_value=0.000001, value=0.00001, step=0.000001)

# =======================
# Start Stream Button
# =======================
if st.sidebar.button("Start Stream"):
    st.success(f"Stream started: {sender_address} → {receiver_address} at {rate_per_second} ETH/sec")
    start_time = time.time()

    # =======================
    # Animated Dashboard
    # =======================
    st.subheader("Live Stream Dashboard 🚀")
    progress_bar = st.progress(0)
    balance_text = st.empty()
    
    df = pd.DataFrame(columns=["Time (s)", "Balance (ETH)"])
    running = True

    while running:
        elapsed = time.time() - start_time
        total_received = elapsed * rate_per_second
        balance_text.text(f"Receiver Balance: {total_received:.6f} ETH")
        progress_bar.progress(min(int((total_received/deposit_amount)*100), 100))
        
        # Update chart
        df = pd.concat([df, pd.DataFrame([[elapsed, total_received]], columns=["Time (s)", "Balance (ETH)"])], ignore_index=True)
        fig = px.line(df, x="Time (s)", y="Balance (ETH)", title="Streaming Balance Over Time", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        time.sleep(1)
        if total_received >= deposit_amount:
            running = False
            st.success("Stream completed! 🎉")

# =======================
# Withdraw Funds Section
# =======================
st.sidebar.subheader("Withdraw Funds")
withdraw_stream_id = st.sidebar.number_input("Stream ID to Withdraw", min_value=1, step=1)
if st.sidebar.button("Withdraw"):
    try:
        tx = contract.functions.withdraw(int(withdraw_stream_id)).buildTransaction({
            "from": sender_address,
            "gas": 200000
        })
        st.success(f"Withdrawn from Stream ID: {withdraw_stream_id} 🚀")
    except Exception as e:
        st.error(f"Error: {e}")

# =======================
# Stop Stream Section
# =======================
st.sidebar.subheader("Stop Stream")
stop_stream_id = st.sidebar.number_input("Stream ID to Stop", min_value=1, step=1)
if st.sidebar.button("Stop Stream"):
    try:
        tx = contract.functions.stopStream(int(stop_stream_id)).buildTransaction({
            "from": sender_address,
            "gas": 200000
        })
        st.success(f"Stream ID {stop_stream_id} stopped ⏹️")
    except Exception as e:
        st.error(f"Error: {e}")

# =======================
# Footer
# =======================
st.markdown("---")
st.markdown("Made with ❤️ for Sonic S Tier Hackathon")
