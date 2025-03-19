# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 또는 'a_very_secret_key_that_is_hard_to_guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(80), nullable=False)  # 'admin', 'customer', or 'superadmin'

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

@app.route('/')
def home():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if user.role == 'admin' or user.role == 'superadmin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        session['username'] = user.username
        session['role'] = user.role
        if user.role == 'admin' or user.role == 'superadmin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))
    return 'Invalid credentials'

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            return 'Username already exists'
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/admin')
def admin_dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    if user.role != 'admin' and user.role != 'superadmin':
        return redirect(url_for('home'))
    items = Item.query.all()
    return render_template('admin_dashboard.html', items=items)

@app.route('/admin/add_item', methods=['POST'])
def add_item():
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    if user.role != 'admin' and user.role != 'superadmin':
        return redirect(url_for('home'))
    name = request.form['name']
    quantity = request.form['quantity']
    item = Item(name=name, quantity=quantity)
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_item/<int:item_id>', methods=['POST'])
def update_item(item_id):
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    if user.role != 'admin' and user.role != 'superadmin':
        return redirect(url_for('home'))
    item = Item.query.get(item_id)
    item.name = request.form['name']
    item.quantity = request.form['quantity']
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_item/<int:item_id>')
def delete_item(item_id):
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    if user.role != 'admin' and user.role != 'superadmin':
        return redirect(url_for('home'))
    item = Item.query.get(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users')
def admin_users():
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    if user.role != 'admin' and user.role != 'superadmin':
        return redirect(url_for('home'))
    admins = User.query.filter_by(role='admin').all()
    customers = User.query.filter_by(role='customer').all()
    superadmins = User.query.filter_by(role='superadmin').all()
    return render_template('admin_users.html', admins=admins, customers=customers, superadmins=superadmins)

@app.route('/admin/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    if user.role != 'admin' and user.role != 'superadmin':
        return redirect(url_for('home'))
    user_to_update = User.query.get(user_id)
    if user_to_update.role == 'superadmin':
        return redirect(url_for('admin_users'))
    user_to_update.username = request.form['username']
    user_to_update.password = request.form['password']
    user_to_update.role = request.form['role']
    db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    if user.role != 'admin' and user.role != 'superadmin':
        return redirect(url_for('home'))
    user_to_delete = User.query.get(user_id)
    if user_to_delete.role == 'superadmin':
        return redirect(url_for('admin_users'))
    db.session.delete(user_to_delete)
    db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/customer')
def customer_dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    user = User.query.filter_by(username=session['username']).first()
    if user.role != 'customer':
        return redirect(url_for('home'))
    items = Item.query.all()
    return render_template('customer_dashboard.html', items=items)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create superadmin if not exists
        if not User.query.filter_by(username='root').first():
            superadmin = User(username='root', password='1234', role='superadmin')
            db.session.add(superadmin)
            db.session.commit()
    app.run(debug=True)