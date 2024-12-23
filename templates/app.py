from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from passlib.hash import sha256_crypt
from bson import ObjectId

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key_here'

# MongoDB connection setup
client = MongoClient("127.0.0.1:27017")  # Use your MongoDB URI
db = client['products']  # Database name
users_collection = db['user']  # Collection for user data
details_collection = db['product_details'] 

# Home route
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/loginpage')
def loginpage():
    return render_template('login.html')

@app.route('/signuppage')
def signuppage():
    return render_template('signup.html')

@app.route('/addproductpage')
def addproductpage():
    return render_template('addproduct.html')

@app.route('/dashboardpage')
def dashboardpage():
    return render_template('dashboard.html')

@app.route('/productspage')
def productspage():
    return render_template('products.html')

# Register route (for simplicity)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']

        # Hash the password
        hashed_password = sha256_crypt.hash(password)

        # Store user in MongoDB
        users_collection.insert_one({'first_name':first_name ,'last_name':last_name ,'email': email, 'password': hashed_password})

        flash("Registration Successful!", "success")
        return redirect(url_for('loginpage'))

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET','POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    # Check if user exists
    email = users_collection.find_one({'email': email})
    
    if email and sha256_crypt.verify(password, email['password']):
        flash("Login Successful!", "success")
        return redirect(url_for('products'))
    else:
        flash("Invalid Username or Password!", "danger")
        return redirect(url_for('home'))

@app.route('/addproduct', methods=['POST'])
def addproduct():
    if request.method == 'POST':
        product_name=request.form['product_name']
        category=request.form['category']
        quantity = request.form['quantity']
        price = request.form['price']

        details_collection.insert_one({'product_name':product_name ,'category':category ,'quantity':quantity, 'price': price})
        
        return redirect(url_for('products'))

@app.route('/dashboard')
def dashboard():
    products = details_collection.find()
    products_list = list(products)
    return render_template('dashboard.html', products=products_list)

@app.route('/products')
def products():
    products = details_collection.find()
    return render_template('products.html', products=products)

@app.route('/productdetails')
def productdetails():
    product_name = request.args.get("product_name")
    product = details_collection.find_one({"product_name": product_name})

    if product:
        return render_template("productdetails.html", product=product)

@app.route('/updateproduct', methods=['GET', 'POST'])
def update_product():
    if request.method == 'GET':
        product_name = request.args.get("product_name")
        if not product_name:
            return "Product name is required!", 400
        
        # Find the product by product_name
        product = details_collection.find_one({"product_name": product_name})
        if not product:
            return "Product not found", 404

        return render_template("updateproduct.html", product=product)

    if request.method == 'POST':
        product_name = request.form.get("product_name")
        field = request.form.get("field")
        new_value = request.form.get("new_value")

        if field == "category":
            try:
                new_value = str(new_value)
            except ValueError:
                return "Category should be a valid string", 400
        
        # Convert price to float and quantity to integer if necessary
        if field == "price":
            try:
                new_value = float(new_value)
            except ValueError:
                return "Price should be a valid number", 400
        elif field == "quantity":
            try:
                new_value = int(new_value)
            except ValueError:
                return "Quantity should be a valid integer", 400

        # Update the product by product_name
        result = details_collection.update_one(
            {"product_name": product_name},
            {"$set": {field: new_value}}
        )

        if result.matched_count > 0:
            return redirect(f"/productdetails?product_name={product_name}")
        else:
            return "Product not found", 404

@app.route('/deleteproduct', methods=['POST'])
def delete_product():
    product_name = request.form.get("product_name")
    
    # Find the product by product_name and delete it
    result = details_collection.delete_one({"product_name": product_name})

    if result.deleted_count > 0:
        return redirect("/products")  # Redirect to the products list page
    else:
        return "Product not found", 404

if __name__== '__main__':
    app.run(debug=True)
