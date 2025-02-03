from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
import shortuuid
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
database_url = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    custom_link = db.Column(db.String(200), unique=True, nullable=False)
    views = db.Column(db.Integer, default=0)
    submissions = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.Index('idx_custom_link', 'custom_link'),
        db.Index('idx_email_phone', 'email', 'phone')
    )

# Main Application Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        # Validation
        if not all([name, email, phone]):
            flash("All fields are required!", "danger")
            return redirect(url_for('home'))
            
        if len(phone) not in [11, 12] or not phone.isdigit():
            flash("Phone number must be 11-12 digits!", "danger")
            return redirect(url_for('home'))

        # Check existing user
        user = User.query.filter((User.email == email) | (User.phone == phone)).first()
        if user:
            flash("You already have a custom link!", "info")
            return render_template_string(existing_user_page, link=user.custom_link)

        # Create new user with dynamic URL
        unique_id = shortuuid.uuid()[:8]
        custom_link = f"{request.host_url}{unique_id}"
        new_user = User(name=name, email=email, phone=phone, custom_link=custom_link)
        
        # Handle referrals
        referral_id = session.get('referral_id')
        if referral_id:
            referrer = User.query.filter_by(custom_link=f"{request.host_url}{referral_id}").first()
            if referrer:
                referrer.submissions += 1
                session.pop('referral_id', None)
        
        db.session.add(new_user)
        db.session.commit()
        
        return render_template_string(new_user_page, link=custom_link)

    return render_template_string(home_page, csrf_token=generate_csrf())

@app.route('/<unique_id>')
def handle_custom_link(unique_id):
    user = User.query.filter_by(custom_link=f"{request.host_url}{unique_id}").first()
    if not user:
        return "Invalid Link", 404

    user.views += 1
    db.session.commit()
    session['referral_id'] = unique_id
    return redirect(url_for('home'))
# Admin Routes
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if not validate_csrf(request.form.get('csrf_token')):
            flash("Security token invalid. Please try again.", "danger")
            return redirect(url_for('admin'))
            
        password = request.form.get('password', '')
        if password == 'nigniga99':
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
            
        flash("Invalid password!", "danger")
        return redirect(url_for('admin'))

    if 'admin_logged_in' in session:
        return redirect(url_for('dashboard'))

    return render_template_string(admin_login_page, csrf_token=generate_csrf())

@app.route('/dashboard')
def dashboard():
    if 'admin_logged_in' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('admin'))
    
    users = User.query.all()
    return render_template_string(admin_dashboard_page, 
                               users=users,
                               csrf_token=generate_csrf())

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not validate_csrf(request.form.get('csrf_token')):
        flash("Security token invalid!", "danger")
        return redirect(url_for('dashboard'))
    
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully!", "success")
    else:
        flash("User not found!", "danger")

    return redirect(url_for('dashboard'))

@app.route('/clear_database', methods=['POST'])
def clear_database():
    if not validate_csrf(request.form.get('csrf_token')):
        flash("Security token invalid!", "danger")
        return redirect(url_for('dashboard'))
    
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))

    db.session.query(User).delete()
    db.session.commit()
    flash("Database cleared successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/logout', methods=['POST'])
def logout():
    if not validate_csrf(request.form.get('csrf_token')):
        flash("Security token invalid!", "danger")
        return redirect(url_for('admin'))
    
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin'))

# Helper Functions
def validate_csrf(token):
    try:
        csrf.protect()
        return True
    except:
        return False

# HTML Templates
home_page = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Join Giveaway</title>
    <style>
        :root { --primary: #66fcf1; --secondary: #45a29e; }
        body { font-family: 'Arial', sans-serif; background: #1a1a1d; color: #c5c6c7; margin: 0; padding: 20px; }
        .container { background: #4e4e50; border-radius: 8px; padding: 2rem; width: 90%; max-width: 400px; margin: 1rem auto; }
        input, button { width: 100%; padding: 0.8rem; margin: 0.5rem 0; border-radius: 5px; border: none; box-sizing: border-box; }
        button { background: var(--primary); color: #1a1a1d; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background: var(--secondary); }
        .flash { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .flash-success { background: #4CAF50; color: white; }
        .flash-danger { background: #f44336; color: white; }
        @media (max-width: 480px) { .container { padding: 1.5rem; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Join the Giveaway</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <input type="text" name="name" placeholder="Your Name" required>
            <input type="email" name="email" placeholder="your@email.com" required>
            <input type="tel" name="phone" placeholder="11-12 Digit Number" 
                   pattern="[0-9]{11,12}" title="11 or 12 digit number" required>
            <button type="submit">Get Your Link</button>
        </form>
    </div>
</body>
</html>
"""

new_user_page = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thank You</title>
    <style>
        body { font-family: 'Arial', sans-serif; background: #1a1a1d; color: #c5c6c7; margin: 0; padding: 20px; }
        .container { background: #4e4e50; border-radius: 8px; padding: 2rem; width: 90%; max-width: 400px; margin: 1rem auto; }
        .link-box { display: flex; gap: 0.5rem; margin: 1.5rem 0; }
        input { flex: 1; border: none; background: #66fcf1; color: #1a1a1d; padding: 0.8rem; border-radius: 5px; }
        button { background: #45a29e; color: white; padding: 0.8rem 1.5rem; border-radius: 5px; cursor: pointer; }
        .whatsapp-btn { background: #25D366; margin-top: 1rem; width: 100%; }
        @media (max-width: 480px) { .link-box { flex-direction: column; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Thank You! 🎉</h1>
        <p>Your custom link:</p>
        <div class="link-box">
            <input type="text" id="customLink" value="{{ link }}" readonly>
            <button onclick="copyLink()">Copy</button>
        </div>
        <button class="whatsapp-btn" onclick="shareOnWhatsApp('{{ link }}')">
            Share via WhatsApp
        </button>
    </div>
    <script>
        function copyLink() {
            const link = document.getElementById('customLink');
            link.select();
            navigator.clipboard.writeText(link.value);
            alert('Link copied to clipboard!');
        }
        function shareOnWhatsApp(link) {
            const message = `Join using my link: ${link}`;
            window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, '_blank');
        }
    </script>
</body>
</html>
"""

admin_login_page = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login</title>
    <style>
        body { font-family: 'Arial', sans-serif; background: #1a1a1d; color: #c5c6c7; margin: 0; padding: 20px; }
        .container { background: #4e4e50; border-radius: 8px; padding: 2rem; width: 90%; max-width: 400px; margin: 1rem auto; }
        input, button { width: 100%; padding: 0.8rem; margin: 0.5rem 0; border-radius: 5px; border: none; }
        button { background: #66fcf1; color: #1a1a1d; font-weight: bold; cursor: pointer; }
        .flash { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .flash-danger { background: #f44336; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Admin Login</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <input type="password" name="password" placeholder="Enter password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""

admin_dashboard_page = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard</title>
    <style>
        body { font-family: 'Arial', sans-serif; background: #1a1a1d; color: #c5c6c7; margin: 0; padding: 20px; }
        .container { background: #4e4e50; border-radius: 8px; padding: 2rem; margin: 1rem auto; max-width: 1000px; }
        table { width: 100%; margin-top: 1rem; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #666; }
        button { padding: 0.5rem 1rem; border-radius: 5px; cursor: pointer; border: none; }
        .danger-btn { background: #ff4444; color: white; }
        .action-group { margin-top: 1rem; display: flex; gap: 0.5rem; }
        .flash { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .flash-success { background: #4CAF50; color: white; }
        .flash-warning { background: #ff9800; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Admin Dashboard</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Views</th>
                    <th>Subs</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for user in users %}
                <tr>
                    <td>{{ user.id }}</td>
                    <td>{{ user.name }}</td>
                    <td>{{ user.email }}</td>
                    <td>{{ user.phone }}</td>
                    <td>{{ user.views }}</td>
                    <td>{{ user.submissions }}</td>
                    <td>
                        <form method="POST" action="{{ url_for('delete_user', user_id=user.id) }}">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                            <button type="submit" class="danger-btn">Delete</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <div class="action-group">
            <form method="POST" action="{{ url_for('clear_database') }}">
                <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                <button type="submit" class="danger-btn">Clear Database</button>
            </form>
            <form method="POST" action="{{ url_for('logout') }}">
                <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                <button type="submit">Logout</button>
            </form>
        </div>
    </div>
</body>
</html>
"""


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))