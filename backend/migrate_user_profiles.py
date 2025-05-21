import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import sys

# Create a minimal Flask app for migration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/mockster.ai')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def migrate_user_profiles():
    """Add missing columns to user_profiles table"""
    print("Starting migration of user_profiles table...")
    
    connection = db.engine.connect()
    
    # Check which columns need to be added
    inspector = db.inspect(db.engine)
    existing_columns = [column['name'] for column in inspector.get_columns('user_profiles')]
    
    # Define columns to add if they don't exist
    columns_to_check = [
        ('skills', 'TEXT'),
        ('location', 'VARCHAR(255)'),
        ('linkedin_url', 'VARCHAR(255)'),
        ('github_url', 'VARCHAR(255)'),
        ('portfolio_url', 'VARCHAR(255)'),
        ('bio', 'TEXT')
    ]
    
    try:
        # Begin a transaction
        trans = connection.begin()
        
        # Add missing columns
        for column_name, column_type in columns_to_check:
            if column_name not in existing_columns:
                print(f"Adding column {column_name} to user_profiles table...")
                # Use text() to create an executable SQL statement
                sql = text(f'ALTER TABLE user_profiles ADD COLUMN {column_name} {column_type};')
                connection.execute(sql)
                print(f"Column {column_name} added successfully")
            else:
                print(f"Column {column_name} already exists in user_profiles table")
        
        # Commit the transaction
        trans.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        # Roll back the transaction in case of error
        if 'trans' in locals():
            trans.rollback()
        print(f"Error during migration: {str(e)}")
        sys.exit(1)
    finally:
        # Close the connection
        connection.close()

if __name__ == "__main__":
    with app.app_context():
        migrate_user_profiles()