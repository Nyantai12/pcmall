from flask import Flask, flash, render_template, request, redirect, url_for, session, g
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"
DB_NAME = "pcmall.db"

# --------------------------
# DB connection
# --------------------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_NAME)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --------------------------
# Home page
# --------------------------
@app.route('/')
def index():
    con = get_db()
    products = con.execute("""
        SELECT product.id, product.name, product.price,
               category.name as category, brand.name as brand, supplier.name as supplier
        FROM product
        LEFT JOIN category ON product.category_id = category.id
        LEFT JOIN brand ON product.brand_id = brand.id
        LEFT JOIN supplier ON product.supplier_id = supplier.id
    """).fetchall()
    return render_template("index.html", products=products)

# --------------------------
# Add product
# --------------------------
@app.route('/add', methods=['GET','POST'])
def add():
    con = get_db()
    categories = con.execute("SELECT * FROM category").fetchall()
    brands = con.execute("SELECT * FROM brand").fetchall()
    suppliers = con.execute("SELECT * FROM supplier").fetchall()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category_id = request.form['category']
        brand_id = request.form['brand']
        supplier_id = request.form['supplier']

        con.execute("""
            INSERT INTO product
            (name, price, category_id, brand_id, supplier_id)
            VALUES (?,?,?,?,?)
        """, (name, price, category_id, brand_id, supplier_id))
        con.commit()
        return redirect(url_for('index'))

    return render_template('add.html', categories=categories, brands=brands, suppliers=suppliers)

# --------------------------
# Edit product
# --------------------------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    con = get_db()
    product = con.execute("SELECT * FROM product WHERE id=?", (id,)).fetchone()
    categories = con.execute("SELECT * FROM category").fetchall()
    brands = con.execute("SELECT * FROM brand").fetchall()
    suppliers = con.execute("SELECT * FROM supplier").fetchall()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category_id = request.form['category']
        brand_id = request.form['brand']
        supplier_id = request.form['supplier']

        con.execute("""
            UPDATE product SET name=?, price=?, category_id=?, brand_id=?, supplier_id=?
            WHERE id=?
        """, (name, price, category_id, brand_id, supplier_id, id))
        con.commit()
        return redirect(url_for('index'))

    return render_template('edit.html', product=product, categories=categories, brands=brands, suppliers=suppliers)



@app.route('/delete/<int:id>')
def delete(id):
    con = get_db()
    con.execute("DELETE FROM product WHERE id=?", (id,))
    con.commit()
    return redirect(url_for('index'))


@app.route("/add_to_cart/<int:id>")
def add_to_cart(id):
    if "cart" not in session:
        session["cart"] = []
    session["cart"].append(id)
    session.modified = True
    return """ <script>
        alert("Бараа сагсанд амжилттай нэмэгдлээ!");
        window.history.back();  // Өмнөх page буюу index.html рүү буцах
    </script>
    """

@app.route("/cart")
def cart():
    con = get_db()
    cart_items = []
    total = 0
    for pid in session.get("cart", []):
        item = con.execute("SELECT id, name, price FROM product WHERE id=?", (pid,)).fetchone()
        if item:
            cart_items.append({"id": item[0], "name": item[1], "price": item[2]})
            total += item[2]
    con.close()
    return render_template("cart.html", cart_items=cart_items, total=total)


@app.route("/checkout")
def checkout():
    con = get_db()
    cur = con.execute("INSERT INTO orders(order_date) VALUES (datetime('now'))")
    order_id = cur.lastrowid
    for pid in session.get("cart", []):
        con.execute("INSERT INTO order_item(order_id, product_id, qty) VALUES (?,?,?)",
                    (order_id, pid, 1))

    con.commit()
    con.close()
    session["cart"] = []  
     # Alert харуулж, index.html рүү шилжүүлэх
    return """
    <script>
        alert("Захиалга амжилттай үүслээ!");
        window.location.href = "/";
    </script>
    """



def init_db():
    con = get_db()
    # ангилал хүснэгт
    con.execute("""CREATE TABLE IF NOT EXISTS category(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)""")
    # брэнд хүснэгт
    con.execute("""CREATE TABLE IF NOT EXISTS brand(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)""")
    # нийлүүлэгч хүснэгт
    con.execute("""CREATE TABLE IF NOT EXISTS supplier(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT)""")
    # Захиалга хүснэгт
    con.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_date TEXT
    )
    """)

    # Захиалгын бараа хүснэгт
    con.execute("""
    CREATE TABLE IF NOT EXISTS order_item(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        qty INTEGER,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES product(id)
    )
    """)
    #бараа хүснэгт
    con.execute("""CREATE TABLE IF NOT EXISTS product(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price INTEGER,
    category_id INTEGER,
    brand_id INTEGER,
    supplier_id INTEGER,
    FOREIGN KEY(category_id) REFERENCES category(id),
    FOREIGN KEY(brand_id) REFERENCES brand(id),
    FOREIGN KEY(supplier_id) REFERENCES supplier(id)
    )""")

    con.commit()
    if con.execute("SELECT COUNT(*) FROM category").fetchone()[0] == 0:
        con.execute("INSERT INTO category(name) VALUES ('Laptop'), ('Keyboard'), ('Mouse'),('Headset')")
    if con.execute("SELECT COUNT(*) FROM brand").fetchone()[0] == 0:
        con.execute("INSERT INTO brand(name) VALUES ('Dell'), ('HP'), ('Logitech'), ('Asus'), ('Acer'), ('Razer')")
    if con.execute("SELECT COUNT(*) FROM supplier").fetchone()[0] == 0:
        con.execute("INSERT INTO supplier(name, phone) VALUES ('PC Import', '99112233'), ('Tech World', '99887766'), ('Dell Distribution', '88776655')")
    con.commit()

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
