from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Product(db.Model):
    product_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)

class Location(db.Model):
    location_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)

class ProductMovement(db.Model):
    movement_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String, db.ForeignKey('product.product_id'), nullable=False)
    from_location = db.Column(db.String, db.ForeignKey('location.location_id'), nullable=True)
    to_location = db.Column(db.String, db.ForeignKey('location.location_id'), nullable=True)
    qty = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init-db')
def init_db():
    db.create_all()
    flash('Database Initialized!', 'success')
    return redirect(url_for('index'))

# Product routes
@app.route('/products')
def products():
    items = Product.query.all()
    return render_template('products.html', products=items)

@app.route('/products/add', methods=['GET','POST'])
def add_product():
    if request.method == 'POST':
        p = Product(product_id=request.form['product_id'], name=request.form['name'])
        db.session.add(p)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html')

@app.route('/products/delete/<id>')
def delete_product(id):
    p = Product.query.get(id)
    db.session.delete(p)
    db.session.commit()
    flash('Product deleted!', 'danger')
    return redirect(url_for('products'))

# Location routes
@app.route('/locations')
def locations():
    items = Location.query.all()
    return render_template('locations.html', locations=items)

@app.route('/locations/add', methods=['GET','POST'])
def add_location():
    if request.method == 'POST':
        l = Location(location_id=request.form['location_id'], name=request.form['name'])
        db.session.add(l)
        db.session.commit()
        flash('Location added successfully!', 'success')
        return redirect(url_for('locations'))
    return render_template('location_form.html')

@app.route('/locations/delete/<id>')
def delete_location(id):
    l = Location.query.get(id)
    db.session.delete(l)
    db.session.commit()
    flash('Location deleted!', 'danger')
    return redirect(url_for('locations'))

# Product Movements
@app.route('/movements')
def movements():
    moves = ProductMovement.query.all()
    products = Product.query.all()
    locations = Location.query.all()
    return render_template('movements.html', movements=moves, products=products, locations=locations)

@app.route('/movements/add', methods=['GET','POST'])
def add_movement():
    products = Product.query.all()
    locations = Location.query.all()
    if request.method == 'POST':
        m = ProductMovement(
            product_id=request.form['product_id'],
            from_location=request.form.get('from_location') or None,
            to_location=request.form.get('to_location') or None,
            qty=int(request.form['qty'])
        )
        db.session.add(m)
        db.session.commit()
        flash('Movement recorded!', 'success')
        return redirect(url_for('movements'))
    return render_template('movement_form.html', products=products, locations=locations)

# Report
@app.route('/report')
def report():
    products = Product.query.all()
    locations = Location.query.all()
    moves = ProductMovement.query.all()

    balances = {p.product_id: {l.location_id: 0 for l in locations} for p in products}
    for m in moves:
        if m.to_location:
            balances[m.product_id][m.to_location] += m.qty
        if m.from_location:
            balances[m.product_id][m.from_location] -= m.qty

    rows = []
    for p in products:
        for l in locations:
            qty = balances[p.product_id][l.location_id]
            if qty != 0:
                rows.append({'product': p.name, 'location': l.name, 'qty': qty})

    return render_template('report.html', rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
