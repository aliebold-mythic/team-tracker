import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- Page Setup ---
st.set_page_config(page_title="Mission Month 2026 Impact Tracker", page_icon="🌟")

# --- CUSTOM CSS FOR FONTS ---
st.markdown(
    """
    <style>
    /* 1. Import the Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap');

    /* 2. Apply the font to the entire app */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Optional: Make the headers bold and colorful */
    h1, h2, h3 {
        font-weight: 600;
        color: #068dea; /* Matches your primary color */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Functions ---
def get_google_sheet():
    """Connects to Google Sheets using Streamlit Secrets."""
    # Define the scope of access
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Load credentials from Streamlit Secrets (we set this up later)
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    # Authorize and open the sheet
    client = gspread.authorize(creds)
    # MAKE SURE your Google Sheet is named exactly this:
    return client.open("Mission Month 2026 Tracker").sheet1

def load_summary_data():
    """Loads data ONLY to calculate totals."""
    try:
        sheet = get_google_sheet()
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame() # Return empty if connection fails

def save_entry(name, type_of_contrib, amount, notes):
    """Sends the new entry to Google Sheets."""
    sheet = get_google_sheet()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # The row structure must match your Sheet columns
    row = [date_str, name, type_of_contrib, amount, notes]
    sheet.append_row(row)

# --- App Interface ---
st.title("🌟 Mission Month 2026 Tracker")
st.markdown("Log your contributions below. Your individual entries are **private**; only the team totals are displayed.")

# --- 1. The Input Form ---
with st.form("entry_form", clear_on_submit=True):
    st.subheader("Log Activity")
    col_a, col_b = st.columns(2)
    with col_a:
        name_input = st.text_input("Name (Private)")
        contrib_type = st.selectbox("Contribution Type", ["Volunteer Hours", "Monetary Donation ($)"])
    with col_b:
        amount_input = st.number_input("Amount", min_value=0.0, step=1.0)
        notes_input = st.text_input("Notes (Optional)")

    submitted = st.form_submit_button("Submit Contribution")
    
    if submitted:
        if name_input and amount_input > 0:
            try:
                save_entry(name_input, contrib_type, amount_input, notes_input)
                st.success(f"Thanks, {name_input}! We've logged {amount_input} for {contrib_type}.")
                st.balloons()
            except Exception as e:
                st.error(f"Error connecting to database: {e}")
        else:
            st.warning("Please enter your name and a valid amount.")

st.markdown("---")

# --- 2. The Team Dashboard (Totals Only) ---
col_header, col_btn = st.columns([4,1])
with col_header:
    st.subheader("📊 Our Collective Impact")
with col_btn:
    # This button triggers a page reload
    if st.button("🔄 Refresh Data"):
        st.rerun()

df = load_summary_data()

if not df.empty:
    # Filter data by type
    hours_df = df[df["Type"] == "Volunteer Hours"]
    money_df = df[df["Type"] == "Monetary Donation ($)"]

    # Calculate Sums
    total_hours = hours_df["Amount"].sum() if not hours_df.empty else 0
    total_money = money_df["Amount"].sum() if not money_df.empty else 0
    total_participants = df["Name"].nunique()

    # Display Big Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Volunteer Hours", f"{total_hours:,.1f} hrs")
    col2.metric("Total Donations", f"${total_money:,.2f}")
    col3.metric("Team Members Active", total_participants)
    
else:
    st.info("Waiting for the first entry.")
