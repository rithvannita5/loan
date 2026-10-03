# scheduler.py
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'loan_system.db'))

def update_overdue_loans():
    """ធ្វើបច្ចុប្បន្នភាពស្ថានភាពកម្ចីហួសកំណត់"""
    if not os.path.exists(DATABASE_FILE):
        print(f"⚠️ Database not found at {DATABASE_FILE}")
        return

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    today = datetime.now().date().isoformat()

    cursor.execute('''
        UPDATE loans
        SET status = 'Bad Debt'
        WHERE status IN ('Approved', 'Pending')
        AND remaining_balance > 0
        AND julianday(?) - julianday(due_date) > 30
    ''', (today,))

    updated = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"✅ Updated {updated} overdue loans at {datetime.now()}")

if __name__ == '__main__':
    update_overdue_loans()
