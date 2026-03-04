import os, sqlite3, uuid
from flask import Flask, render_template_string, request, redirect, session

app = Flask(__name__)
app.secret_key = "nimbus_2026_key"
DB_PATH = "nimbus_final_system.db"

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Simplified Table muna para iwas crash
    c.execute("CREATE TABLE IF NOT EXISTS properties (id INTEGER PRIMARY KEY, name TEXT)")
    c.execute("""CREATE TABLE IF NOT EXISTS tenants (
        id TEXT PRIMARY KEY, name TEXT, biz_name TEXT, rent REAL, prop_id INTEGER)""")
    
    props = [(1,'Kapasigan'),(2,'Rosario'),(3,'Marikina'),(4,'Camarin 1'),(5,'Camarin 3'),
             (6,'Palatiw'),(7,'MB Old'),(8,'MB New'),(9,'Tagaytay 1'),(10,'Tagaytay 2'),
             (11,'Camarin 2'),(12,'Pateros')]
    c.executemany("INSERT OR IGNORE INTO properties VALUES (?,?)", props)
    conn.commit()
    conn.close()

init_db()

# --- DESIGN ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Nimbus ERP</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; background: #f0f2f5; }
        .box { background: white; padding: 30px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        input, select { display: block; width: 100%; margin: 10px 0; padding: 10px; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Nimbus Dev & Leasing Corp</h2>
        {% if not logged %}
            <form method="POST" action="/login">
                <input type="password" name="pw" placeholder="Admin Password" required>
                <button>Login</button>
            </form>
        {% else %}
            <p>Welcome, Admin! | <a href="/logout">Logout</a></p>
            <hr>
            <h3>Enroll New Tenant</h3>
            <form method="POST" action="/save">
                <input name="name" placeholder="Tenant Name" required>
                <input name="biz_name" placeholder="Business Name">
                <input name="rent" type="number" placeholder="Rent Amount" required>
                <select name="prop_id">
                    {% for p in props %} <option value="{{p[0]}}">{{p[1]}}</option> {% endfor %}
                </select>
                <button>Save Tenant</button>
            </form>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    conn = sqlite3.connect(DB_PATH)
    props = conn.execute("SELECT * FROM properties").fetchall()
    conn.close()
    return render_template_string(HTML_PAGE, logged=session.get('logged'), props=props)

@app.route("/login", methods=["POST"])
def login():
    if request.form.get("pw") == "admin123":
        session['logged'] = True
    return redirect("/")

@app.route("/save", methods=["POST"])
def save():
    if not session.get('logged'): return redirect("/")
    f = request.form
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO tenants (id, name, biz_name, rent, prop_id) VALUES (?,?,?,?,?)",
                 (str(uuid.uuid4())[:8], f['name'], f['biz_name'], f['rent'], f['prop_id']))
    conn.commit()
    conn.close()
    return "<h1>Saved Successfully!</h1><a href='/'>Go Back</a>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    # Sinigurado nating Port 9999
    app.run(host="127.0.0.1", port=9999, debug=True)
