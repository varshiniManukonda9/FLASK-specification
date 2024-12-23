from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pymongo import MongoClient
from passlib.hash import sha256_crypt
from bson import ObjectId

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key_here'

# MongoDB connection setup
client = MongoClient("127.0.0.1:27017")  # MongoDB URI
db = client['products']  # Database name
users_collection = db['user']  # User data collection
details_collection = db['product_details']  # Product details collection
favorites_collection = db['favorites']  # Favorites collection

# ---------- Helper Functions ----------

def get_product(product_name):
    """Fetch a product by name."""
    return details_collection.find_one({"product_name": product_name})

def get_all_products():
    """Fetch all products."""
    return list(details_collection.find())


def get_favorites():
    """Fetch all favorite products with full details."""
    # Get all product IDs from the favorites collection
    favorite_ids = favorites_collection.find({}, {"product_id": 1, "_id": 0})
    product_ids = [fav['product_id'] for fav in favorite_ids]
    
    # Fetch product details for the IDs in the favorites collection
    return list(details_collection.find({"_id": {"$in": product_ids}}))





# ---------- Routes ----------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/loginpage')
def loginpage():
    return render_template('login.html')

@app.route('/signuppage')
def signuppage():
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    products = get_all_products()
    favorites = get_favorites()  # Get full product details for favorites
    favorite_ids = [fav['product_id'] for fav in favorites_collection.find()]
    return render_template('dashboard.html', products=products, favorite_ids=favorite_ids)

@app.route('/favorites')
def favorites():
    favorites = get_favorites()  # Ensure this function is defined above the route handler
    return render_template('favorites.html', favorites=favorites)


@app.route('/register', methods=['POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']

        # Check if email already exists
        if users_collection.find_one({'email': email}):
            flash("Email already registered!", "danger")
            return redirect(url_for('signuppage'))

        # Hash the password and save the user
        hashed_password = sha256_crypt.hash(password)
        users_collection.insert_one({'first_name': first_name, 'last_name': last_name, 'email': email, 'password': hashed_password})

        flash("Registration Successful!", "success")
        return redirect(url_for('loginpage'))

@app.route('/login', methods=['POST'])
def login():
    """User login."""
    email = request.form['email']
    password = request.form['password']

    # Find the user by email
    user = users_collection.find_one({'email': email})
    if user and sha256_crypt.verify(password, user['password']):
        flash("Login Successful!", "success")
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid Email or Password!", "danger")
        return redirect(url_for('loginpage'))

@app.route('/addproduct', methods=['POST'])
def addproduct():
    """Add a new product."""
    if request.method == 'POST':
        product_name = request.form['product_name']
        category = request.form['category']
        quantity = request.form['quantity']
        price = request.form['price']

        # Insert the product into the database
        details_collection.insert_one({'product_name': product_name, 'category': category, 'quantity': int(quantity), 'price': float(price)})
        flash("Product added successfully!", "success")
        return redirect(url_for('dashboard'))


@app.route('/updateproduct', methods=['GET', 'POST'])
def update_product():
    """Update an existing product."""
    if request.method == 'GET':
        product_name = request.args.get("product_name")
        product = get_product(product_name)
        if not product:
            flash("Product not found!", "danger")
            return redirect(url_for('dashboard'))
        return render_template("updateproduct.html", product=product)

    if request.method == 'POST':
        product_name = request.form.get("product_name")
        field = request.form.get("field")
        new_value = request.form.get("new_value")

        # Validate input
        if field == "quantity":
            new_value = int(new_value)
        elif field == "price":
            new_value = float(new_value)

        # Update the product
        result = details_collection.update_one({"product_name": product_name}, {"$set": {field: new_value}})
        if result.matched_count:
            flash("Product updated successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Product not found!", "danger")
            return redirect(url_for('dashboard'))

@app.route('/deleteproduct', methods=['POST'])
def delete_product():
    """Delete a product."""
    product_name = request.form.get("product_name")
    result = details_collection.delete_one({"product_name": product_name})

    if result.deleted_count > 0:
        flash("Product deleted successfully!", "success")
    else:
        flash("Product not found!", "danger")
    return redirect(url_for('dashboard'))

@app.route('/productdetails')
def productdetails():
    """View product details."""
    product_name = request.args.get("product_name")
    product = get_product(product_name)
    if product:
        return render_template("productdetails.html", product=product)
    else:
        flash("Product not found!", "danger")
        return redirect(url_for('dashboard'))

# ---------- Main ----------
if __name__ == '__main__':
    app.run(debug=True)
