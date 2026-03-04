import os
from flask import Flask, render_template_string, request, redirect, session, url_for
import sqlite3, uuid
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'nimbus_v29_final_fixed')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "nimbus_erp.db")

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS properties (id INTEGER PRIMARY KEY, name TEXT)")
    props = [(1,'Kapasigan'),(2,'Rosario'),(3,'Marikina'),(4,'Camarin 1'),(5,'Camarin 3'),(6,'Palatiw'),
             (7,'MB Old'),(8,'MB New'),(9,'Tagaytay 1'),(10,'Tagaytay 2'),(11,'Camarin 2'),(12,'Pateros')]
    c.executemany("INSERT OR IGNORE INTO properties VALUES (?,?)", props)
    c.execute("""CREATE TABLE IF NOT EXISTS tenants (
        id TEXT PRIMARY KEY, name TEXT, bname TEXT, prop_id INTEGER,
        t_type TEXT, rent REAL, status TEXT DEFAULT 'Active')""")
    c.execute("""CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT, t_id TEXT, period TEXT, 
        basic REAL, vat REAL, wtax REAL, signage REAL, electric REAL, water REAL, 
        total REAL, due_date TEXT, check_no TEXT, ds_series TEXT, date_paid TEXT, remarks TEXT)""")
    conn.commit()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not session.get('logged_in'): return redirect(url_for('login'))
        return f(*args, **kwargs)
    return dec

CSS = """
<style>
    body { font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; background: #f0f2f5; font-size: 12px; }
    .sidebar { width: 220px; background: #2c3e50; color: white; height: 100vh; position: fixed; padding: 20px; box-sizing: border-box; }
    .sidebar h2 { color: #3498db; text-align: center; border-bottom: 1px solid #34495e; padding-bottom: 10px; }
    .sidebar a { color: #bdc3c7; text-decoration: none; display: block; padding: 12px; border-radius: 5px; margin-bottom: 5px; }
    .sidebar a:hover { background: #34495e; color: white; }
    .main { margin-left: 230px; padding: 25px; }
    .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; min-width: 1000px; }
    th { background: #34495e; color: white; padding: 10px; border: 1px solid #ddd; font-size: 10px; text-transform: uppercase; }
    td { padding: 10px; border: 1px solid #ddd; text-align: center; }
    .btn { background: #3498db; color: white; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-weight: bold; font-size: 11px; }
    .btn-print { background: #e67e22; }
    input, select, textarea { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
    @media print { .sidebar, .btn, .no-print { display: none !important; } .main { margin-left: 0; padding: 0; } .card { box-shadow: none; border: none; } }
</style>
"""

LAYOUT = """
<!DOCTYPE html>
<html>
<head><title>Nimbus ERP Final</title>{{ css|safe }}</head>
<body>
    <div class="sidebar">
        <h2>NIMBUS</h2>
        <a href="/">📊 Master Ledger</a>
        <a href="/directory">📂 Tenant Directory</a>
        <a href="/enroll">➕ New Tenant</a>
        <a href="/reports">📋 Reports & Clearance</a>
        <a href="/logout" style="color:#e74c3c; margin-top:50px;">Logout</a>
    </div>
    <div class="main">
        {% if p == 'dash' %}
            <h1>Master Collection Report</h1>
            <div class="card">
                <table>
                    <tr>
                        <th>Period</th><th>Tenant</th><th>Basic</th><th>VAT(12%)</th><th>W-Tax(5%)</th>
                        <th>Signage</th><th>Utils</th><th>Total Paid</th><th>Check No</th><th>DS Series</th><th>Date Paid</th><th>Remarks</th>
                    </tr>
                    {% for r in all_ledger %}
                    <tr>
                        <td>{{ r[2] }}</td><td><b>{{ r[15] }}</b></td><td>{{ r[3] }}</td><td>{{ r[4] }}</td>
                        <td style="color:red;">-{{ r[5] }}</td><td>{{ r[6] }}</td><td>{{ r[7]+r[8] }}</td>
                        <td style="font-weight:bold; color:green;">₱{{"%.2f"|format(r[9])}}</td>
                        <td>{{ r[11] or 'CASH' }}</td><td>{{ r[12] }}</td><td>{{ r[13] }}</td><td>{{ r[14] }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

        {% elif p == 'reports' %}
            <h1>Reports & Printing</h1>
            <div class="card">
                <h3>Generate Tenant Clearance</h3>
                <form action="/clearance" method="GET">
                    Select Tenant: 
                    <select name="tid" required>
                        {% for t in tenants %}<option value="{{t[0]}}">{{t[1]}} - {{t[7]}}</option>{% endfor %}
                    </select>
                    <button type="submit" class="btn btn-print">Generate Clearance Certificate</button>
                </form>
                <hr>
                <h3>Monthly Report Summary</h3>
                <button onclick="window.print()" class="btn">Print Current Dashboard Report</button>
            </div>

        {% elif p == 'clearance' %}
            <div style="max-width:800px; margin:auto; padding:50px; background:white; border:2px solid #333; text-align:center;">
                <h1 style="margin:0;">CERTIFICATE OF CLEARANCE</h1>
                <p>Nimbus Property Management Group</p>
                <hr>
                <div style="text-align:left; margin-top:40px; font-size:16px; line-height:1.8;">
                    <p>Date: <b>{{ today }}</b></p>
                    <p>To Whom It May Concern,</p>
                    <p>This is to certify that <b>{{ t[1] }}</b>, occupying a <b>{{ t[4] }}</b> unit at <b>{{ t[7] }}</b>, 
                    has cleared all financial obligations including rentals, VAT, and utility bills as of this date.</p>
                    <p>This clearance is issued for whatever legal purpose it may serve.</p>
                </div>
                <div style="margin-top:100px; display:flex; justify-content:space-between;">
                    <div style="border-top:1px solid #000; width:200px;">Tenant Signature</div>
                    <div style="border-top:1px solid #000; width:200px;">Authorized Manager</div>
                </div>
                <br><br>
                <button onclick="window.print()" class="btn btn-print no-print">Print Clearance</button>
                <a href="/reports" class="btn no-print" style="background:#7f8c8d;">Back</a>
            </div>

        {% elif p == 'dir' %}
            <h1>Tenant Directory</h1>
            <div class="card">
                <table>
                    <tr><th>Name</th><th>Building</th><th>Type</th><th>Basic Rent</th><th>Action</th></tr>
                    {% for t in tenants %}
                    <tr><td><b>{{t[1]}}</b></td><td>{{t[7]}}</td><td>{{t[4]}}</td><td>₱{{t[5]}}</td><td><a href="/profile/{{t[0]}}" class="btn">View Ledger</a></td></tr>
                    {% endfor %}
                </table>
            </div>

        {% elif p == 'enr' %}
            <div class="card" style="max-width:500px; margin:auto;">
                <h2>Enroll Tenant</h2>
                <form action="/save_t" method="POST">
                    Name: <input name="name" required>
                    Building: <select name="prop_id">{% for pr in props %}<option value="{{pr[0]}}">{{pr[1]}}</option>{% endfor %}</select>
                    Type: <select name="t_type"><option>Commercial</option><option>Residential</option></select>
                    Monthly Rent: <input name="rent" type="number" step="0.01" required>
                    <button type="submit" class="btn" style="width:100%;">Save Tenant</button>
                </form>
            </div>

        {% elif p == 'profile' %}
            <h1>{{t[1]}} - Personal Ledger</h1>
            <div class="card">
                <a href="/add_l/{{t[0]}}" class="btn" style="background:#27ae60; margin-bottom:15px;">➕ Add New Payment</a>
                <table>
                    <tr><th>Period</th><th>Basic</th><th>VAT</th><th>W-Tax</th><th>Total Paid</th><th>Date</th><th>Remarks</th></tr>
                    {% for l in ledger %}
                    <tr><td>{{l[2]}}</td><td>₱{{l[3]}}</td><td>{{l[4]}}</td><td>{{l[5]}}</td><td><b>₱{{"%.2f"|format(l[9])}}</b></td><td>{{l[13]}}</td><td>{{l[14]}}</td></tr>
                    {% endfor %}
                </table>
            </div>

        {% elif p == 'add_l' %}
            <div class="card" style="max-width:600px; margin:auto;">
                <h2>Post Payment: {{t[1]}}</h2>
                <form action="/save_l" method="POST">
                    <input type="hidden" name="tid" value="{{t[0]}}">
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
                        <div>Billing Period: <input name="period" required placeholder="March 2026"></div>
                        <div>Basic Rent: <input name="basic" type="number" step="0.01" value="{{t[5]}}"></div>
                        <div>Signage/Mainte: <input name="signage" type="number" step="0.01" value="0"></div>
                        <div>Electric: <input name="elec" type="number" step="0.01" value="0"></div>
                        <div>Water: <input name="water" type="number" step="0.01" value="0"></div>
                        <div>Check No: <input name="check_no" placeholder="N/A"></div>
                        <div>DS Series: <input name="ds_series" placeholder="0001"></div>
                        <div>Date Paid: <input type="date" name="d_paid" required></div>
                    </div>
                    Remarks: <textarea name="remarks"></textarea>
                    <button type="submit" class="btn" style="width:100%; margin-top:15px; background:#2c3e50;">Save Transaction</button>
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
    conn = sqlite3.connect(DB)
    all_ledger = conn.execute("SELECT ledger.*, tenants.name FROM ledger JOIN tenants ON ledger.t_id = tenants.id ORDER BY ledger.id DESC").fetchall()
    conn.close()
    return render_template_string(LAYOUT, p='dash', all_ledger=all_ledger, css=CSS)

@app.route("/reports")
@login_required
def reports():
    conn = sqlite3.connect(DB)
    tenants = conn.execute("SELECT tenants.*, properties.name FROM tenants JOIN properties ON tenants.prop_id = properties.id").fetchall()
    conn.close()
    return render_template_string(LAYOUT, p='reports', tenants=tenants, css=CSS)

@app.route("/clearance")
@login_required
def clearance():
    tid = request.args.get('tid')
    conn = sqlite3.connect(DB)
    t = conn.execute("SELECT tenants.*, properties.name FROM tenants JOIN properties ON tenants.prop_id = properties.id WHERE tenants.id=?", (tid,)).fetchone()
    conn.close()
    from datetime import date
    return render_template_string(LAYOUT, p='clearance', t=t, today=date.today().strftime("%B %d, %Y"), css=CSS)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST" and request.form.get("pw") == "admin123":
        session['logged_in'] = True
        return redirect(url_for('dash'))
    return '<body style="display:grid; place-items:center; height:100vh; background:#2c3e50;"><form method="POST" style="background:white; padding:40px; border-radius:10px;"><h2>NIMBUS ERP</h2><input type="password" name="pw" placeholder="Password"><br><br><button class="btn" style="width:100%;">Login</button></form></body>'

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('login'))

@app.route("/directory")
@login_required
def dir():
    conn = sqlite3.connect(DB)
    tenants = conn.execute("SELECT tenants.*, properties.name FROM tenants JOIN properties ON tenants.prop_id = properties.id").fetchall()
    conn.close()
    return render_template_string(LAYOUT, p='dir', tenants=tenants, css=CSS)

@app.route("/enroll")
@login_required
def enr():
    conn = sqlite3.connect(DB); props = conn.execute("SELECT * FROM properties").fetchall(); conn.close()
    return render_template_string(LAYOUT, p='enr', props=props, css=CSS)

@app.route("/profile/<tid>")
@login_required
def profile(tid):
    conn = sqlite3.connect(DB); t = conn.execute("SELECT tenants.*, properties.name FROM tenants JOIN properties ON tenants.prop_id = properties.id WHERE tenants.id=?", (tid,)).fetchone()
    ledger = conn.execute("SELECT * FROM ledger WHERE t_id=?", (tid,)).fetchall(); conn.close()
    return render_template_string(LAYOUT, p='profile', t=t, ledger=ledger, css=CSS)

@app.route("/add_l/<tid>")
@login_required
def add_l(tid):
    conn = sqlite3.connect(DB); t = conn.execute("SELECT * FROM tenants WHERE id=?", (tid,)).fetchone(); conn.close()
    return render_template_string(LAYOUT, p='add_l', t=t, css=CSS)

@app.route("/save_t", methods=["POST"])
@login_required
def save_t():
    f = request.form; conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO tenants (id, name, prop_id, t_type, rent) VALUES (?,?,?,?,?)", 
                 (str(uuid.uuid4())[:8], f['name'], int(f['prop_id']), f['t_type'], float(f['rent'])))
    conn.commit(); conn.close(); return redirect(url_for('dir'))

@app.route("/save_l", methods=["POST"])
@login_required
def save_l():
    f = request.form; basic = float(f['basic']); vat, wtax = basic * 0.12, basic * 0.05
    total = (basic + vat + float(f['signage']) + float(f['elec']) + float(f['water'])) - wtax
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO ledger (t_id, period, basic, vat, wtax, signage, electric, water, total, due_date, check_no, ds_series, date_paid, remarks) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 (f['tid'], f['period'], basic, vat, wtax, float(f['signage']), float(f['elec']), float(f['water']), total, '', f['check_no'], f['ds_series'], f['d_paid'], f['remarks']))
    conn.commit(); conn.close(); return redirect(url_for('dash'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
