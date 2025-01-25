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
    Dumps all tables from the database into an SQL file, excluding auto-incremented ID columns.
    """
    with engine.connect() as connection:
        with open(output_file, "w", encoding="utf-8") as f:
            # Dump Schema (Table Structure)
            print("-- Dumping Table Structure", file=f)
            tables = connection.execute(text("SHOW TABLES")).fetchall()
            for table in tables:
                table_name = table[0]  # Extract table name from tuple
                create_stmt = connection.execute(text(f"SHOW CREATE TABLE `{table_name}`"))
                create_stmt = create_stmt.fetchone()[1]
                f.write(f"\n-- Table structure for `{table_name}`\n")
                f.write(f"{create_stmt};\n\n")
            
            # Dump Data
            print("-- Dumping Table Data", file=f)
            for table in tables:
                table_name = table[0]  # Extract table name from tuple
                columns_query = connection.execute(text(f"DESCRIBE `{table_name}`"))
                columns = columns_query.fetchall()
                
                # Identify auto-increment column (usually `id`)
                non_auto_inc_columns = [col[0] for col in columns if "auto_increment" not in col[5].lower()]
                
                if not non_auto_inc_columns:
                    continue  # Skip tables with only an auto-increment column
                
                escaped_columns = [f"`{col}`" for col in non_auto_inc_columns]  # Escape column names
                rows = connection.execute(text(f"SELECT {', '.join(escaped_columns)} FROM `{table_name}`"))
                rows = rows.fetchall()
                
                if rows:
                    f.write(f"\n-- Dumping data for `{table_name}`\n")
                    
                    for row in rows:
                        values = ", ".join([f"'{str(value)}'" if value is not None else "NULL" for value in row])
                        insert_stmt = f"INSERT INTO `{table_name}` ({', '.join(escaped_columns)}) VALUES ({values});"
                        f.write(f"{insert_stmt}\n")
                
                f.write("\n")

    print(f"Database dump saved to {output_file}")

# Run the dump
dump_file = f"mysql_dump_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
dump_database(dump_file)


