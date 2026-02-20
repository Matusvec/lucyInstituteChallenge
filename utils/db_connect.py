import psycopg2
from psycopg2 import OperationalError

# Database connection parameters
DB_CONFIG = {
    "host": "lucy-iqvia-db.c61zpvuf4ib1.us-east-1.rds.amazonaws.com",
    "port": 5432,
    "database": "postgres", 
    "user": "student_read_only_limited",           
    "password": "studentuseriqvialogin"         
}


def test_connection():
    """Test the database connection and print status."""
    try:
        print("Attempting to connect to the database...")
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Get server version to confirm connection
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print("Connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        # List available tables with row counts and columns
        # WARNING: 'main' table has 2+ billion rows - NEVER SELECT * FROM main!
        cursor.execute("""
            SELECT 
                t.table_name,
                (SELECT COUNT(*) FROM information_schema.columns c 
                 WHERE c.table_name = t.table_name AND c.table_schema = 'public') as col_count
            FROM information_schema.tables t
            WHERE t.table_schema = 'public'
            ORDER BY t.table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"\nAvailable tables ({len(tables)}):")
            print("-" * 50)
            for table_name, col_count in tables:
                # Get estimated row count (fast, doesn't scan table)
                cursor.execute(f"""
                    SELECT reltuples::bigint 
                    FROM pg_class 
                    WHERE relname = '{table_name}';
                """)
                row_count = cursor.fetchone()[0]
                warning = " DO NOT SELECT * !" if row_count > 1000000 else ""
                print(f"  {table_name}: ~{row_count:,} rows, {col_count} columns{warning}")
            
            # Show schema for each table
            print("\n" + "=" * 50)
            print("TABLE SCHEMAS:")
            print("=" * 50)
            for table_name, _ in tables:
                cursor.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                print(f"\n{table_name}:")
                for col_name, data_type in columns:
                    print(f"    {col_name} ({data_type})")
        else:
            print("\nNo tables found in public schema.")
        
        cursor.close()
        conn.close()
        print("\nConnection closed successfully.")
        return True
        
    except OperationalError as e:
        print(f"Connection failed!")
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    test_connection()
