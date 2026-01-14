import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- Page Setup ---
st.set_page_config(page_title="Team Impact Tracker", page_icon="🌟")

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
    return client.open("Team Tracker").sheet1

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
st.title("🌟 Team Impact Tracker")
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
                st.balloons() # Fun visual celebration
            except Exception as e:
                st.error("Error connecting to database. Please notify the admin.")
        else:
            st.warning("Please enter your name and a valid amount.")

st.markdown("---")

# --- 2. The Team Dashboard (Totals Only) ---
st.subheader("📊 Our Collective Impact")

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
    
    # Optional: A chart showing progress over time (anonymized)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        # Simple bar chart of activity counts per day
        daily_counts = df.groupby(df["Date"].dt.date).size()
        st.bar_chart(daily_counts)
        st.caption("Activity trend over time (Count of entries)")

else:
    st.info("Waiting for the first entry...")