from flask import Flask, request, render_template_string, redirect, url_for
import pandas as pd
import sqlite3
import os

app = Flask(__name__)
DB_FILE = 'candidates.db'

# Ensure database exists
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                job_title TEXT,
                company_name TEXT,
                country TEXT
            )
        """)

@app.route('/', methods=['GET', 'POST'])
def upload():
    message = ''
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            required_columns = ['First Name', 'Last Name', 'Email', 'Phone Number', 'Job Title', 'Company Name', 'Country']
            if all(col in df.columns for col in required_columns):
                df = df[required_columns]
                df = df.fillna('')
                with sqlite3.connect(DB_FILE) as conn:
                    for _, row in df.iterrows():
                        if row['Email'] or row['Phone Number']:
                            conn.execute("""
                                INSERT INTO candidates (first_name, last_name, email, phone, job_title, company_name, country)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                row['First Name'], row['Last Name'], row['Email'], row['Phone Number'],
                                row['Job Title'], row['Company Name'], row['Country']
                            ))
                    conn.commit()
                message = 'File uploaded and processed successfully.'
            else:
                message = 'Missing required columns in CSV.'
        else:
            message = 'Please upload a valid CSV file.'
    return render_template_string("""
        <h2>Upload EvaBoot CSV</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <input type="submit" value="Upload">
        </form>
        <p>{{ message }}</p>
        <a href="{{ url_for('report') }}">View Report</a>
    """, message=message)

@app.route('/report')
def report():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query('SELECT * FROM candidates', conn)
    return render_template_string("""
        <h2>Candidate Report</h2>
        <table border="1">
            <tr>
                {% for col in df.columns %}
                <th>{{ col }}</th>
                {% endfor %}
            </tr>
            {% for row in df.itertuples() %}
            <tr>
                {% for value in row[1:] %}
                <td>{{ value }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </table>
        <a href="{{ url_for('upload') }}">Back to Upload</a>
    """, df=df)

if __name__ == '__main__':
    init_db()
    
import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)

