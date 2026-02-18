from db import engine
from sqlalchemy import text
import json

def get_db_schema():
    """
    Queries information_schema.columns to retrieve the schema for all tables
    in the public schema.
    """
    query = text("""
    SELECT 
        table_name, 
        column_name, 
        data_type, 
        is_nullable, 
        column_default
    FROM 
        information_schema.columns 
    WHERE 
        table_schema = 'public'
    ORDER BY 
        table_name, ordinal_position;
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query)
            tables = {}
            for row in result:
                table_name = row[0]
                if table_name not in tables:
                    tables[table_name] = []
                tables[table_name].append({
                    'Column': row[1],
                    'Type': row[2],
                    'Nullable': row[3],
                    'Default': row[4]
                })
            return tables
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def format_schema(tables):
    """
    Formats the schema dictionary into a readable output.
    """
    if not tables:
        print("No tables found or error occurred.")
        return

    print("\n" + "="*50)
    print("DATABASE SCHEMA OVERVIEW")
    print("="*50)

    for table_name, columns in tables.items():
        print(f"\nTable: {table_name}")
        print("-" * len(f"Table: {table_name}"))
        
        # Headers
        header = f"{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default'}"
        print(header)
        print("-" * len(header))
        
        for col in columns:
            nullable = "YES" if col['Nullable'] == 'YES' else "NO"
            default = str(col['Default']) if col['Default'] is not None else "None"
            print(f"{col['Column']:<25} {col['Type']:<20} {nullable:<10} {default}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    schema = get_db_schema()
    format_schema(schema)
