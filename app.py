from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Vikash@2004",
    database="local_marketplace"
)
cursor = db.cursor(dictionary=True)

# Home Page
@app.route('/')
def home():
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return render_template('index.html', products=products)

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return "Email already registered. Please login or use a different email."

        cursor.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                       (name, email, password, role))
        db.commit()
        return redirect('/login')
    return render_template('register.html')

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        if user:
            session['user'] = user
            return redirect('/dashboard')
        else:
            return "Invalid credentials"
    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    
    user = session['user']
    
    if user['role'] == 'vendor':
        cursor.execute("SELECT * FROM products WHERE vendor_id = %s", (user['id'],))
        products = cursor.fetchall()
        return render_template('vendor_dashboard.html', user=user, products=products)
    
    else:
        # ✅ Corrected query to fetch price and quantity
        cursor.execute("""
            SELECT p.name, p.price, o.quantity 
            FROM orders o 
            JOIN products p ON o.product_id = p.id 
            WHERE o.user_id = %s
        """, (user['id'],))
        orders = cursor.fetchall()
        return render_template('user_dashboard.html', user=user, orders=orders)

# Add Product (Vendor)
@app.route('/vendor/add-product', methods=['POST'])
def add_product():
    if 'user' in session and session['user']['role'] == 'vendor':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        image_url = request.form['image_url']
        vendor_id = session['user']['id']
        cursor.execute(
            "INSERT INTO products (vendor_id, name, price, description, image_url) VALUES (%s, %s, %s, %s, %s)",
            (vendor_id, name, price, description, image_url)
        )
        db.commit()
    return redirect('/dashboard')

# Place Order (User)
@app.route('/order/<int:product_id>', methods=['POST'])
def order(product_id):
    if 'user' not in session or session['user']['role'] != 'user':
        return redirect('/login')

    user_id = session['user']['id']
    quantity = int(request.form['quantity'])

    cursor.execute("INSERT INTO orders (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                   (user_id, product_id, quantity))
    db.commit()
    return redirect('/dashboard')

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# Show all users (new route)
@app.route('/show_data')
def show_data():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template('show_data.html', users=users)

# Insert Sample Products
def insert_sample_products():
    cursor.execute("SELECT COUNT(*) AS count FROM products")
    count = cursor.fetchone()['count']

    if count == 0:
        print("👉 Inserting sample grocery products...")
        sample_products = [
            (1, "Rice (5kg)", 350.00, "Premium quality basmati rice.", "rice_5kg.jpg"),
            (1, "Toor Dal (1kg)", 120.00, "Best quality yellow split peas.", "toor_dal_1kg.jpg"),
            (1, "Cooking Oil (1L)", 160.00, "Sunflower cooking oil.", "cooking_oil_1l.jpg"),
            (1, "Wheat Flour (5kg)", 200.00, "Freshly milled whole wheat flour.", "wheat_flour_5kg.jpg"),
            (1, "Sugar (1kg)", 55.00, "Clean, white, granulated sugar.", "sugar_1kg.jpg"),
            (1, "Salt (1kg)", 20.00, "Iodized cooking salt.", "salt_1kg.jpg"),
        ]
        cursor.executemany(
            "INSERT INTO products (vendor_id, name, price, description, image_url) VALUES (%s, %s, %s, %s, %s)",
            sample_products
        )
        db.commit()
        print("✅ Sample products added.")
    else:
        print("✅ Products already exist — skipping insert.")

if __name__ == '__main__':
    insert_sample_products()
    app.run(debug=True)
