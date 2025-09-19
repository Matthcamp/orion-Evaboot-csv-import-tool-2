from flask import Flask, request, render_template_string, send_file, redirect, url_for
import pandas as pd
import sqlite3
import os
import io

app = Flask(__name__)
DB_FILE = 'candidates.db'

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

def extract_country(location):
    if pd.isna(location):
        return ''
    parts = [part.strip() for part in str(location).split(',')]
    return parts[-1] if parts else ''

@app.route('/', methods=['GET', 'POST'])
def upload():
    message = ''
    download_ready = False
    download_missing = False
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            # Map EvaBoot columns to Orion columns
            orion_df = pd.DataFrame()
            orion_df['First Name'] = df.get('First Name', '')
            orion_df['Last Name'] = df.get('Last Name', '')
            orion_df['Job Title'] = df.get('Current Job', '')
            orion_df['Email'] = df.get('Email', '')
            orion_df['Phone Number'] = ''  # EvaBoot doesn't provide phone
            orion_df['Company Name'] = df.get('Company Name', '')
            orion_df['Country'] = df.get('Location', '').apply(extract_country)

            # Save to DB and prepare missing report
            required = ['First Name', 'Last Name', 'Email', 'Job Title', 'Company Name', 'Country']
            missing_rows = orion_df[orion_df[required].isnull().any(axis=1) | (orion_df[required] == '').any(axis=1)]
            valid_rows = orion_df.drop(missing_rows.index)

            # Save valid candidates to DB
            with sqlite3.connect(DB_FILE) as conn:
                for _, row in valid_rows.iterrows():
                    conn.execute("""
                        INSERT INTO candidates (first_name, last_name, email, phone, job_title, company_name, country)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['First Name'], row['Last Name'], row['Email'], row['Phone Number'],
                        row['Job Title'], row['Company Name'], row['Country']
                    ))
                conn.commit()

            # Save Orion-ready CSV and missing report to memory for download
            valid_csv = valid_rows.to_csv(index=False)
            missing_csv = missing_rows.to_csv(index=False)
            with open('orion_ready_candidates.csv', 'w', encoding='utf-8') as f:
                f.write(valid_csv)
            with open('missing_fields_report.csv', 'w', encoding='utf-8') as f:
                f.write(missing_csv)

            message = f'Upload complete! {len(valid_rows)} candidates ready for Orion. {len(missing_rows)} rows had missing fields.'
            download_ready = True
            download_missing = len(missing_rows) > 0
        else:
            message = 'Please upload a valid CSV file.'
    return render_template_string('''
        <h2>Upload EvaBoot CSV</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <input type="submit" value="Upload">
        </form>
        <p>{{ message }}</p>
        {% if download_ready %}
            <a href="{{ url_for('download_ready') }}">Download Orion-Ready CSV</a><br>
        {% endif %}
        {% if download_missing %}
            <a href="{{ url_for('download_missing') }}">Download Missing Fields Report</a><br>
        {% endif %}
        <a href="{{ url_for('report') }}">View Candidate Report</a>
    ''', message=message, download_ready=download_ready, download_missing=download_missing)

@app.route('/download_ready')
def download_ready():
    return send_file('orion_ready_candidates.csv', as_attachment=True)

@app.route('/download_missing')
def download_missing():
    return send_file('missing_fields_report.csv', as_attachment=True)

@app.route('/report', methods=['GET', 'POST'])
def report():
    filters = {
        'first_name': request.form.get('first_name', ''),
        'last_name': request.form.get('last_name', ''),
        'email': request.form.get('email', ''),
        'phone': request.form.get('phone', ''),
        'job_title': request.form.get('job_title', ''),
        'company_name': request.form.get('company_name', ''),
        'country': request.form.get('country', '')
    }
    query = 'SELECT * FROM candidates WHERE 1=1'
    params = []
    for field, value in filters.items():
        if value:
            query += f' AND {field} LIKE ?'
            params.append(f'%{value}%')
    with sqlite3.connect(DB_FILE) as conn:
        results = conn.execute(query, params).fetchall()
    return render_template_string('''
        <h2>Candidate Report</h2>
        <form method="post">
            {% for field in filters %}
                <label>{{ field.replace('_', ' ').title() }}:</label>
                <input type="text" name="{{ field }}" value="{{ filters[field] }}"><br>
            {% endfor %}
            <input type="submit" value="Filter">
        </form>
        <table border="1">
            <tr>
                <th>ID</th><th>First Name</th><th>Last Name</th><th>Email</th><th>Phone</th>
                <th>Job Title</th><th>Company Name</th><th>Country</th>
            </tr>
            {% for row in results %}
                <tr>
                    {% for item in row %}
                        <td>{{ item }}</td>
                    {% endfor %}
                </tr>
            {% endfor %}
        </table>
        <a href="{{ url_for('upload') }}">Back to Upload</a>
    ''', filters=filters, results=results)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
