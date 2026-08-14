from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_atm_key'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'atm_db'
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

@app.route('/')
def index():
    if 'card_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        card_number = request.form['card_number']
        pin = request.form['pin']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Cards WHERE card_number = %s", (card_number,))
        card = cursor.fetchone()
        
        if card:
            if card['status'] == 'blocked':
                flash('Карта заблокирована. Обратитесь в банк.', 'error')
            elif check_password_hash(card['pin_hash'], pin):
                cursor.execute("UPDATE Cards SET failed_attempts = 0 WHERE id_card = %s", (card['id_card'],))
                conn.commit()
                session['card_id'] = card['id_card']
                session['account_id'] = card['id_account']
                cursor.close()
                conn.close()
                return redirect(url_for('dashboard'))
            else:
                attempts = card['failed_attempts'] + 1
                if attempts >= 3:
                    cursor.execute("UPDATE Cards SET status = 'blocked', failed_attempts = %s WHERE id_card = %s", (attempts, card['id_card']))
                    flash('Карта заблокирована из-за неверного ПИН-кода.', 'error')
                else:
                    cursor.execute("UPDATE Cards SET failed_attempts = %s WHERE id_card = %s", (attempts, card['id_card']))
                    flash(f'Неверный ПИН-код. Осталось попыток: {3 - attempts}', 'error')
                conn.commit()
        else:
            flash('Карта не найдена.', 'error')
            
        cursor.close()
        conn.close()
        
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'card_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT balance FROM Accounts WHERE id_account = %s", (session['account_id'],))
    account = cursor.fetchone()
    
    cursor.execute("INSERT INTO Transactions (id_card, trans_type, amount) VALUES (%s, 'balance_check', 0)", (session['card_id'],))
    conn.commit()
    
    cursor.execute("SELECT * FROM Transactions WHERE id_card = %s ORDER BY created_at DESC LIMIT 5", (session['card_id'],))
    transactions = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', balance=account['balance'], transactions=transactions)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'card_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        amount = float(request.form['amount'])
        
        if amount <= 0 or amount % 100 != 0:
            flash('Сумма должна быть кратна 100.', 'error')
            return redirect(url_for('withdraw'))
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT balance FROM Accounts WHERE id_account = %s", (session['account_id'],))
        account = cursor.fetchone()
        
        if account['balance'] >= amount:
            new_balance = float(account['balance']) - amount
            cursor.execute("UPDATE Accounts SET balance = %s WHERE id_account = %s", (new_balance, session['account_id']))
            cursor.execute("INSERT INTO Transactions (id_card, trans_type, amount) VALUES (%s, 'withdraw', %s)", (session['card_id'], amount))
            conn.commit()
            flash(f'Успешно снято {amount} руб.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Недостаточно средств.', 'error')
            
        cursor.close()
        conn.close()
        
    return render_template('withdraw.html')

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'card_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        amount = float(request.form['amount'])
        
        if amount <= 0 or amount % 100 != 0:
            flash('Сумма должна быть кратна 100.', 'error')
            return redirect(url_for('deposit'))
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE Accounts SET balance = balance + %s WHERE id_account = %s", (amount, session['account_id']))
        cursor.execute("INSERT INTO Transactions (id_card, trans_type, amount) VALUES (%s, 'deposit', %s)", (session['card_id'], amount))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        flash(f'Счет успешно пополнен на {amount} руб.', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('deposit.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)