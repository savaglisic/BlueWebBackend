import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure your database connection
DB_URI = "mysql+mysqlconnector://devuser:Sava2290!@localhost:3306/blueweb"
engine = create_engine(DB_URI)

# Path to the dump file
DUMP_FILE = "/Users/savaglisic/Desktop/Code/BlueBackend/mysql_dump_20250125_204807.sql"

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

def drop_all_tables():
    """
    Drops all tables from the database to ensure a clean restoration.
    """
    with engine.connect() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))  # Disable foreign key checks
        tables = connection.execute(text("SHOW TABLES")).fetchall()
        for table in tables:
            table_name = table[0]
            connection.execute(text(f"DROP TABLE IF EXISTS `{table_name}`;"))
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))  # Re-enable foreign key checks
        connection.commit()

def restore_database(dump_file):
    """
    Restores the database from a given SQL dump file.
    """
    with engine.connect() as connection:
        with open(dump_file, "r", encoding="utf-8") as f:
            sql_commands = f.read()
        statements = sql_commands.split(";\n")  # Split by SQL statements
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement + ";"))  # Execute each statement
        connection.commit()

# Run the recovery process
drop_all_tables()
restore_database(DUMP_FILE)

print("Database restoration complete.")

