import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]),
    scopes=scopes
)

client = gspread.authorize(creds)

print("Authentication successful!")

sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"])

print("Spreadsheet:", sh.title)

ws = sh.sheet1

print("Worksheet:", ws.title)

ws.update(
    values=[["TEST", "Google Sheets connection works"]],
    range_name="A1:B1"
)

print("TEST ROW WRITTEN SUCCESSFULLY!")