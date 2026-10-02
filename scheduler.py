# scheduler.py - ដំណើរការប្រចាំថ្ងៃ
import sqlite3
from datetime import datetime, timedelta
import os

DATABASE_FILE = '/home/loan167/mysite/loan_system.db'

def update_overdue_loans():
    """ធ្វើបច្ចុប្បន្នភាពស្ថានភាពកម្ចីហួសកំណត់"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    today = datetime.now().date().isoformat()
    
    # កម្ចីដែលយឺតលើស 30 ថ្ងៃ -> Bad Debt
    cursor.execute('''
        UPDATE loans 
        SET status = 'Bad Debt' 
        WHERE status IN ('Approved', 'Pending')
        AND remaining_balance > 0
        AND julianday(?) - julianday(due_date) > 30
    ''', (today,))
    
    conn.commit()
    conn.close()
    print(f"✅ Updated overdue loans at {datetime.now()}")

if __name__ == '__main__':
    update_overdue_loans()