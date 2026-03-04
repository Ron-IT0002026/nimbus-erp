from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'nimbus_leasing.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODEL ---
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
    total_rent = db.Column(db.Float)

# --- MODERN CSS & LAYOUT ---
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nimbus Development & Leasing</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #f8f9fa; font-family: 'Inter', sans-serif; display: flex; min-height: 100vh; overflow-x: hidden; }
        .sidebar { width: 260px; background: white; border-right: 1px solid #e0e0e0; padding: 20px; display: flex; flex-direction: column; position: fixed; height: 100vh; }
        .main-content { margin-left: 260px; flex: 1; padding: 30px; }
        .nav-link { color: #6c757d; font-weight: 500; padding: 12px 15px; border-radius: 8px; margin-bottom: 5px; transition: 0.3s; }
        .nav-link:hover, .nav-link.active { background: #eef2ff; color: #4f46e5; }
        .nav-link i { margin-right: 10px; }
        .stat-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #eef0f2; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        .card-title { color: #64748b; font-size: 0.875rem; font-weight: 600; text-transform: uppercase; }
        .card-value { font-size: 1.5rem; font-weight: 700; margin-top: 5px; }
        .btn-nimbus { background: #0f172a; color: white; border-radius: 8px; padding: 10px 20px; font-weight: 600; }
        .form-section { background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .form-label { font-weight: 600; color: #334155; }
        .table thead { background: #f8fafc; color: #64748b; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h4 class="fw-bold text-primary mb-4"><i class="fa-solid fa-building"></i> Nimbus</h4>
        <nav class="nav flex-column">
            <a class="nav-link {% if page == 'dashboard' %}active{% endif %}" href="/dashboard"><i class="fa-solid fa-gauge"></i> Dashboard</a>
            <a class="nav-link {% if page == 'register' %}active{% endif %}" href="/"><i class="fa-solid fa-user-plus"></i> Tenant Profile</a>
            <a class="nav-link" href="#"><i class="fa-solid fa-file-invoice-dollar"></i> Ledger</a>
            <a class="nav-link" href="#"><i class="fa-solid fa-bolt"></i> Utility Billing</a>
            <a class="nav-link" href="#"><i class="fa-solid fa-chart-line"></i> Reports</a>
        </nav>
    </div>
    <div class="main-content">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

INDEX_HTML = """
{% extends "layout" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>Tenant Profile</h2>
    <button class="btn btn-nimbus">+ New Tenant</button>
</div>
<div class="form-section">
    <h5 class="mb-4 border-bottom pb-2">New Tenant Information</h5>
    <form action="/submit" method="POST">
        <div class="row g-3">
            <div class="col-md-6">
                <label class="form-label">Full Name</label>
                <input type="text" name="name" class="form-control bg-light border-0" placeholder="Juan Dela Cruz" required>
            </div>
            <div class="col-md-6">
                <label class="form-label">Business Name</label>
                <input type="text" name="bus_name" class="form-control bg-light border-0" placeholder="Bakery / Shop Name">
            </div>
            <div class="col-md-12">
                <label class="form-label">Property Location</label>
                <select name="property" class="form-select bg-light border-0">
                    <option>1 Kapasigan Building - Commercial</option>
                    <option>2 Rosario Building - Comm+Res</option>
                    <option>12 Pateros Building - Comm+Res</option>
                </select>
            </div>
            <div class="col-md-6">
                <label class="form-label">Father's Name</label>
                <input type="text" name="father_name" class="form-control bg-light border-0">
            </div>
            <div class="col-md-6">
                <label class="form-label">Father's Health Status</label>
                <input type="text" name="f_health" class="form-control bg-light border-0">
            </div>
            <div class="col-md-12 mt-4">
                <label class="form-label">Monthly Basic Rent (PHP)</label>
                <input type="number" name="basic_rent" class="form-control bg-light border-0" step="0.01" required>
            </div>
            <div class="col-md-12 mt-4">
                <button type="submit" class="btn btn-nimbus w-100"><i class="fa-solid fa-save"></i> Save Tenant Data</button>
            </div>
        </div>
    </form>
</div>
{% endblock %}
"""

DASHBOARD_HTML = """
{% extends "layout" %}
{% block content %}
<h2 class="mb-4">Dashboard Overview</h2>
<div class="row g-4 mb-5">
    <div class="col-md-3">
        <div class="stat-card">
            <div class="card-title">Total Tenants</div>
            <div class="card-value">{{ tenants|length }}</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card">
            <div class="card-title">Active Contracts</div>
            <div class="card-value">{{ tenants|length }}</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card">
            <div class="card-title text-success">Total Revenue</div>
            <div class="card-value">₱ {{ "{:,.2f}".format(total_revenue) }}</div>
        </div>
    </div>
</div>

<div class="form-section">
    <h5 class="mb-4">Tenants by Property</h5>
    <table class="table table-hover align-middle">
        <thead>
            <tr>
                <th>Name / Business</th>
                <th>Property</th>
                <th>Monthly Dues</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for t in tenants %}
            <tr>
                <td><strong>{{ t.name }}</strong><br><small class="text-muted">{{ t.bus_name }}</small></td>
                <td>{{ t.property_name }}</td>
                <td>₱ {{ "{:,.2f}".format(t.total_rent) }}</td>
                <td><span class="badge bg-success-subtle text-success px-3">Active</span></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
"""

@app.route('/')
def index():
    return render_template_string(LAYOUT.replace("{% block content %}{% endblock %}", INDEX_HTML), page='register')

@app.route('/dashboard')
def dashboard():
    tenants = Tenant.query.all()
    total_rev = sum(t.total_rent for t in tenants)
    return render_template_string(LAYOUT.replace("{% block content %}{% endblock %}", DASHBOARD_HTML), page='dashboard', tenants=tenants, total_revenue=total_rev)

@app.route('/submit', methods=['POST'])
def submit():
    basic = float(request.form.get('basic_rent', 0))
    total = (basic + (basic * 0.12)) - (basic * 0.05)
    new_tenant = Tenant(
        name=request.form.get('name'), bus_name=request.form.get('bus_name'),
        property_name=request.form.get('property'), father_name=request.form.get('father_name'),
        f_health=request.form.get('f_health'), basic_rent=basic, total_rent=total
    )
    db.session.add(new_tenant)
    db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
