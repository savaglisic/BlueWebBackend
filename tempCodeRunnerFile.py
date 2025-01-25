import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import datetime

# Configure your database connection
DB_URI = "mysql+mysqlconnector://devuser:Sava2290!@localhost:3306/blueweb"
engine = create_engine(DB_URI)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

def dump_database(output_file):
    """
    Dumps all tables from the database into an SQL file.
    """
    with engine.connect() as connection:
        with open(output_file, "w", encoding="utf-8") as f:
            # Dump Schema (Table Structure)
            print("-- Dumping Table Structure", file=f)
            tables = connection.execute(text("SHOW TABLES")).fetchall()
            for table in tables:
                table_name = table[0]  # Extract table name from tuple
                create_stmt = connection.execute(text(f"SHOW CREATE TABLE {table_name}")).fetchone()[1]
                f.write(f"\n-- Table structure for `{table_name}`\n")
                f.write(f"{create_stmt};\n\n")
            
            # Dump Data
            print("-- Dumping Table Data", file=f)
            for table in tables:
                table_name = table[0]  # Extract table name from tuple
                rows = connection.execute(text(f"SELECT * FROM {table_name}")).fetchall()
                
                if rows:
                    # FIX: Extract column names properly
                    column_names = [col[0] for col in connection.execute(text(f"DESCRIBE {table_name}")).fetchall()]
                    
                    f.write(f"\n-- Dumping data for `{table_name}`\n")
                    
                    for row in rows:
                        values = ", ".join([f"'{str(value)}'" if value is not None else "NULL" for value in row])
                        insert_stmt = f"INSERT INTO `{table_name}` ({', '.join(column_names)}) VALUES ({values});"
                        f.write(f"{insert_stmt}\n")
                
                f.write("\n")

    print(f"Database dump saved to {output_file}")

# Run the dump
dump_file = f"mysql_dump_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
dump_database(dump_file)

