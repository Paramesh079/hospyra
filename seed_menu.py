import psycopg2
import random
from faker import Faker

# -----------------------------
# DB CONFIG (CHANGE IF NEEDED)
# -----------------------------
DB_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "1122",
    "port": 5432
}

fake = Faker()

CATEGORIES = ["Veg", "Non-Veg", "Beverages"]

FOOD_ITEMS = {
    "Veg": [
        "Veg Burger", "Paneer Pizza", "Veg Biryani",
        "Veg Sandwich", "Paneer Tikka", "Veg Pasta"
    ],
    "Non-Veg": [
        "Chicken Burger", "Chicken Pizza", "Chicken Biryani",
        "Mutton Curry", "Fish Fry", "Chicken Pasta"
    ],
    "Beverages": [
        "Coca Cola", "Orange Juice", "Cold Coffee",
        "Lemonade", "Milk Shake", "Green Tea"
    ]
}

# -----------------------------
# CONNECT TO POSTGRES
# -----------------------------
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# -----------------------------
# CREATE TABLE
# -----------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS menu (
    itemid INT PRIMARY KEY,
    item TEXT NOT NULL,
    restaurant TEXT NOT NULL,
    category TEXT NOT NULL,
    price NUMERIC NOT NULL
);
""")

conn.commit()

# -----------------------------
# GENERATE & INSERT DATA
# -----------------------------
records = []

for itemid in range(1, 1001):
    category = random.choice(CATEGORIES)
    item = random.choice(FOOD_ITEMS[category])
    restaurant = fake.company()
    price = round(random.uniform(50, 500), 2)

    records.append((itemid, item, restaurant, category, price))

insert_query = """
INSERT INTO menu (itemid, item, restaurant, category, price)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (itemid) DO NOTHING;
"""

cur.executemany(insert_query, records)
conn.commit()

print("✅ 1000 menu records inserted successfully")

# -----------------------------
# CLEANUP
# -----------------------------
cur.close()
conn.close()
