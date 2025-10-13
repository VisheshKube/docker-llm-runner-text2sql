import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "data/demo.db"

def initialize_db() -> None:
    """
    Reset database schema and insert demo data.
    - Drops old tables (customers, products, orders)
    - Creates new schema
    - Seeds with ~30 sample records each
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Drop old tables if they exist
    for t in ["customers", "products", "orders"]:
        cur.execute(f"DROP TABLE IF EXISTS {t}")

    # Create tables
    cur.execute("""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        city TEXT,
        join_date TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        category TEXT,
        price REAL
    )
    """)

    cur.execute("""
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        order_date TEXT,
        total REAL,
        FOREIGN KEY(customer_id) REFERENCES customers(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)
    # Seed with demo data
    random.seed(42)

    # Customers (30 records)
    cities = [
        "New York", "San Francisco", "Chicago", "Boston", "Los Angeles",
        "Houston", "Seattle", "Denver", "Miami", "Dallas",
        "Atlanta", "Newark", "Phoenix", "Philadelphia", "Detroit"
    ]
    customers = []
    for i in range(30):
        name = f"Customer_{i+1}"
        city = random.choice(cities)
        join_date = (
            datetime(2018, 1, 1) + timedelta(days=random.randint(0, 2000))
        ).strftime("%Y-%m-%d")
        customers.append((name, city, join_date))
    cur.executemany("INSERT INTO customers (name, city, join_date) VALUES (?, ?, ?)", customers)

    # Products (30 records)
    categories = ["Electronics", "Furniture", "Accessories", "Appliances", "Office"]
    product_names = [f"Product_{i+1}" for i in range(30)]
    products = [
        (name, random.choice(categories), round(random.uniform(50, 2000), 2))
        for name in product_names
    ]
    cur.executemany("INSERT INTO products (name, category, price) VALUES (?, ?, ?)", products)

    # Orders (30+ records)
    orders = []
    for i in range(30):
        cust_id = random.randint(1, 30)
        prod_id = random.randint(1, 30)
        qty = random.randint(1, 5)
        order_date = (
            datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))
        ).strftime("%Y-%m-%d")
        price = products[prod_id - 1][2]
        total = qty * price
        orders.append((cust_id, prod_id, qty, order_date, total))
    cur.executemany(
        "INSERT INTO orders (customer_id, product_id, quantity, order_date, total) VALUES (?, ?, ?, ?, ?)",
        orders
    )

    # Commit and close
    conn.commit()
    conn.close()
    #print(" Database initialized with 30+ records per table.")


if __name__ == "__main__":
    initialize_db()
