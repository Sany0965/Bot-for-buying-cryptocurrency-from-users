import sqlite3
import config

conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
cursor = conn.cursor()

def create_table():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        amount_usdt REAL,
        phone TEXT,
        invoice_id TEXT,
        rate REAL,
        rub_amount REAL,
        commission REAL,
        total_rub REAL,
        msg_id INTEGER
    )
    ''')
    conn.commit()

def save_amount(chat_id, amount):
    cursor.execute('REPLACE INTO users(chat_id, amount_usdt) VALUES(?, ?)', (chat_id, amount))
    conn.commit()

def save_phone(chat_id, phone):
    cursor.execute('UPDATE users SET phone = ? WHERE chat_id = ?', (phone, chat_id))
    conn.commit()

def save_invoice(chat_id, invoice_id):
    cursor.execute('UPDATE users SET invoice_id = ? WHERE chat_id = ?', (invoice_id, chat_id))
    conn.commit()

def save_msg_id(chat_id, msg_id):
    cursor.execute('UPDATE users SET msg_id = ? WHERE chat_id = ?', (msg_id, chat_id))
    conn.commit()

def save_final(chat_id, rate, rub_amount, commission, total_rub):
    cursor.execute(
        'UPDATE users SET rate=?, rub_amount=?, commission=?, total_rub=? WHERE chat_id=?',
        (rate, rub_amount, commission, total_rub, chat_id)
    )
    conn.commit()

def get_user(chat_id):
    cursor.execute('SELECT * FROM users WHERE chat_id=?', (chat_id,))
    return cursor.fetchone()

def delete_user(chat_id):
    cursor.execute('DELETE FROM users WHERE chat_id=?', (chat_id,))
    conn.commit()