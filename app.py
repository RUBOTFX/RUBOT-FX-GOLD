import streamlit as st
import streamlit.components.v1 as components
import requests
import time
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Spot Gold Sniper (Live)",
    page_icon="👑",
    layout="wide" # Switched to WIDE layout for better visibility
)

# --- 1H BARRIER RANGES ---
BARRIER_RANGES = [
    (4551.000, 4570.000),
    (4380.000, 4400.000),
    (4253.000, 4273.000),
    (3980.000, 4000.000),
    (3871.000, 3891.000),
    (3651.000, 3671.000)
]
PIP_TRIGGER = 2.00

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: white; }
    .big-price {
        font-size: 80px !important; font-weight: 800;
        color: #FFD700; text-align: center;
        text-shadow: 0px 0px 20px rgba(255, 215, 0, 0.6);
        margin-bottom: 5px;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .signal-box {
        padding: 25px; border-radius: 12px;
        text-align: center; font-size: 22px; font-weight: bold;
        margin-bottom: 20px; border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    /* Ladder Styling */
    .ladder-row {
        padding: 10px;
        border-bottom: 1px solid #333;
        font-family: monospace;
        font-size: 16px;
        display: flex; justify-content: space-between;
    }
    .zone-res { background-color: #3d0000; color: #ff9999; border-left: 5px solid #ff0000; }
    .zone-sup { background-color: #002600; color: #99ff99; border-left: 5px solid #00ff00; }
    .price-row { 
        background-color: #FFD700; 
        color: black; 
        font-weight: bold; 
        font-size: 18px;
        border: 2px solid white;
        text-align: center;
        margin: 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA SOURCE: GOLDPRICE.ORG ---
def get_gold_price():
    try:
        url = "https://data-asg.goldprice.org/dbXRates/USD"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=5)
        data = resp.json()
        if 'items' in data and len(data['items']) > 0:
            return float(data['items'][0]['xauPrice'])
        return None
    except Exception as e:
        print(f"Error fetching: {e}")
        return None

# --- SESSION STATE ---
if 'last_res' not in st.session_state: st.session_state.last_res = None
if 'last_sup' not in st.session_state: st.session_state.last_sup = None
if 'sell_active' not in st.session_state: st.session_state.sell_active = False
if 'buy_active' not in st.session_state: st.session_state.buy_active = False

# --- MAIN APP LAYOUT ---
st.title("👑 Spot Gold Sniper")

# Create two columns: Chart on Left, Ladder on Right
col1, col2 = st.columns([2, 1])

# --- MAIN LOOP ---
while True:
    price = get_gold_price()
    
    if price:
        # 1. BARRIER LOGIC
        active_res = None
        active_sup = None
        
        potential_resistances = [r for r in BARRIER_RANGES if r[0] > price]
        if potential_resistances:
            active_res = min(potential_resistances, key=lambda x: x[0])

        potential_supports = [r for r in BARRIER_RANGES if r[1] < price]
        if potential_supports:
            active_sup = max(potential_supports, key=lambda x: x[0])

        # --- LEFT COLUMN: CHART & SIGNALS ---
        with col1:
            st.markdown(f'<div class="big-price">${price:.2f}</div>', unsafe_allow_html=True)
            
            # SIGNAL LOGIC
            status_msg = "SCANNING MARKET..."
            box_color = "#2a2a2a"
            text_color = "#888888"

            # SELL SIDE
            if active_res:
                if active_res != st.session_state.last_res:
                    st.session_state.sell_active = False
                    st.session_state.last_res = active_res
                
                if price >= active_res[0]: st.session_state.sell_active = True
                
                if st.session_state.sell_active:
                    if price > active_res[1]:
                        st.session_state.sell_active = False
                    elif price < active_res[0]:
                        drop = active_res[0] - price
                        if drop >= PIP_TRIGGER:
                            status_msg = f"🚨 SELL SIGNAL @ ${price:.2f} 🚨<br>Drop: {drop:.2f} pts"
                            box_color = "#8B0000"
                            text_color = "white"
                        else:
                            status_msg = f"📉 SELL WATCH<br>Drop: {drop:.2f} pts"
                            box_color = "#5c0000"
                            text_color = "white"
                    else:
                        status_msg = "⚠️ IN RESISTANCE ZONE"
                        box_color = "#B8860B"
                        text_color = "black"

            # BUY SIDE
            if active_sup:
                if active_sup != st.session_state.last_sup:
                    st.session_state.buy_active = False
                    st.session_state.last_sup = active_sup
                
                if price <= active_sup[1]: st.session_state.buy_active = True
                
                if st.session_state.buy_active:
                    if price < active_sup[0]:
                        st.session_state.buy_active = False
                    elif price > active_sup[1]:
                        rise = price - active_sup[1]
                        if rise >= PIP_TRIGGER:
                            status_msg = f"🚀 BUY SIGNAL @ ${price:.2f} 🚀<br>Rise: {rise:.2f} pts"
                            box_color = "#006400"
                            text_color = "white"
                        else:
                            status_msg = f"📈 BUY WATCH<br>Rise: {rise:.2f} pts"
                            box_color = "#004d00"
                            text_color = "white"
                    else:
                        if "SELL" not in status_msg:
                            status_msg = "⚠️ IN SUPPORT ZONE"
                            box_color = "#B8860B"
                            text_color = "black"

            st.markdown(f"""
                <div class="signal-box" style="background-color: {box_color}; color: {text_color};">
                    {status_msg}
                </div>
            """, unsafe_allow_html=True)

            # LIVE CHART
            components.html("""
            <div class="tradingview-widget-container">
              <div id="tradingview_gold"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget(
              {
              "width": "100%", "height": 450,
              "symbol": "OANDA:XAUUSD",
              "interval": "15",
              "timezone": "Etc/UTC",
              "theme": "dark",
              "style": "1",
              "locale": "en",
              "enable_publishing": false,
              "hide_top_toolbar": true,
              "allow_symbol_change": false,
              "container_id": "tradingview_gold"
            });
              </script>
            </div>
            """, height=450)

        # --- RIGHT COLUMN: LADDER VIEW ---
        with col2:
            st.subheader("Price Ladder")
            ladder_html = ""
            
            # Sort barriers High to Low
            sorted_barriers = sorted(BARRIER_RANGES, key=lambda x: x[0], reverse=True)
            
            # Insert Price into the list visually
            price_inserted = False
            
            for r in sorted_barriers:
                # Check if price is ABOVE this zone (and hasn't been printed yet)
                if not price_inserted and price > r[1]:
                    ladder_html += f'<div class="price-row">📍 PRICE: {price:.2f}</div>'
                    price_inserted = True
                
                # Render Zone
                zone_type = "zone-res" if price < r[0] else ("zone-sup" if price > r[1] else "price-row")
                label = "RESISTANCE" if price < r[0] else ("SUPPORT" if price > r[1] else "INSIDE ZONE")
                if zone_type == "price-row": label = "⚠️ INSIDE ZONE ⚠️"
                
                ladder_html += f"""
                <div class="ladder-row {zone_type}">
                    <span>{label}</span>
                    <span>{r[0]:.1f} - {r[1]:.1f}</span>
                </div>
                """
                
                # Check if price is INSIDE this zone
                if not price_inserted and r[0] <= price <= r[1]:
                     price_inserted = True # Already handled by highlighting the zone yellow above
            
            # If price is lower than the lowest zone
            if not price_inserted:
                ladder_html += f'<div class="price-row">📍 PRICE: {price:.2f}</div>'

            st.markdown(ladder_html, unsafe_allow_html=True)
            
    else:
        st.warning("⚠️ Connecting...")
            
    time.sleep(2)
