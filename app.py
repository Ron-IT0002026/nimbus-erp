from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# 1. DATABASE CONFIGURATION
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'nimbus_leasing.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 2. DATABASE MODEL
class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    bus_name = db.Column(db.String(100))
    property_name = db.Column(db.String(100))
    father_name = db.Column(db.String(100))
    mother_name = db.Column(db.String(100))
    f_health = db.Column(db.String(100))
    m_health = db.Column(db.String(100))
    basic_rent = db.Column(db.Float)
    vat_12 = db.Column(db.Float)
    wht_5 = db.Column(db.Float)
    total_rent = db.Column(db.Float)

# 3. HTML TEMPLATES (LAYOUT, INDEX, DASHBOARD)
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nimbus Leasing System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f7f6; font-family: 'Segoe UI', sans-serif; }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .navbar { background-color: #2c3e50 !important; }
        .btn-primary { background-color: #3498db; border: none; }
        .table-container { background: white; padding: 20px; border-radius: 12px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-4 text-center">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">NIMBUS DEVELOPMENT</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/">Register Tenant</a>
                <a class="nav-link" href="/dashboard">Dashboard & Reports</a>
            </div>
        </div>
    </nav>
    <div class="container"> {% block content %} {% endblock %} </div>
</body>
</html>
"""

INDEX_HTML = """
{% extends "layout" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card p-4">
            <h3 class="text-center mb-4 text-primary">Tenant Information Profile</h3>
            <form action="/submit" method="POST">
                <div class="row g-3">
                    <div class="col-md-6"><label class="form-label">Full Name</label><input type="text" name="name" class="form-control" required></div>
                    <div class="col-md-6"><label class="form-label">Business Name</label><input type="text" name="bus_name" class="form-control"></div>
                    <div class="col-md-12">
                        <label class="form-label">Assign Property</label>
                        <select name="property" class="form-select">
                            <option>1 Kapasigan Building- commercial</option>
                            <option>2 Rosario building - commercial+residential</option>
                            <option>3 marikina building - commercial</option>
                            <option>12 pateros - commercial + residential</option>
                        </select>
                    </div>
                    <hr class="my-4">
                    <h5 class="text-secondary">Parental Information & Health</h5>
                    <div class="col-md-6"><input type="text" name="father_name" class="form-control" placeholder="Father's Name"></div>
                    <div class="col-md-6"><input type="text" name="f_health" class="form-control" placeholder="Father's Health Condition"></div>
                    <div class="col-md-6"><input type="text" name="mother_name" class="form-control" placeholder="Mother's Name"></div>
                    <div class="col-md-6"><input type="text" name="m_health" class="form-control" placeholder="Mother's Health Condition"></div>
                    <hr class="my-4">
                    <h5 class="text-secondary">Financial Setup</h5>
                    <div class="col-md-12">
                        <label class="form-label">Basic Monthly Rent (PHP)</label>
                        <input type="number" name="basic_rent" step="0.01" class="form-control" placeholder="0.00" required>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary mt-4 w-100 py-2 fw-bold">Save & Generate Ledger</button>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""

DASHBOARD_HTML = """
{% extends "layout" %}
{% block content %}
<div class="row mb-4">
    <div class="col-md-4">
        <div class="card bg-primary text-white p-3 shadow-sm">
            <h5>Total Sales Revenue</h5>
            <h2>₱ {{ "{:,.2f}".format(total_revenue) }}</h2>
        </div>
    </div>
</div>
<div class="table-container shadow-sm">
    <table class="table table-striped">
        <thead class="table-dark">
            <tr>
                <th>Tenant / Business</th>
                <th>Property</th>
                <th>Parents & Health</th>
                <th>Monthly Dues</th>
            </tr>
        </thead>
        <tbody>
            {% for t in tenants %}
            <tr>
                <td><strong>{{ t.name }}</strong><br><small>{{ t.bus_name }}</small></td>
                <td>{{ t.property_name }}</td>
                <td>F: {{ t.father_name }} ({{ t.f_health }})<br>M: {{ t.mother_name }} ({{ t.m_health }})</td>
                <td>₱ {{ "{:,.2f}".format(t.total_rent) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
"""

# 4. ROUTES & LOGIC
@app.route('/')
def index():
    return render_template_string(LAYOUT.replace("{% block content %} {% endblock %}", INDEX_HTML))

@app.route('/submit', methods=['POST'])
def submit():
    basic = float(request.form.get('basic_rent', 0))
    vat = basic * 0.12
    wht = basic * 0.05
    total = (basic + vat) - wht
    new_tenant = Tenant(
        name=request.form.get('name'), bus_name=request.form.get('bus_name'),
        property_name=request.form.get('property'), father_name=request.form.get('father_name'),
        mother_name=request.form.get('mother_name'), f_health=request.form.get('f_health'),
        m_health=request.form.get('m_health'), basic_rent=basic, vat_12=vat,
        wht_5=wht, total_rent=total
    )
    db.session.add(new_tenant)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    search = request.args.get('search', '')
    if search:
        tenants = Tenant.query.filter(Tenant.name.contains(search) | Tenant.bus_name.contains(search)).all()
    else:
        tenants = Tenant.query.all()
    total_rev = sum(t.total_rent for t in tenants)
    return render_template_string(LAYOUT.replace("{% block content %} {% endblock %}", DASHBOARD_HTML), 
                                  tenants=tenants, total_revenue=total_rev, search=search)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
