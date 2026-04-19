from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import mysql.connector

app = Flask(__name__)
app.secret_key = 'reeat_secret_key_2024_xk9'

USERS = {
    'provider': {'password': 'provider123', 'role': 'provider'},
    'recipient': {'password': 'recipient123', 'role': 'recipient'},
}


def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Swesan23*',
        database='food_redistribution'
    )


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped


def provider_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'provider':
            flash('Provider access required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped


def recipient_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'recipient':
            flash('Recipient access required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped


# ── AUTH ──────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('provider_dashboard') if session['role'] == 'provider'
                        else url_for('recipient_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('Please enter both username and password.', 'error')
        else:
            role = 'recipient' if 'recipient' in username.lower() else 'provider'
            session['user'] = username
            session['role'] = role
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('provider_dashboard') if role == 'provider'
                            else url_for('recipient_dashboard'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out.', 'success')
    return redirect(url_for('login'))


# ── HOME ──────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('home.html')


# ── PROVIDER ──────────────────────────────────────────────────────────────────

@app.route('/provider')
@provider_required
def provider_dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = """
        SELECT sl.*, fp.name AS provider_name
        FROM surplus_listing sl
        JOIN Food_Provider fp ON sl.provider_id = fp.provider_id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND fp.name LIKE %s"
        params.append(f'%{search}%')
    if status_filter:
        query += " AND sl.status = %s"
        params.append(status_filter)
    query += " ORDER BY sl.post_date DESC"

    cursor.execute(query, params)
    listings = cursor.fetchall()

    # Aggregate: live counts by status for dashboard stats
    cursor.execute("""
        SELECT status, COUNT(*) AS count
        FROM surplus_listing
        GROUP BY status
    """)
    counts_raw = cursor.fetchall()
    status_counts = {row['status']: row['count'] for row in counts_raw}
    total_count = sum(status_counts.values())

    cursor.close()
    db.close()
    return render_template('provider_dashboard.html', listings=listings,
                           search=search, status_filter=status_filter,
                           status_counts=status_counts, total_count=total_count)


@app.route('/provider/new', methods=['GET', 'POST'])
@provider_required
def new_listing():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        provider_id = request.form.get('provider_id', '').strip()
        post_date = request.form.get('post_date', '').strip()
        expiration_date = request.form.get('expiration_date', '').strip()
        total_quantity = request.form.get('total_quantity', '').strip()

        if not all([provider_id, post_date, expiration_date, total_quantity]):
            flash('All listing fields are required.', 'error')
        else:
            cursor.execute("""
                INSERT INTO surplus_listing
                    (provider_id, post_date, expiration_date, total_quantity, status)
                VALUES (%s, %s, %s, %s, 'available')
            """, (provider_id, post_date, expiration_date, total_quantity))
            db.commit()
            listing_id = cursor.lastrowid

            food_ids = request.form.getlist('food_id[]')
            quantities = request.form.getlist('item_quantity[]')
            for fid, qty in zip(food_ids, quantities):
                if fid and qty:
                    try:
                        cursor.execute("""
                            INSERT INTO listing_item (listing_id, food_id, quantity)
                            VALUES (%s, %s, %s)
                        """, (listing_id, fid, qty))
                    except Exception:
                        pass
            db.commit()
            flash('Listing posted successfully.', 'success')
            cursor.close()
            db.close()
            return redirect(url_for('provider_dashboard'))

    cursor.execute("SELECT provider_id, name FROM Food_Provider ORDER BY name")
    providers = cursor.fetchall()

    food_items = []
    try:
        cursor.execute("SELECT food_id, food_name FROM food_item ORDER BY food_name")
        food_items = cursor.fetchall()
    except Exception:
        pass

    cursor.close()
    db.close()
    return render_template('new_listing.html', providers=providers, food_items=food_items)


@app.route('/provider/delete/<int:listing_id>')
@provider_required
def delete_listing(listing_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM listing_item WHERE listing_id = %s", (listing_id,))
    cursor.execute("DELETE FROM surplus_listing WHERE listing_id = %s", (listing_id,))
    db.commit()
    cursor.close()
    db.close()
    flash('Listing deleted.', 'success')
    return redirect(url_for('provider_dashboard'))


@app.route('/provider/update/<int:listing_id>/<status>')
@provider_required
def update_status(listing_id, status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE surplus_listing SET status = %s WHERE listing_id = %s",
                   (status, listing_id))
    db.commit()
    cursor.close()
    db.close()
    flash('Listing status updated.', 'success')
    return redirect(url_for('provider_dashboard'))


# ── RECIPIENT ─────────────────────────────────────────────────────────────────

@app.route('/recipient')
@recipient_required
def recipient_dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    search = request.args.get('search', '').strip()

    query = """
        SELECT sl.*, fp.name AS provider_name
        FROM surplus_listing sl
        JOIN Food_Provider fp ON sl.provider_id = fp.provider_id
        WHERE sl.status = 'available'
    """
    params = []
    if search:
        query += " AND fp.name LIKE %s"
        params.append(f'%{search}%')
    query += " ORDER BY sl.post_date DESC"

    cursor.execute(query, params)
    listings = cursor.fetchall()
    cursor.execute("SELECT org_id, name FROM recipient_organization ORDER BY name")
    orgs = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('recipient_dashboard.html', listings=listings,
                           orgs=orgs, search=search)


@app.route('/recipient/request', methods=['POST'])
@recipient_required
def submit_request():
    listing_id = request.form.get('listing_id', '').strip()
    org_id = request.form.get('org_id', '').strip()
    requested_quantity = request.form.get('requested_quantity', '').strip()

    if not all([listing_id, org_id, requested_quantity]):
        flash('Please fill in all request fields.', 'error')
        return redirect(url_for('recipient_dashboard'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO request (listing_id, org_id, request_date, requested_quantity, status)
        VALUES (%s, %s, CURDATE(), %s, 'pending')
    """, (listing_id, org_id, requested_quantity))
    db.commit()
    cursor.close()
    db.close()
    flash('Request submitted successfully.', 'success')
    return redirect(url_for('my_requests'))


@app.route('/recipient/requests')
@recipient_required
def my_requests():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.*, sl.post_date, sl.expiration_date, sl.total_quantity,
               fp.name AS provider_name, ro.name AS org_name
        FROM request r
        JOIN surplus_listing sl ON r.listing_id = sl.listing_id
        JOIN Food_Provider fp ON sl.provider_id = fp.provider_id
        JOIN recipient_organization ro ON r.org_id = ro.org_id
        ORDER BY r.request_date DESC
    """)
    requests_list = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('my_requests.html', requests=requests_list)


# ── SHARED ────────────────────────────────────────────────────────────────────

@app.route('/pickups')
@login_required
def pickup_history():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, fp.name AS provider_name, ro.name AS org_name,
               sl.post_date, sl.total_quantity, r.requested_quantity
        FROM pickup p
        JOIN request r ON p.request_id = r.request_id
        JOIN surplus_listing sl ON r.listing_id = sl.listing_id
        JOIN Food_Provider fp ON sl.provider_id = fp.provider_id
        JOIN recipient_organization ro ON r.org_id = ro.org_id
        ORDER BY p.pickup_date DESC
    """)
    pickups = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('pickup_history.html', pickups=pickups)


@app.route('/analytics')
@login_required
def analytics():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT fp.name, COUNT(sl.listing_id) AS total_listings,
               COALESCE(SUM(sl.total_quantity), 0) AS total_quantity
        FROM Food_Provider fp
        JOIN surplus_listing sl ON fp.provider_id = sl.provider_id
        GROUP BY fp.provider_id, fp.name
        ORDER BY total_quantity DESC
    """)
    surplus = cursor.fetchall()

    cursor.execute("""
        SELECT fp.name,
               ROUND(AVG(DATEDIFF(p.pickup_date, sl.post_date)), 1) AS avg_days
        FROM Food_Provider fp
        JOIN surplus_listing sl ON fp.provider_id = sl.provider_id
        JOIN request r ON sl.listing_id = r.listing_id
        JOIN pickup p ON r.request_id = p.request_id
        WHERE p.pickup_status = 'completed'
        GROUP BY fp.provider_id, fp.name
        ORDER BY avg_days ASC
    """)
    patterns = cursor.fetchall()
    cursor.close()
    db.close()

    # Surplus patterns over time: monthly breakdown
    cursor.execute("""
        SELECT DATE_FORMAT(sl.post_date, '%b %Y') AS period,
               YEAR(sl.post_date)                 AS yr,
               MONTH(sl.post_date)                AS mo,
               COUNT(*)                           AS listing_count,
               COALESCE(SUM(sl.total_quantity), 0) AS total_quantity
        FROM surplus_listing sl
        GROUP BY YEAR(sl.post_date), MONTH(sl.post_date)
        ORDER BY yr, mo
    """)
    monthly = cursor.fetchall()

    cursor.close()
    db.close()

    max_qty = max((row['total_quantity'] for row in surplus), default=1) or 1
    max_monthly = max((row['total_quantity'] for row in monthly), default=1) or 1
    return render_template('analytics.html', surplus=surplus, patterns=patterns,
                           max_qty=max_qty, monthly=monthly, max_monthly=max_monthly)


if __name__ == '__main__':
    app.run(debug=True)
