# Orion CSV Import Tool

This is a Flask web application that allows you to upload CSV files from EvaBoot, validate them against Orion CRM's "Other Sources" requirements, and store them in a local SQLite database.

## Features

- Upload and validate CSV files
- Store valid candidates in a database
- View and filter reports of uploaded candidates

## Setup

1. Install dependencies:
   pip install -r requirements.txt

2. Run the app:
   python app.py

3. Open your browser to:
   http://127.0.0.1:5000
