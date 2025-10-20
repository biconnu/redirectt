from flask import Flask, render_template, request, redirect, flash, session
import psycopg2
import string
import random
from datetime import datetime
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import requests
from datetime import datetime, timedelta
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import psycopg2
import psycopg2.extras
import requests
from datetime import datetime, timedelta
import os
import urllib.parse as up
from functools import wraps
import time
import re
import json
import secrets
import uuid

app = Flask(__name__)
app.secret_key = "secretkey"
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Database initialization
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS urls
        (id SERIAL PRIMARY KEY,
         original_url TEXT NOT NULL,
         short_code TEXT UNIQUE NOT NULL,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         clicks INTEGER DEFAULT 0,
         is_active BOOLEAN DEFAULT TRUE)
    ''')
    conn.commit()
    conn.close()
init_db()
# Generate UUID-style token
def generate_short_code():
    segments = []
    for i in range(5):
        segment = ''.join(random.choices('abcdef' + string.digits, k=8))
        segments.append(segment)
    return '-'.join(segments)

# Login required decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, original_url, short_code, created_at, clicks, is_active 
        FROM urls 
        ORDER BY created_at DESC
    ''')
    urls = c.fetchall()
    conn.close()
    
    # Format the dates for display
    formatted_urls = []
    for url in urls:
        url_id, original_url, short_code, created_at, clicks, is_active = url
        # Convert datetime to string for display
        if isinstance(created_at, datetime):
            created_at_str = created_at.strftime('%Y-%m-%d')
        else:
            created_at_str = str(created_at)[:10]  # Take first 10 characters if it's already a string
        formatted_urls.append((url_id, original_url, short_code, created_at_str, clicks, is_active))
    
    return render_template('index.html', urls=formatted_urls)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'Roy' and password == '1234':
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect('/')
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/login')

@app.route('/shorten', methods=['POST'])
@login_required
def shorten_url():
    original_url = request.form.get('url')
    
    if not original_url:
        flash('Please enter a URL', 'error')
        return redirect('/')
    
    if not original_url.startswith(('http://', 'https://')):
        original_url = 'http://' + original_url
    
    short_code = generate_short_code()
    
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO urls (original_url, short_code) VALUES (%s, %s)',
                 (original_url, short_code))
        conn.commit()
        flash(f'Short URL created successfully!', 'success')
        
    except psycopg2.IntegrityError:
        # If short_code already exists, generate a new one
        short_code = generate_short_code()
        c.execute('INSERT INTO urls (original_url, short_code) VALUES (%s, %s)',
                 (original_url, short_code))
        conn.commit()
        flash(f'Short URL created successfully!', 'success')
    
    conn.close()
    return redirect('/')

@app.route('/toggle_url/<int:url_id>')
@login_required
def toggle_url(url_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT is_active FROM urls WHERE id = %s', (url_id,))
    result = c.fetchone()
    
    if result:
        new_status = not result[0]  # Toggle the boolean value
        c.execute('UPDATE urls SET is_active = %s WHERE id = %s', (new_status, url_id))
        conn.commit()
        status_text = "enabled" if new_status else "disabled"
        flash(f'URL {status_text} successfully!', 'success')
    
    conn.close()
    return redirect('/')

@app.route('/delete_url/<int:url_id>')
@login_required
def delete_url(url_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('DELETE FROM urls WHERE id = %s', (url_id,))
    conn.commit()
    conn.close()
    
    flash('URL deleted successfully!', 'success')
    return redirect('/')

@app.route('/<short_code>')
def redirect_to_url(short_code):
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT original_url, is_active FROM urls WHERE short_code = %s', (short_code,))
    result = c.fetchone()
    
    if result:
        original_url, is_active = result
        if is_active:
            c.execute('UPDATE urls SET clicks = clicks + 1 WHERE short_code = %s', (short_code,))
            conn.commit()
            conn.close()
            return redirect(original_url)
        else:
            conn.close()
            return "URL not found", 404
    else:
        conn.close()
        return "URL not found", 404

if __name__ == '__main__':
   
    
    

    app.run(
        host='0.0.0.0', 
        port=5000,
        debug=False
    )