import psycopg2

# -----------------------------
# DB CONFIG
# -----------------------------
DB_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "1122",
    "port": 5432
}

# -----------------------------
# FIXED MENU (ITEM → PRICE MAP)
# -----------------------------
MENU_ITEMS = [
    # Veg
    ("Veg Burger", "Veg", 120),
    ("Paneer Burger", "Veg", 140),
    ("Aloo Tikki Burger", "Veg", 110),
    ("Cheese Veg Burger", "Veg", 150),
    ("Veg Patty Sandwich", "Veg", 100),
    ("Veg Wrap", "Veg", 130),
    ("Veg Sandwich", "Veg", 100),
    ("Paneer Pizza", "Veg", 220),
    ("Veg Biryani", "Veg", 180),
    ("Paneer Tikka", "Veg", 240),
    ("Veg Pasta", "Veg", 200),

    # Non-Veg
    ("Chicken Burger", "Non-Veg", 180),
    ("Chicken Pizza", "Non-Veg", 260),
    ("Chicken Biryani", "Non-Veg", 230),
    ("Mutton Curry", "Non-Veg", 350),
    ("Fish Fry", "Non-Veg", 300),
    ("Chicken Pasta", "Non-Veg", 280),

    # Beverages
    ("Coca Cola", "Beverages", 80),
    ("Orange Juice", "Beverages", 120),
    ("Cold Coffee", "Beverages", 150),
    ("Lemonade", "Beverages", 70),
    ("Milk Shake", "Beverages", 160),
    ("Green Tea", "Beverages", 90),
]

# -----------------------------
# CONNECT TO POSTGRES
# -----------------------------
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# -----------------------------
# RESET TABLE
# -----------------------------
cur.execute("DROP TABLE IF EXISTS samsgriddle_menu;")

cur.execute("""
CREATE TABLE samsgriddle_menu (
    id SERIAL PRIMARY KEY,
    item TEXT NOT NULL,
    category TEXT NOT NULL,
    price NUMERIC NOT NULL,
    UNIQUE (item)
);
""")

conn.commit()

# -----------------------------
# INSERT FIXED DATA
# -----------------------------
cur.executemany(
    "INSERT INTO samsgriddle_menu (item, category, price) VALUES (%s, %s, %s);",
    MENU_ITEMS
)

conn.commit()

print("✅ Menu table created with FIXED prices per item")

# -----------------------------
# CLEANUP
# -----------------------------
cur.close()
conn.close()
