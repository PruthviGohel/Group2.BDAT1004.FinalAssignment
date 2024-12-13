from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = '2896239425'

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database configuration using your specific credentials
db_config = {
    'user': 'sanjay1007',
    'password': 'st2896239425',
    'host': 'sanjay1007.mysql.pythonanywhere-services.com',
    'database': 'sanjay1007$default'
}

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return User(id=user[0], username=user[1], password=user[2])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            login_user(User(id=user[0], username=user[1], password=user[2]))
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    crypto = request.args.get('crypto', 'Bitcoin')
    years = int(request.args.get('years', 1))

    now = datetime.utcnow()
    start_date = now - timedelta(days=365 * years)
    last_week_date = now - timedelta(weeks=1)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT price_usd, timestamp FROM crypto_prices
        WHERE crypto_name = %s
        ORDER BY timestamp DESC LIMIT 1
    """, (crypto,))
    latest = cursor.fetchone()

    cursor.execute("""
        SELECT price_usd, timestamp FROM crypto_prices
        WHERE crypto_name = %s AND timestamp <= %s
        ORDER BY timestamp DESC LIMIT 1
    """, (crypto, last_week_date))
    last_week = cursor.fetchone()

    cursor.execute("""
        SELECT price_usd, timestamp FROM crypto_prices
        WHERE crypto_name = %s AND timestamp >= %s
        ORDER BY timestamp ASC
    """, (crypto, start_date))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    chart_data = {
        'timestamps': [row['timestamp'].strftime('%Y-%m-%d') for row in rows],
        'prices': [row['price_usd'] for row in rows]
    }

    percentage_change = ((latest['price_usd'] - last_week['price_usd']) / last_week['price_usd']) * 100 if latest and last_week else 0

    summary_data = {
        'crypto_name': crypto,
        'latest_price': latest['price_usd'] if latest else 'N/A',
        'last_week_price': last_week['price_usd'] if last_week else 'N/A',
        'percentage_change': percentage_change
    }

    return jsonify({
        'summary': summary_data,
        'chart': chart_data
    })

if __name__ == '__main__':
    app.run(debug=True)
