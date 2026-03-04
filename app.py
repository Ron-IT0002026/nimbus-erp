import os, sqlite3, uuid
from flask import Flask, render_template_string, request, redirect, session, url_for
from functools import wraps

app = Flask(__name__)
app.secret_key = "nimbus_v33_utility_pro"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nimbus_erp.db")

# --- DATABASE INIT ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS properties (id INTEGER PRIMARY KEY, name TEXT)")
        c.execute("""CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY, name TEXT, prop_id INTEGER, t_type TEXT, rent REAL,
            phone TEXT, email TEXT, emergency_contact TEXT, start_date TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT, t_id TEXT, period TEXT, 
            basic REAL, vat REAL, wtax REAL, signage REAL, 
            prev_elec REAL, curr_elec REAL, prev_water REAL, curr_water REAL,
            elec_amount REAL, water_amount REAL, total REAL, 
            check_no TEXT, ds_series TEXT, date_paid TEXT, remarks TEXT)""")
        
        # Default Properties
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

# --- STYLES ---
CSS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #f4f7f6; font-size: 13px; }
    .sidebar { width: 230px; background: #2d3748; color: white; height: 100vh; position: fixed; padding: 20px; }
    .sidebar h2 { color: #63b3ed; text-align: center; margin-bottom: 30px; }
    .sidebar a { color: #edf2f7; text-decoration: none; display: block; padding: 12px; border-radius: 8px; margin-bottom: 5px; }
    .sidebar a:hover { background: #4a5568; }
    .main { margin-left: 250px; padding: 30px; }
    .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { padding: 12px; border: 1px solid #e2e8f0; text-align: center; }
    th { background: #edf2f7; font-size: 11px; text-transform: uppercase; color: #4a5568; }
    .btn { background: #3182ce; color: white; padding: 10px 15px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-weight: bold; }
    .summary-box { display: flex; gap: 20px; margin-bottom: 20px; }
    .s-card { flex: 1; padding: 20px; border-radius: 12px; color: white; text-align: center; }
    .bg-blue { background: #4299e1; } .bg-green { background: #48bb78; } .bg-orange { background: #ed8936; }
    input, select, textarea { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #e2e8f0; border-radius: 6px; box-sizing: border-box; }
</style>
"""

LAYOUT = """
<!DOCTYPE html>
<html>
<head><title>Nimbus ERP v33</title>{{ css|safe }}</head>
<body>
    <div class="sidebar">
        <h2>NIMBUS ERP</h2>
        <a href="/">📊 Master Ledger</a>
        <a href="/directory">📂 Tenant List</a>
        <a href="/utility">🚰 Utility Tracking</a>
        <a href="/enroll">➕ New Tenant</a>
        <hr style="border: 0.5px solid #4a5568; margin: 20px 0;">
        <a href="/logout" style="color:#feb2b2;">Logout</a>
    </div>
    <div class="main">
        {% if p == 'dash' %}
            <h1>Master Collection</h1>
            <div class="card">
                <table>
                    <tr><th>Period</th><th>Tenant</th><th>Rent</th><th>VAT</th><th>Utils</th><th>Total</th><th>Date</th></tr>
                    {% for r in data %}
                    <tr>
                        <td>{{r[2]}}</td><td><b>{{r[18]}}</b></td><td>₱{{r[3]}}</td><td>{{r[4]}}</td>
                        <td>₱{{r[11]+r[12]}}</td><td style="font-weight:bold; color:#2f855a;">₱{{"%.2f"|format(r[13])}}</td><td>{{r[16]}}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

        {% elif p == 'utility' %}
            <h1>Utility Consumption & Rates</h1>
            <div class="summary-box">
                <div class="s-card bg-blue"><h3>Total Elec</h3>₱{{summary.elec}}</div>
                <div class="s-card bg-green"><h3>Total Water</h3>₱{{summary.water}}</div>
                <div class="s-card bg-orange"><h3>Active Tenants</h3>{{summary.count}}</div>
            </div>
            <div class="card">
                <h3>Consumption Summary</h3>
                <table>
                    <tr><th>Tenant</th><th>Elec (Prev/Curr)</th><th>Water (Prev/Curr)</th><th>Elec Amount</th><th>Water Amount</th><th>Period</th></tr>
                    {% for u in utils %}
                    <tr>
                        <td><b>{{u.t_name}}</b></td>
                        <td>{{u.prev_elec}} → {{u.curr_elec}}</td>
                        <td>{{u.prev_water}} → {{u.curr_water}}</td>
                        <td style="color:#2b6cb0;">₱{{u.elec_amount}}</td>
                        <td style="color:#2b6cb0;">₱{{u.water_amount}}</td>
                        <td>{{u.period}}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

        {% elif p == 'dir' %}
            <h1>Tenant Directory</h1>
            <div class="card">
                <table>
                    <tr><th>Name</th><th>Building</th><th>Type</th><th>Rent</th><th>Action</th></tr>
                    {% for t in tenants %}
                    <tr><td><b>{{t[1]}}</b></td><td>{{t[9]}}</td><td>{{t[3]}}</td><td>₱{{t[4]}}</td><td><a href="/add_l/{{t[0]}}" class="btn">Billing</a></td></tr>
                    {% endfor %}
                </table>
            </div>

        {% elif p == 'add_l' %}
            <div class="card" style="max-width:800px; margin:auto;">
                <h2>Post Billing & Utility Reading: {{t[1]}}</h2>
                <form action="/save_l" method="POST">
                    <input type="hidden" name="tid" value="{{t[0]}}">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px;">
                        <div>Period: <input name="period" required placeholder="May 2026"></div>
                        <div>Date Paid: <input type="date" name="d_paid" required></div>
                        <div>Basic Rent: <input name="basic" type="number" step="0.01" value="{{t[4]}}"></div>
                        <div>Signage: <input name="signage" type="number" step="0.01" value="0"></div>
                    </div>
                    <h4 style="color:#3182ce; border-bottom:1px solid #e2e8f0; margin-top:20px;">Electric Meter Reading</h4>
                    <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px;">
                        <div>Previous: <input name="p_elec" type="number" step="0.1" value="0"></div>
                        <div>Current: <input name="c_elec" type="number" step="0.1" value="0"></div>
                        <div>Amount (₱): <input name="e_amt" type="number" step="0.01" value="0"></div>
                    </div>
                    <h4 style="color:#3182ce; border-bottom:1px solid #e2e8f0; margin-top:20px;">Water Meter Reading</h4>
                    <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px;">
                        <div>Previous: <input name="p_water" type="number" step="0.1" value="0"></div>
                        <div>Current: <input name="c_water" type="number" step="0.1" value="0"></div>
                        <div>Amount (₱): <input name="w_amt" type="number" step="0.01" value="0"></div>
                    </div>
                    <button type="submit" class="btn" style="width:100%; margin-top:20px; background:#2d3748;">Post Transaction</button>
                </form>
            </div>
        {% elif p == 'enr' %}
            <div class="card" style="max-width:500px; margin:auto;">
                <h2>New Tenant</h2>
                <form action="/save_t" method="POST">
                    Name: <input name="name" required>
                    Phone: <input name="phone">
                    Rent: <input name="rent" type="number" step="0.01" required>
                    Building: <select name="prop_id">{% for pr in props %}<option value="{{pr[0]}}">{{pr[1]}}</option>{% endfor %}</select>
                    Type: <select name="t_type"><option>Commercial</option><option>Residential</option></select>
                    <button type="submit" class="btn" style="width:100%;">Save</button>
                </form>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# --- ROUTES ---

@app.route("/")
@login_required
def dash():
    conn = sqlite3.connect(DB_PATH)
    data = conn.execute("SELECT ledger.*, tenants.name FROM ledger LEFT JOIN tenants ON ledger.t_id = tenants.id ORDER BY ledger.id DESC").fetchall()
    conn.close()
    return render_template_string(LAYOUT, p='dash', data=data, css=CSS)

@app.route("/utility")
@login_required
def utility():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    utils = conn.execute("SELECT ledger.*, tenants.name as t_name FROM ledger JOIN tenants ON ledger.t_id = tenants.id ORDER BY ledger.id DESC").fetchall()
    
    # Calculate Summary
    stats = conn.execute("SELECT SUM(elec_amount), SUM(water_amount), COUNT(DISTINCT t_id) FROM ledger").fetchone()
    summary = {'elec': stats[0] or 0, 'water': stats[1] or 0, 'count': stats[2] or 0}
    
    conn.close()
    return render_template_string(LAYOUT, p='utility', utils=utils, summary=summary, css=CSS)

@app.route("/directory")
@login_required
def directory():
    conn = sqlite3.connect(DB_PATH)
    tenants = conn.execute("SELECT tenants.*, properties.name FROM tenants LEFT JOIN properties ON tenants.prop_id = properties.id").fetchall()
    conn.close()
    return render_template_string(LAYOUT, p='dir', tenants=tenants, css=CSS)

@app.route("/enroll")
@login_required
def enroll():
    conn = sqlite3.connect(DB_PATH); props = conn.execute("SELECT * FROM properties").fetchall(); conn.close()
    return render_template_string(LAYOUT, p='enr', props=props, css=CSS)

@app.route("/save_t", methods=["POST"])
def save_t():
    f = request.form; conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO tenants (id, name, prop_id, t_type, rent, phone) VALUES (?,?,?,?,?,?)",
               (str(uuid.uuid4())[:8], f['name'], f['prop_id'], f['t_type'], f['rent'], f['phone']))
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
    conn.execute("""INSERT INTO ledger (t_id, period, basic, vat, wtax, signage, 
                    prev_elec, curr_elec, prev_water, curr_water, elec_amount, water_amount, total, date_paid) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                 (f['tid'], f['period'], basic, vat, wtax, f['signage'], f['p_elec'], f['c_elec'], f['p_water'], f['c_water'], e_amt, w_amt, total, f['d_paid']))
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
