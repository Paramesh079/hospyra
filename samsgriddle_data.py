import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "1122"
}

menu_data = [
     # 🟢 VEGETARIAN
    ("Vegetarian","Jalapeno Cheese Soup",199),
    ("Vegetarian","Tomato Basil Herb Soup",159),
    ("Vegetarian","Broccoli Almond Soup",199),
    ("Vegetarian","Cream of Mushroom Soup",199),
    ("Vegetarian","French Onion Soup",199),
    ("Vegetarian","Garden Veg Soup",199),
    ("Vegetarian","Broccoli Cheddar Cheese Soup",299),
    ("Vegetarian","Potato & Leek Soup",249),
    ("Vegetarian","Mexican Chilly Bean Soup (Veg)",196),
    ("Vegetarian","Mexican Tortilla Soup",196),
    ("Vegetarian","Beijing Manchow Soup (Veg)",175),
    ("Vegetarian","Hot & Sour Soup (Veg)",179),
    ("Vegetarian","Thai Coconut Soup (Veg)",239),
    ("Vegetarian","Lemon Coriander Soup (Veg)",175),
    ("Vegetarian","Sweet Corn Soup (Veg)",179),
    ("Vegetarian","Clear Soup (Veg)",149),
    ("Vegetarian","Fattoush Salad",329),
    ("Vegetarian","Caesar Salad (Veg)",319),
    ("Vegetarian","Green Salad with Italian Dressing",299),
    ("Vegetarian","Mexican Tortilla Salad",299),
    ("Vegetarian","Green Salad",180),
    ("Vegetarian","Mezze Platter",419),
    ("Vegetarian","Hummus with Falafel Tikki",390),
    ("Vegetarian","Hummus with Sautéed Mushroom",410),
    ("Vegetarian","Cottage Cheese Pesto",349),
    ("Vegetarian","Spicy Cheese Spinach Balls",349),
    ("Vegetarian","Focaccia Bruschetta",319),
    ("Vegetarian","Sautéed Mushroom with Garlic",419),
    ("Vegetarian","Cheese Fondue",479),
    ("Vegetarian","French Fries",208),
    ("Vegetarian","Garlic Bread",155),
    ("Vegetarian","Cheese Garlic Bread",239),
    ("Vegetarian","Paneer Tikka",369),
    ("Vegetarian","Bhara Bhara Cheese Kebab",329),
    ("Vegetarian","Nachos with Cheese Sauce",329),
    ("Vegetarian","Nachos Grande (Veg)",339),
    ("Vegetarian","Cheese Quesadillas (Veg)",339),
    ("Vegetarian","Mexican Croquettes (Veg)",339),
    ("Vegetarian","Crispy Paneer",349),
    ("Vegetarian","Baby Corn Chilli / Crispy",339),
    ("Vegetarian","Paneer Butter Masala",349),
    ("Vegetarian","Shahi Paneer",349),
    ("Vegetarian","Kadai Vegetables",329),
    ("Vegetarian","Veg Kolhapuri",309),
    ("Vegetarian","Alfredo Pasta (Veg)",449),
    ("Vegetarian","Spaghetti Aglio Olio Veg",429),
    ("Vegetarian","Margherita Pizza",419),
    ("Vegetarian","Gulab Jamun with Vanilla Ice Cream",174),
    ("Vegetarian","Sizzling Brownie",329),

    # 🌱 VEGAN
    ("Vegan","Garden Veg Soup",199),
    ("Vegan","Clear Soup (Veg)",149),
    ("Vegan","Lemon Coriander Soup (Veg)",175),
    ("Vegan","Water Chestnuts in Plum Sauce",429),
    ("Vegan","Crispy Vegetables Salt & Pepper",329),
    ("Vegan","Crispy Corn Salt & Pepper",319),
    ("Vegan","Crispy Chilli Potato",319),
    ("Vegan","Chilli Mushroom",339),

    # 🔴 NON-VEGETARIAN
    ("Non-Vegetarian","Cream of Chicken Soup",209),
    ("Non-Vegetarian","Mexican Chilly Bean Soup (Non-Veg)",233),
    ("Non-Vegetarian","Beijing Manchow Soup (Non-Veg)",199),
    ("Non-Vegetarian","Hot & Sour Soup (Non-Veg)",199),
    ("Non-Vegetarian","Thai Coconut Soup (Chicken)",289),
    ("Non-Vegetarian","Thai Coconut Soup (Seafood)",299),
    ("Non-Vegetarian","Tom Yum Chicken Soup",199),
    ("Non-Vegetarian","Chicken Tikka",379),
    ("Non-Vegetarian","Kalmi Kebab",429),
    ("Non-Vegetarian","Chicken Seekh Kebab",449),
    ("Non-Vegetarian","Chicken Angara Kebab",449),
    ("Non-Vegetarian","Chilli Chicken",379),
    ("Non-Vegetarian","Chicken Manchurian",379),
    ("Non-Vegetarian","BBQ Chicken Wings",369),
    ("Non-Vegetarian","Apollo Fish",379),
    ("Non-Vegetarian","Murgh Makhani",379),
    ("Non-Vegetarian","Chicken Lababdar",379),
    ("Non-Vegetarian","Chicken Mughlai",429),
    ("Non-Vegetarian","Mutton Rogan Josh",499),
    ("Non-Vegetarian","Chicken Dum Biryani",359),
    ("Non-Vegetarian","Mutton Biryani",469),
    ("Non-Vegetarian","Grilled Chicken Pizza",549),
    ("Non-Vegetarian","BBQ Chicken Pizza",549),
    ("Non-Vegetarian","Chicken Steak Sizzler",579),
    ("Non-Vegetarian","Sea Food Sizzler",679),

    # 🥤 BEVERAGES
    ("Beverage","Cinderella",209),
    ("Beverage","Caribbean Exotic",209),
    ("Beverage","Green Temptation",209),
    ("Beverage","Guava Punch",209),
    ("Beverage","Pina Colada",209),
    ("Beverage","Ginger Ale",209),
    ("Beverage","Sam’s Griddle Special Mocktail",229),
    ("Beverage","Cold Coffee",159),
    ("Beverage","Fresh Lime Soda",79),
    ("Beverage","Butter Milk",60),
    ("Beverage","Lassi (Mango)",119),
]

# ----------------- Intelligence Functions -----------------

def infer_taste(name, category):
    name = name.lower()
    if any(k in name for k in ["chilli", "spicy", "tikka", "kebab", "masala", "biryani", "bbq"]):
        return "Spicy"
    if any(k in name for k in ["sweet", "brownie", "gulab", "coffee", "lassi", "mocktail"]):
        return "Sweet"
    if any(k in name for k in ["soup", "salad", "clear"]):
        return "Mild"
    if any(k in name for k in ["cheese", "butter", "cream", "paneer"]):
        return "Savory"
    if category == "Beverage":
        return "Sweet"
    return "Mild"


def infer_quantity(name, category):
    name = name.lower()
    if any(k in name for k in ["soup", "salad", "coffee", "lassi", "mocktail"]):
        return "Light"
    if any(k in name for k in ["starter", "pizza", "pasta"]):
        return "Medium"
    if any(k in name for k in ["biryani", "masala", "sizzler"]):
        return "Heavy"
    if category == "Beverage":
        return "Light"
    return "Medium"


def infer_special(name, price, category):
    name = name.lower()
    if "special" in name or "sizzler" in name or "biryani" in name:
        return "Chef Special"
    if price >= 500:
        return "Premium"
    if category == "Beverage":
        return "Refreshing"
    if any(k in name for k in ["brownie", "gulab", "dessert"]):
        return "Bestseller"
    return "Regular"

# ----------------- MAIN -----------------

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS samsgriddle_menu;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS samsgriddle_menu (
            id SERIAL PRIMARY KEY,
            item_category VARCHAR(20),
            item_name TEXT,
            item_price INTEGER,
            item_taste VARCHAR(20),
            item_quantity VARCHAR(20),
            item_special VARCHAR(50),
            customer_id INTEGER,
            customer_preference VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    enriched_data = []
    for i, (category, name, price) in enumerate(menu_data):
        # Sequential customer ID starting from 1
        cust_id = i + 1
        
        # Inferred taste for the preference
        taste = infer_taste(name, category)
        
        # Preference based on category and taste as requested
        cust_pref = f"Prefers {category} items with {taste} taste"

        enriched_data.append((
            category,
            name,
            price,
            taste,
            infer_quantity(name, category),
            infer_special(name, price, category),
            cust_id,
            cust_pref
        ))

    cur.executemany("""
        INSERT INTO samsgriddle_menu
        (item_category, item_name, item_price, item_taste, item_quantity, item_special, customer_id, customer_preference)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """, enriched_data)

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Inserted {len(enriched_data)} intelligent rows")

if __name__ == "__main__":
    main()
