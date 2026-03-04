import os, sqlite3, uuid
from flask import Flask, render_template_string, request, redirect, session, url_for
from functools import wraps

app = Flask(__name__)
app.secret_key = "nimbus_v33_port8080"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Gumamit ng bagong database para iwas error sa columns
DB_PATH = os.path.join(BASE_DIR, "nimbus_final_db.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS properties (id INTEGER PRIMARY KEY, name TEXT, type TEXT)")
        
        # Complete Tenant Profile Columns base sa listahan mo
        c.execute("""CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY, name TEXT, biz_name TEXT, birthday TEXT, citizenship TEXT, 
            civil_status TEXT, tel_no TEXT, mobile_no TEXT, religion TEXT, email TEXT, 
            res_address TEXT, res_type TEXT, stay_length TEXT, leave_reason TEXT,
            occupation TEXT, salary REAL, co_address TEXT, co_contact TEXT,
            prop_id INTEGER, t_type TEXT, rent REAL, sec_deposit REAL)""")

        # Default Buildings
        props = [
            (1,'Kapasigan Building','Commercial'),(2,'Rosario Building','Comm+Res'),
            (3,'Marikina Building','Commercial'),(4,'Camarin 1 Building','Commercial'),
            (5,'Camarin 3 Building','Comm+Res'),(6,'Market Ave Palatiw','Commercial'),
            (7,'MB Old Apartment','Residential'),(8,'MB New Apartment','Residential'),
            (9,'Tagaytay 1','Commercial'),(10,'Tagaytay 2','Commercial'),
            (11,'Camarin 2','Commercial'),(12,'Pateros','Comm+Res')
        ]
        c.executemany("INSERT OR IGNORE INTO properties VALUES (?,?,?)", props)
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
    body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
    .card { background: white; max-width: 850px; margin: auto; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
    h1 { color: #1a365d; border-bottom: 3px solid #3182ce; padding-bottom: 10px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
    input, select { width: 100%; padding: 12px; margin-top: 5px; border: 1px solid #cbd5e0; border-radius: 8px; box-sizing: border-box; }
    label { font-weight: bold; color: #4a5568; margin-top: 10px; display: block; }
    .btn { background: #2b6cb0; color: white; padding: 15px; border: none; width: 100%; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 20px; }
    .btn:hover { background: #2c5282; }
    .nav { text-align: center; margin-bottom: 20px; }
    .nav a { color: #2b6cb0; text-decoration: none; font-weight: bold; margin: 0 15px; }
</style>
"""

LAYOUT = """
<!DOCTYPE html>
<html>
<head><title>Nimbus Dev & Leasing Corp</title>{{ css|safe }}</head>
<body>
    <div class="nav">
        <a href="/">🏠 Home</a> | <a href="/enroll">➕ Enroll Tenant</a> | <a href="/logout">🚪 Logout</a>
    </div>
    <div class="card">
        {% if p == 'dash' %}
            <h1>Nimbus Dashboard</h1>
            <p>System is running on <b>Port 8080</b>.</p>
            <div style="background: #ebf8ff; padding: 20px; border-radius: 10px; color: #2c5282;">
                <b>Property Management System Online</b><br>
                Handa na ang database para sa Nimbus Development and Leasing Corporation.
            </div>
            <br>
            <a href="/enroll" style="text-decoration:none;"><button class="btn">Magsimula: Mag-enroll ng Tenant</button></a>

        {% elif p == 'enr' %}
            <h1>New Tenant Profile</h1>
            <form action="/save_t" method="POST">
                <div class="grid">
                    <div><label>Name</label><input name="name" required></div>
                    <div><label>Business Name</label><input name="biz_name"></div>
                    <div><label>Birthday</label><input type="date" name="birthday"></div>
                    <div><label>Citizenship</label><input name="citizenship"></div>
                    <div><label>Civil Status</label>
                        <select name="civil_status">
                            <option>Single</option><option>Married</option><option>Widowed</option><option>Separated</option>
                        </select>
                    </div>
                    <div><label>Mobile Number</label><input name="mobile_no"></div>
                    <div><label>Monthly Rent</label><input type="number" step="0.01" name="rent" required></div>
                    <div><label>Building</label>
                        <select name="prop_id">
                            {% for pr in props %} <option value="{{pr[0]}}">{{pr[1]}} ({{pr[2]}})</option> {% endfor %}
                        </select>
                    </div>
                </div>
                <button type="submit" class="btn">SAVE PROFILE</button>
            </form>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/")
@login_required
def dash(): return render_template_string(LAYOUT, p='dash', css=CSS)

@app.route("/enroll")
@login_required
def enroll():
    conn = sqlite3.connect(DB_PATH); props = conn.execute("SELECT * FROM properties").fetchall(); conn.close()
    return render_template_string(LAYOUT, p='enr', props=props, css=CSS)

@app.route("/save_t", methods=["POST"])
def save_t():
    f = request.form
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""INSERT INTO tenants (id, name, biz_name, birthday, citizenship, civil_status, mobile_no, prop_id, rent) 
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                   (str(uuid.uuid4())[:8], f['name'], f['biz_name'], f['birthday'], f['citizenship'], f['civil_status'], f['mobile_no'], f['prop_id'], f['rent']))
        conn.commit(); conn.close()
        return redirect('/')
    except Exception as e:
        return f"Error: {e}"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST" and request.form.get("pw") == "admin123":
        session['logged_in'] = True; return redirect('/')
    return '<body style="font-family:sans-serif; text-align:center; padding-top:100px;"><h2>Nimbus Admin</h2><form method="POST"><input type="password" name="pw" placeholder="Password"><button>Login</button></form></body>'

@app.route("/logout")
def logout(): session.clear(); return redirect('/login')

if __name__ == "__main__":
    # GUMAGAMIT NA NG PORT 8080
    app.run(debug=True, host="0.0.0.0", port=8080)
