# config.py

# The name of your Google Sheet (must be shared with your Service Account email)
GOOGLE_SHEET_NAME = "getNewtasksinWeek"

# The JSON file downloaded from Google Cloud Console
CREDENTIALS_FILE = 'getnewtaskinweek-5a476d4f2124.json'

# Outlook folder constant (6 is the default Inbox)
OUTLOOK_INBOX_ID = 6

# Scope for Google Sheets and Drive API
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

TARGET_SUBFOLDER = "ThamDinh"

OUTPUT_JSON_FILE = "task_export.json"

GOOGLE_SHEET_NAME = "getNewtasksinWeek"