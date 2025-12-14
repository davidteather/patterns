#!/usr/bin/env python3
"""
Database migration script for Debezium CDC setup.
Creates the customers table and configures it for full row replication.
"""

import psycopg2
import sys
import os
from psycopg2 import sql

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'example'),
    'user': os.getenv('POSTGRES_USER', 'dbz'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dbz'),
}


def create_customers_table(conn):
    """Create the customers table if it doesn't exist."""
    with conn.cursor() as cur:
        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'customers'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            print("✓ Table 'customers' already exists")
        else:
            # Create the customers table
            cur.execute("""
                CREATE TABLE customers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    email VARCHAR(255)
                );
            """)
            conn.commit()
            print("✓ Created 'customers' table")


def set_replica_identity(conn):
    """Set REPLICA IDENTITY to FULL for full row capture."""
    with conn.cursor() as cur:
        # Check current replica identity
        cur.execute("""
            SELECT relreplident 
            FROM pg_class 
            WHERE relname = 'customers';
        """)
        current_identity = cur.fetchone()[0]
        
        # relreplident values: 'd' = default, 'n' = nothing, 'f' = full, 'i' = index
        if current_identity == 'f':
            print("✓ REPLICA IDENTITY already set to FULL")
        else:
            cur.execute("ALTER TABLE customers REPLICA IDENTITY FULL;")
            conn.commit()
            print("✓ Set REPLICA IDENTITY to FULL for 'customers' table")


def create_replication_user(conn):
    """Create a replication user for Debezium if it doesn't exist."""
    with conn.cursor() as cur:
        # Check if replication user exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM pg_catalog.pg_user 
                WHERE usename = 'dbz'
            );
        """)
        user_exists = cur.fetchone()[0]
        
        if user_exists:
            # Grant replication privileges if not already granted
            try:
                cur.execute("ALTER USER dbz WITH REPLICATION;")
                conn.commit()
                print("✓ Replication user 'dbz' exists and has replication privileges")
            except Exception as e:
                # User might already have privileges
                print(f"✓ Replication user 'dbz' exists (privileges check: {e})")
        else:
            print("⚠ Replication user 'dbz' does not exist (this is OK if using docker-compose defaults)")


def main():
    """Main migration function."""
    print("Starting database migrations...")
    print(f"Connecting to {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Connected to database")
        
        # Run migrations
        create_customers_table(conn)
        set_replica_identity(conn)
        create_replication_user(conn)
        
        conn.close()
        print("\n✅ All migrations completed successfully!")
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Database connection failed: {e}")
        print("\nMake sure PostgreSQL is running:")
        print("  make up")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

