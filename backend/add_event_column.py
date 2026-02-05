"""Add event_date column to articles table"""

import sqlite3

conn = sqlite3.connect('eagle_harbor.db')
cur = conn.cursor()

try:
    # Add event_date column to articles table
    cur.execute('ALTER TABLE articles ADD COLUMN event_date TIMESTAMP')
    print('✅ Added event_date column to articles table')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e).lower():
        print('✓ event_date column already exists')
    else:
        print(f'Error: {e}')

# Create events table
try:
    cur.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(500) NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            event_date TIMESTAMP,
            end_date TIMESTAMP,
            location VARCHAR(500),
            description TEXT,
            article_id INTEGER NOT NULL,
            county VARCHAR(50),
            is_recurring BOOLEAN DEFAULT FALSE,
            is_past BOOLEAN DEFAULT FALSE,
            is_cancelled BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id)
        )
    ''')
    print('✅ Created events table')
except Exception as e:
    print(f'Events table: {e}')

conn.commit()
conn.close()

print('\n✅ Database schema updated successfully!')
