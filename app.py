import os, sqlite3, uuid
from flask import Flask, render_template_string, request, redirect, session, url_for
from functools import wraps

app = Flask(__name__)
app.secret_key = "nimbus_v32_pro"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nimbus_erp.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS properties (id INTEGER PRIMARY KEY, name TEXT)")
        # In-upgrade na Tenant Table (Added Contact Info)
        c.execute("""CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY, name TEXT, prop_id INTEGER, t_type TEXT, rent REAL,
            phone TEXT, email TEXT, emergency_contact TEXT, start_date TEXT)""")
        
        # Ledger Table (Added Utility Readings)
        c.execute("""CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT, t_id TEXT, period TEXT, 
            basic REAL, vat REAL, wtax REAL, signage REAL, 
            elec_reading REAL, water_reading REAL, elec_amount REAL, water_amount REAL,
            total REAL, check_no TEXT, ds_series TEXT, date_paid TEXT, remarks TEXT)""")
        
        props = [(1,'Kapasigan'),(2,'Rosario'),(3,'Marikina'),(4,'Camarin 1'),(5,'Camarin 3'),(6,'Palatiw'),
                 (7,'MB Old'),(8,'MB New'),(9,'Tagaytay 1'),(10,'Tagaytay 2'),(11,'Camarin 2'),(12,'Pateros')]
        c.executemany("INSERT OR IGNORE INTO properties VALUES (?,?)", props)
        conn.commit()

init_db()

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not session.get('logged_in'): return redirect('/login')
        return f(*args, **kwargs)
    return dec

CSS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #f0f2f5; font-size: 13px; }
    .sidebar { width: 220px; background: #1a202c; color: white; height: 100vh; position: fixed; padding: 20px; }
    .sidebar a { color: #cbd5e0; text-decoration: none; display: block; padding: 12px; border-radius: 8px; margin-bottom: 5px; }
    .sidebar a:hover { background: #2d3748; }
    .main { margin-left: 240px; padding: 30px; }
    .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    table { width: 100%; border-collapse: collapse; background: white; }
    th, td { padding: 12px; border: 1px solid #e2e8f0; text-align: center; }
    th { background: #f7fafc; color: #4a5568; font-size: 11px; text-transform: uppercase; }
    .btn { background: #3182ce; color: white; padding: 10px 15px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-weight: bold; }
    .btn-sub { background: #2d3748; width: 100%; margin-top: 15px; }
    input, select, textarea { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #e2e8f0; border-radius: 6px; box-sizing: border-box; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
</style>
"""

LAYOUT = """
<!DOCTYPE html>
<html>
<head><title>Nimbus ERP v32</title>{{ css|safe }}</head>
<body>
    <div class="sidebar">
        <h2>NIMBUS</h2>
        <a href="/">📊 Master Ledger</a>
        <a href="/directory">📂 Tenant List</a>
        <a href="/enroll">➕ New Tenant</a>
        <a href="/logout" style="margin-top:100px; color:#fc8181;">Logout</a>
    </div>
    <div class="main">
        {% if p == 'dash' %}
            <h1>Collection Dashboard</h1>
            <div class="card">
                <table>
                    <tr><th>Period</th><th>Tenant</th><th>Basic</th><th>Utils (E+W)</th><th>Total Paid</th><th>Check No</th><th>Date</th></tr>
                    {% for r in data %}
                    <tr>
                        <td>{{r[2]}}</td><td><b>{{r[16]}}</b></td><td>{{r[3]}}</td>
                        <td>₱{{r[9]+r[10]}}</td><td style="color:green; font-weight:bold;">₱{{"%.2f"|format(r[11])}}</td>
                        <td>{{r[12]}}</td><td>{{r[14]}}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

        {% elif p == 'dir' %}
            <h1>Tenant Information Center</h1>
            <div class="card">
                <table>
                    <tr><th>Name</th><th>Phone</th><th>Building</th><th>Type</th><th>Action</th></tr>
                    {% for t in tenants %}
                    <tr>
                        <td><b>{{t[1]}}</b></td><td>{{t[5]}}</td><td>{{t[9]}}</td><td>{{t[3]}}</td>
                        <td><a href="/profile/{{t[0]}}" class="btn">View Info & Ledger</a></td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

        {% elif p == 'profile' %}
            <h1>Tenant: {{t[1]}}</h1>
            <div class="grid">
                <div class="card">
                    <h3>Contact Information</h3>
                    <p><b>Phone:</b> {{t[5]}}</p>
                    <p><b>Email:</b> {{t[6]}}</p>
                    <p><b>Emergency:</b> {{t[7]}}</p>
                    <p><b>Start Date:</b> {{t[8]}}</p>
                </div>
                <div class="card">
                    <h3>Billing Summary</h3>
                    <p><b>Unit Type:</b> {{t[3]}}</p>
                    <p><b>Monthly Rent:</b> ₱{{t[4]}}</p>
                    <a href="/add_l/{{t[0]}}" class="btn">➕ Post Payment / Utility</a>
                </div>
            </div>
            <div class="card">
                <h3>Payment History</h3>
                <table>
                    <tr><th>Period</th><th>Rent</th><th>Elec Amount</th><th>Water Amount</th><th>Total</th><th>Date</th></tr>
                    {% for l in ledger %}
                    <tr><td>{{l[2]}}</td><td>{{l[3]}}</td><td>{{l[9]}}</td><td>{{l[10]}}</td><td><b>₱{{l[11]}}</b></td><td>{{l[14]}}</td></tr>
                    {% endfor %}
                </table>
            </div>

        {% elif p == 'enr' %}
            <div class="card" style="max-width:600px; margin:auto;">
                <h2>Add New Tenant Information</h2>
                <form action="/save_t" method="POST">
                    <div class="grid">
                        <div>Name: <input name="name" required></div>
                        <div>Phone: <input name="phone"></div>
                        <div>Email: <input name="email" type="email"></div>
                        <div>Emergency Contact: <input name="e_contact"></div>
                        <div>Start Date: <input type="date" name="s_date"></div>
                        <div>Monthly Rent: <input name="rent" type="number" step="0.01" required></div>
                    </div>
                    Property: <select name="prop_id">{% for pr in props %}<option value="{{pr[0]}}">{{pr[1]}}</option>{% endfor %}</select>
                    Type: <select name="t_type"><option>Commercial</option><option>Residential</option></select>
                    <button type="submit" class="btn btn-sub">Save Tenant Information</button>
                </form>
            </div>

        {% elif p == 'add_l' %}
            <div class="card" style="max-width:700px; margin:auto;">
                <h2>Post Payment & Utilities: {{t[1]}}</h2>
                <form action="/save_l" method="POST">
                    <input type="hidden" name="tid" value="{{t[0]}}">
                    <div class="grid">
                        <div>Billing Period: <input name="period" required placeholder="April 2026"></div>
                        <div>Date Paid: <input type="date" name="d_paid" required></div>
                        <div>Basic Rent: <input name="basic" type="number" step="0.01" value="{{t[4]}}"></div>
                        <div>Signage: <input name="signage" type="number" step="0.01" value="0"></div>
                    </div>
                    <h3 style="border-bottom: 1px solid #ddd; padding-bottom: 5px;">Utility Metering</h3>
                    <div class="grid">
                        <div>Elec Reading: <input name="e_read" type="number" step="0.1" placeholder="Current Meter"></div>
                        <div>Elec Amount: <input name="e_amt" type="number" step="0.01" placeholder="₱ Amount"></div>
                        <div>Water Reading: <input name="w_read" type="number" step="0.1" placeholder="Current Meter"></div>
                        <div>Water Amount: <input name="w_amt" type="number" step="0.01" placeholder="₱ Amount"></div>
                    </div>
                    <div class="grid" style="margin-top:10px;">
                        <div>Check No: <input name="check_no" placeholder="N/A"></div>
                        <div>DS Series: <input name="ds_series"></div>
                    </div>
                    Remarks: <textarea name="remarks"></textarea>
                    <button type="submit" class="btn btn-sub">Post to Ledger</button>
                </form>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/")
@login_required
def dash():
    conn = sqlite3.connect(DB_PATH)
    data = conn.execute("SELECT ledger.*, tenants.name FROM ledger LEFT JOIN tenants ON ledger.t_id = tenants.id ORDER BY ledger.id DESC").fetchall()
    conn.close()
    return render_template_string(LAYOUT, p='dash', data=data, css=CSS)

@app.route("/directory")
@login_required
def directory():
    conn = sqlite3.connect(DB_PATH)
    tenants = conn.execute("SELECT tenants.*, properties.name FROM tenants LEFT JOIN properties ON tenants.prop_id = properties.id").fetchall()
    conn.close()
    return render_template_string(LAYOUT, p='dir', tenants=tenants, css=CSS)

@app.route("/profile/<tid>")
@login_required
def profile(tid):
    conn = sqlite3.connect(DB_PATH)
    t = conn.execute("SELECT tenants.*, properties.name FROM tenants LEFT JOIN properties ON tenants.prop_id = properties.id WHERE tenants.id=?", (tid,)).fetchone()
    ledger = conn.execute("SELECT * FROM ledger WHERE t_id=?", (tid,)).fetchall()
    conn.close()
    return render_template_string(LAYOUT, p='profile', t=t, ledger=ledger, css=CSS)

@app.route("/enroll")
@login_required
def enroll():
    conn = sqlite3.connect(DB_PATH); props = conn.execute("SELECT * FROM properties").fetchall(); conn.close()
    return render_template_string(LAYOUT, p='enr', props=props, css=CSS)

@app.route("/save_t", methods=["POST"])
def save_t():
    f = request.form; conn = sqlite3.connect(DB_PATH)
    conn.execute("""INSERT INTO tenants (id, name, prop_id, t_type, rent, phone, email, emergency_contact, start_date) 
                    VALUES (?,?,?,?,?,?,?,?,?)""",
               (str(uuid.uuid4())[:8], f['name'], f['prop_id'], f['t_type'], f['rent'], f['phone'], f['email'], f['e_contact'], f['s_date']))
    conn.commit(); conn.close()
    return redirect('/directory')

@app.route("/add_l/<tid>")
@login_required
def add_l(tid):
    conn = sqlite3.connect(DB_PATH); t = conn.execute("SELECT * FROM tenants WHERE id=?", (tid,)).fetchone(); conn.close()
    return render_template_string(LAYOUT, p='add_l', t=t, css=CSS)

@app.route("/save_l", methods=["POST"])
def save_l():
    f = request.form; basic = float(f['basic']); vat, wtax = basic * 0.12, basic * 0.05
    e_amt = float(f['e_amt'] or 0); w_amt = float(f['w_amt'] or 0)
    total = (basic + vat + float(f['signage']) + e_amt + w_amt) - wtax
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""INSERT INTO ledger (t_id, period, basic, vat, wtax, signage, elec_reading, water_reading, elec_amount, water_amount, total, check_no, ds_series, date_paid, remarks) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                 (f['tid'], f['period'], basic, vat, wtax, f['signage'], f['e_read'], f['w_read'], e_amt, w_amt, total, f['check_no'], f['ds_series'], f['d_paid'], f['remarks']))
    conn.commit(); conn.close()
    return redirect('/')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST" and request.form.get("pw") == "admin123":
        session['logged_in'] = True
        return redirect('/')
    return '<h3>Login</h3><form method="POST"><input type="password" name="pw"><button>Enter</button></form>'

@app.route("/logout")
def logout(): session.clear(); return redirect('/login')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
