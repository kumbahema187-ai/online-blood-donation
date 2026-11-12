from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import sqlite3, os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "blood.db")

app = Flask(__name__)
app.secret_key = "change_this_secret_for_prod"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS donors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        phone TEXT,
        location TEXT,
        last_donation TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        hospital TEXT,
        reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS blood_banks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT,
        available_groups TEXT,
        contact TEXT
    );''')

    conn.commit()
    conn.close()


@app.route('/')
def index():
    conn = get_db_connection()
    donors = conn.execute("SELECT * FROM donors ORDER BY created_at DESC LIMIT 8").fetchall()
    requests_ = conn.execute("SELECT * FROM requests ORDER BY created_at DESC LIMIT 6").fetchall()
    banks = conn.execute("SELECT * FROM blood_banks ORDER BY name LIMIT 6").fetchall()
    conn.close()
    return render_template("index.html", donors=donors, requests=requests_, banks=banks)


@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        blood_group = request.form.get('blood_group','').strip().upper()
        phone = request.form.get('phone','').strip()
        location = request.form.get('location','').strip()
        last = request.form.get('last_donation','').strip()

        if not name or not blood_group:
            flash("Name and Blood Group are required", "danger")
            return redirect(url_for('donate'))

        conn = get_db_connection()
        conn.execute("INSERT INTO donors (name,blood_group,phone,location,last_donation) VALUES (?,?,?,?,?)",
                     (name,blood_group,phone,location,last))
        conn.commit()
        conn.close()
        flash("Thank you! You are registered as a donor.", "success")
        return redirect(url_for('index'))

    return render_template("donate.html")


@app.route('/request', methods=['GET', 'POST'])
def blood_request():
    if request.method == 'POST':
        patient = request.form.get('patient_name','').strip()
        blood_group = request.form.get('blood_group','').strip().upper()
        hospital = request.form.get('hospital','').strip()
        reason = request.form.get('reason','').strip()

        if not patient or not blood_group:
            flash("Patient name and Blood Group are required", "danger")
            return redirect(url_for('blood_request'))

        conn = get_db_connection()
        conn.execute("INSERT INTO requests (patient_name,blood_group,hospital,reason) VALUES (?,?,?,?)",
                     (patient,blood_group,hospital,reason))
        conn.commit()
        conn.close()
        flash("Blood request submitted.", "success")
        return redirect(url_for('index'))

    return render_template("request.html")


@app.route('/banks')
def banks():
    conn = get_db_connection()
    banks = conn.execute("SELECT * FROM blood_banks ORDER BY name").fetchall()
    conn.close()
    return render_template("banks.html", banks=banks)


@app.route('/availability')
def availability():
    group = request.args.get('group','').strip().upper()
    conn = get_db_connection()
    if group:
        donors = conn.execute("SELECT * FROM donors WHERE blood_group = ? ORDER BY created_at DESC", (group,)).fetchall()
    else:
        donors = conn.execute("SELECT * FROM donors ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("availability.html", donors=donors, group=group)


@app.route('/donor/<int:donor_id>')
def donor_detail(donor_id):
    conn = get_db_connection()
    donor = conn.execute("SELECT * FROM donors WHERE id = ?", (donor_id,)).fetchone()
    conn.close()
    if not donor:
        flash("Donor not found", "danger")
        return redirect(url_for('index'))
    return render_template("donor_detail.html", donor=donor)


@app.route('/static/img/<path:filename>')
def static_img(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static", "img"), filename)


if __name__ == '__main__':
    init_db()
    # run local server
    app.run(debug=True, host='127.0.0.1', port=5000)
