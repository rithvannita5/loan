from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import database as db
import re
import pytz


# ===== SET TIMEZONE TO CAMBODIA =====
CAMBODIA_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_cambodia_time():
    """ទាញយកពេលវេលាបច្ចុប្បន្នតាមម៉ោងកម្ពុជា"""
    return datetime.now(CAMBODIA_TZ)

def get_cambodia_date():
    """ទាញយកថ្ងៃបច្ចុប្បន្នតាមម៉ោងកម្ពុជា"""
    return datetime.now(CAMBODIA_TZ).date()


# ===== CREATE FLASK APP =====
app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-it-12345'

# ============================================================
# ===== NUMBER TO WORDS =====
# ============================================================

def number_to_words(number, currency='KHR'):
    """បម្លែងលេខទៅជាអក្សរខ្មែរ"""
    if not number or number == 0:
        if currency == 'KHR':
            return 'សូន្យរៀល'
        else:
            return 'សូន្យដុល្លា'

    if currency == 'KHR':
        number = round(number / 100) * 100
        number = int(number)
    else:
        number = round(number, 2)

    khmer_digits = ['', 'មួយ', 'ពីរ', 'បី', 'បួន', 'ប្រាំ', 'ប្រាំមួយ', 'ប្រាំពីរ', 'ប្រាំបី', 'ប្រាំបួន']
    khmer_positions = ['', 'ដប់', 'រយ', 'ពាន់', 'ម៉ឺន', 'សែន', 'លាន']

    if number < 10:
        result = khmer_digits[int(number)]
    else:
        result = ''
        num_str = str(number)
        length = len(num_str)

        for i, digit in enumerate(num_str):
            pos = length - i - 1
            d = int(digit)
            if d == 0:
                continue
            if pos == 1 and d == 1:
                result += 'ដប់'
            elif pos == 1:
                result += khmer_digits[d] + 'ដប់'
            else:
                result += khmer_digits[d] + khmer_positions[pos]

        result = result.replace('មួយដប់', 'ដប់')
        result = result.replace('ពីរដប់', 'ម្ភៃ')
        result = result.replace('បីដប់', 'សាមសិប')
        result = result.replace('បួនដប់', 'សែសិប')
        result = result.replace('ប្រាំដប់', 'ហាសិប')
        result = result.replace('ប្រាំមួយដប់', 'ហុកសិប')
        result = result.replace('ប្រាំពីរដប់', 'ចិតសិប')
        result = result.replace('ប្រាំបីដប់', 'ប៉ែតសិប')
        result = result.replace('ប្រាំបួនដប់', 'កៅសិប')

    if currency == 'KHR':
        return result + 'រៀល'
    else:
        return result + 'ដុល្លា'

# ============================================================
# ===== FORMAT NUMBER =====
# ============================================================

def format_number(amount, currency='USD'):
    if amount is None:
        amount = 0
    if currency == 'KHR':
        return '៛ ' + '{:,.0f}'.format(round(amount / 100) * 100)
    else:
        return '$ ' + '{:,.2f}'.format(amount)

# ============================================================
# ===== PAGE ROUTES =====
# ============================================================

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = db.get_user_by_username(username)
    if user and user['password'] == password:
        session['username'] = username
        session['user_id'] = user['id']
        session['full_name'] = user['full_name']
        session['role'] = user['role']  # <-- បន្ថែមនេះ
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error="ឈ្មោះអ្នកប្រើ ឬ ពាក្យសម្ងាត់មិនត្រឹមត្រូវ"), 401

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html', username=session.get('full_name', session['username']))

@app.route('/customers')
def customers():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('customers.html', username=session.get('full_name', session['username']))

@app.route('/create_customer')
def create_customer():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('create_customer.html', username=session.get('full_name', session['username']))

@app.route('/edit_customer')
def edit_customer():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('edit_customer.html', username=session.get('full_name', session['username']))

@app.route('/loans')
def loans():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('loans.html', username=session.get('full_name', session['username']))

@app.route('/loans/bad')
def loans_bad():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('loans_bad.html', username=session.get('full_name', session['username']))

@app.route('/create_loan')
def create_loan():
    if 'username' not in session:
        return redirect(url_for('index'))
    customers = db.get_all_customers_simple()
    return render_template('create_loan.html', username=session.get('full_name', session['username']), customers=customers)

@app.route('/edit_loan/<int:loan_id>')
def edit_loan(loan_id):
    if 'username' not in session:
        return redirect(url_for('index'))
    loan = db.get_loan_by_id(loan_id)
    if not loan:
        return "មិនឃើញកម្ចីនេះទេ!", 404
    customer = db.get_customer_by_id(loan['customer_id'])
    customers = db.get_all_customers_simple()
    return render_template('edit_loan.html', loan=loan, customer=customer, customers=customers, username=session.get('full_name', session['username']))

@app.route('/collection')
def collection():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('collection.html', 
                          username=session.get('full_name', session['username']))

@app.route('/collection_good')
def collection_good():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('collection_good.html', 
                          username=session.get('full_name', session['username']))

@app.route('/collection_late')
def collection_late():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('collection_late.html', 
                          username=session.get('full_name', session['username']))

@app.route('/collection_bad')
def collection_bad():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('collection_bad.html', 
                          username=session.get('full_name', session['username']))

@app.route('/settings')
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html', username=session.get('full_name', session['username']))

@app.route('/payments')
def payments():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('payment.html', username=session.get('full_name', session['username']))

@app.route('/disbursement')
def disbursement():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('disbursement.html', username=session.get('full_name', session['username']))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('full_name', None)
    return redirect(url_for('index'))

# ============================================================
# ===== PRINT ROUTES =====
# ============================================================

@app.route('/print_contract/<int:loan_id>')
def print_contract(loan_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    loan = db.get_loan_by_id(loan_id)
    if not loan:
        return "មិនឃើញកម្ចីនេះទេ!", 404

    customer = db.get_customer_by_id(loan['customer_id'])
    if not customer:
        customer = {
            'name': 'មិនស្គាល់',
            'code': '',
            'gender': '',
            'phone': '',
            'address': '',
            'dob': '',
            'id_card': '',
            'guarantor_name': '',
            'guarantor_gender': '',
            'guarantor_id_card': '',
            'guarantor_dob': '',
            'guarantor_phone': '',
            'guarantor_address': '',
            'relation': ''
        }

    # ===== គណនា Schedule =====
    schedule_data = []
    if loan.get('duration_num') and loan['duration_num'] > 0:
        total_payment = (loan.get('loan_amount', 0) or 0) + (loan.get('total_interest', 0) or 0)
        daily_payment = total_payment / loan['duration_num']

        if loan.get('currency') == 'KHR':
            daily_payment = round(daily_payment / 100) * 100
        else:
            daily_payment = round(daily_payment, 2)

        schedule_data = [{'payment': daily_payment, 'period': 1}]

    # ===== ចម្លង loan និង customer ទៅ dict =====
    loan_dict = dict(loan) if isinstance(loan, dict) else loan
    customer_dict = dict(customer) if isinstance(customer, dict) else customer

    return render_template('print_contract.html',
                         loan=loan_dict,
                         customer=customer_dict,
                         schedule_data=schedule_data,
                         username=session.get('full_name', session['username']),
                         now=get_cambodia_time(),
                         number_to_words=number_to_words)

@app.route('/print_schedule/<int:loan_id>')
def print_schedule(loan_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    loan = db.get_loan_by_id(loan_id)
    if not loan:
        return "មិនឃើញកម្ចីនេះទេ!", 404

    customer = db.get_customer_by_id(loan['customer_id'])
    loan_dict = dict(loan) if not isinstance(loan, dict) else loan
    customer_dict = dict(customer) if customer and not isinstance(customer, dict) else (customer or {})

    # ============================================================
    # ===== គណនា Schedule តាម calc_type (ដូច /api/calculate_loan) =====
    # ============================================================
    schedule_data = []
    loan_amount = float(loan.get('loan_amount', 0))
    interest_rate = float(loan.get('interest_rate', 0))
    duration_num = int(loan.get('duration_num', 0))
    currency = loan.get('currency', 'USD')
    calc_type = int(loan.get('calc_type', 1))

    if duration_num > 0 and loan_amount > 0:
        rate_decimal = interest_rate / 100

        # ===== ថ្ងៃចាប់ផ្ដើម =====
        try:
            start_date = datetime.strptime(loan['loan_date'], '%Y-%m-%d').date()
        except:
            start_date = get_cambodia_date()

        # ============================================================
        # ===== ១. រំលោះបង់ថេរ (Equal Installment) =====
        # ============================================================
        if calc_type == 1:
            if rate_decimal > 0:
                daily_payment = loan_amount * (rate_decimal * (1 + rate_decimal) ** duration_num) / ((1 + rate_decimal) ** duration_num - 1)
            else:
                daily_payment = loan_amount / duration_num

            balance = loan_amount
            for i in range(1, duration_num + 1):
                due_date = db.get_next_working_day(start_date, i)
                interest = balance * rate_decimal
                principal = daily_payment - interest

                if i == duration_num:
                    principal = balance
                    payment = balance + interest
                else:
                    payment = daily_payment

                balance -= principal

                if currency == 'KHR':
                    interest = round(interest / 100) * 100 if interest > 0 else 0
                    principal = round(principal / 100) * 100 if principal > 0 else 0
                    payment = round(payment / 100) * 100 if payment > 0 else 0
                    balance = round(balance / 100) * 100 if balance > 0 else 0
                else:
                    interest = round(interest, 2)
                    principal = round(principal, 2)
                    payment = round(payment, 2)
                    balance = round(balance, 2)

                schedule_data.append({
                    'period': i,
                    'payment': payment,
                    'interest': interest,
                    'principal': principal,
                    'balance': max(balance, 0),
                    'due_date': due_date.strftime('%Y-%m-%d')
                })

        # ============================================================
        # ===== ២. ដើមថេរ ការថេរ (Flat Rate) =====
        # ============================================================
        elif calc_type == 2:
            total_interest = loan_amount * rate_decimal * duration_num
            total_payment = loan_amount + total_interest
            daily_payment = total_payment / duration_num
            daily_principal = loan_amount / duration_num
            daily_interest = total_interest / duration_num

            balance = loan_amount
            for i in range(1, duration_num + 1):
                due_date = db.get_next_working_day(start_date, i)

                if i == duration_num:
                    principal = balance
                    interest = daily_interest
                    payment = balance + interest
                else:
                    principal = daily_principal
                    interest = daily_interest
                    payment = daily_payment

                balance -= principal

                if currency == 'KHR':
                    interest = round(interest / 100) * 100 if interest > 0 else 0
                    principal = round(principal / 100) * 100 if principal > 0 else 0
                    payment = round(payment / 100) * 100 if payment > 0 else 0
                    balance = round(balance / 100) * 100 if balance > 0 else 0
                else:
                    interest = round(interest, 2)
                    principal = round(principal, 2)
                    payment = round(payment, 2)
                    balance = round(balance, 2)

                schedule_data.append({
                    'period': i,
                    'payment': payment,
                    'interest': interest,
                    'principal': principal,
                    'balance': max(balance, 0),
                    'due_date': due_date.strftime('%Y-%m-%d')
                })

        # ============================================================
        # ===== ៣. បង់តែការ បង់ថយ (Interest Only + 2 Stages Principal) =====
        # ============================================================
        elif calc_type == 3:
            midpoint = duration_num // 2
            principal_payment_1 = loan_amount / 2
            balance = loan_amount

            for i in range(1, duration_num + 1):
                due_date = db.get_next_working_day(start_date, i)
                interest = balance * rate_decimal

                if i == midpoint:
                    principal = principal_payment_1
                elif i == duration_num:
                    principal = balance
                else:
                    principal = 0

                payment = principal + interest
                balance -= principal

                if currency == 'KHR':
                    interest = round(interest / 100) * 100 if interest > 0 else 0
                    principal = round(principal / 100) * 100 if principal > 0 else 0
                    payment = round(payment / 100) * 100 if payment > 0 else 0
                    balance = round(balance / 100) * 100 if balance > 0 else 0
                else:
                    interest = round(interest, 2)
                    principal = round(principal, 2)
                    payment = round(payment, 2)
                    balance = round(balance, 2)

                schedule_data.append({
                    'period': i,
                    'payment': payment,
                    'interest': interest,
                    'principal': principal,
                    'balance': max(balance, 0),
                    'due_date': due_date.strftime('%Y-%m-%d')
                })

        # ============================================================
        # ===== ៤. បង់តែការប្រាក់ (Interest Only) =====
        # ============================================================
        elif calc_type == 4:
            daily_interest = loan_amount * rate_decimal
            balance = loan_amount

            for i in range(1, duration_num + 1):
                due_date = db.get_next_working_day(start_date, i)
                principal = 0
                interest = daily_interest
                payment = daily_interest

                if currency == 'KHR':
                    interest = round(interest / 100) * 100 if interest > 0 else 0
                    payment = round(payment / 100) * 100 if payment > 0 else 0
                else:
                    interest = round(interest, 2)
                    payment = round(payment, 2)

                schedule_data.append({
                    'period': i,
                    'payment': payment,
                    'interest': interest,
                    'principal': principal,
                    'balance': balance,
                    'due_date': due_date.strftime('%Y-%m-%d')
                })

    return render_template('print_schedule.html',
                         loan=loan_dict,
                         customer=customer_dict,
                         schedule_data=schedule_data,
                         username=session.get('full_name', session['username']),
                         now=get_cambodia_time())

# ============================================================
# ===== API ROUTES =====
# ============================================================

@app.route('/api/current_user')
def api_current_user():
    if 'username' in session:
        return jsonify({'username': session['username'], 'full_name': session.get('full_name', session['username'])})
    return jsonify({'username': None})

# ===== API: CUSTOMERS =====
@app.route('/api/customers')
def api_customers():
    if 'username' not in session:
        return jsonify([])

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')

    # ===== ទាញយកតួនាទី និងឈ្មោះអ្នកប្រើ =====
    user_role = session.get('role', 'user')
    username = session.get('username', '')

    if user_role == 'officer':
        # ===== CO ឃើញតែអតិថិជនដែលខ្លួនទទួលខុសត្រូវ =====
        # ===== ទាញយកបញ្ជី customer_id ពី loans ដែល co_officer = username =====
        conn = db.get_db_connection()
        customer_ids = conn.execute('''
            SELECT DISTINCT customer_id FROM loans
            WHERE co_officer = ?
        ''', (username,)).fetchall()
        customer_ids = [c['customer_id'] for c in customer_ids]
        conn.close()

        if not customer_ids:
            return jsonify([])

        # ===== ច្រោះអតិថិជនតាម customer_ids =====
        conn = db.get_db_connection()
        placeholders = ','.join(['?'] * len(customer_ids))
        if search:
            like = f'%{search}%'
            query = f'''
                SELECT * FROM customers
                WHERE id IN ({placeholders})
                AND (name LIKE ? OR code LIKE ? OR phone LIKE ? OR address LIKE ?)
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            '''
            params = customer_ids + [like, like, like, like, per_page, (page - 1) * per_page]
        else:
            query = f'''
                SELECT * FROM customers
                WHERE id IN ({placeholders})
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            '''
            params = customer_ids + [per_page, (page - 1) * per_page]

        customers = conn.execute(query, params).fetchall()
        conn.close()

        customers_data = []
        for c in customers:
            customers_data.append({
                'id': c['id'], 'code': c['code'], 'name': c['name'],
                'gender': c['gender'], 'phone': c['phone'], 'id_card': c['id_card'],
                'address': c['address'], 'guarantor_name': c['guarantor_name'],
                'guarantor_gender': c['guarantor_gender'],
                'guarantor_id_card': c['guarantor_id_card'],
                'guarantor_address': c['guarantor_address'],
                'guarantor_phone': c['guarantor_phone'], 'relation': c['relation'],
                'dob': c['dob'] or '', 'guarantor_dob': c['guarantor_dob'] or ''
            })
        return jsonify(customers_data)

    else:
        # ===== Admin ឃើញទាំងអស់ =====
        if search:
            customer_list = db.search_customers_paginated(search, page, per_page)
        else:
            customer_list = db.get_customers_paginated(page, per_page)

        customers_data = []
        for c in customer_list:
            customers_data.append({
                'id': c['id'], 'code': c['code'], 'name': c['name'],
                'gender': c['gender'], 'phone': c['phone'], 'id_card': c['id_card'],
                'address': c['address'], 'guarantor_name': c['guarantor_name'],
                'guarantor_gender': c['guarantor_gender'],
                'guarantor_id_card': c['guarantor_id_card'],
                'guarantor_address': c['guarantor_address'],
                'guarantor_phone': c['guarantor_phone'], 'relation': c['relation'],
                'dob': c['dob'] or '', 'guarantor_dob': c['guarantor_dob'] or ''
            })
        return jsonify(customers_data)

@app.route('/api/customers/count')
def api_customers_count():
    if 'username' not in session:
        return jsonify({'count': 0})
    search = request.args.get('search', '')
    if search:
        count = db.count_search_customers(search)
    else:
        count = db.count_customers()
    return jsonify({'count': count})

@app.route('/api/customer/<int:customer_id>')
def api_get_customer(customer_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    customer = db.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({'error': 'រកមិនឃើញអតិថិជន!'}), 404
    return jsonify(dict(customer))

@app.route('/api/search_customers')
def api_search_customers():
    if 'username' not in session:
        return jsonify([])
    keyword = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    results = db.search_customers(keyword, limit)
    customers_data = []
    for c in results:
        customers_data.append({
            'id': c['id'], 'code': c['code'], 'name': c['name'],
            'gender': c['gender'], 'phone': c['phone'], 'id_card': c['id_card'],
            'address': c['address'], 'guarantor_name': c['guarantor_name'],
            'guarantor_gender': c['guarantor_gender'],
            'guarantor_id_card': c['guarantor_id_card'],
            'guarantor_address': c['guarantor_address'],
            'guarantor_phone': c['guarantor_phone'], 'relation': c['relation'],
            'dob': c['dob'] or '', 'guarantor_dob': c['guarantor_dob'] or ''
        })
    return jsonify(customers_data)

@app.route('/api/create_customer', methods=['POST'])
def api_create_customer():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    if not data.get('code') or not data.get('name'):
        return jsonify({'error': 'លេខកូដ និង ឈ្មោះអតិថិជន ត្រូវបានទាមទារ'}), 400
    existing = db.get_customer_by_code(data['code'])
    if existing:
        return jsonify({'error': f'លេខកូដ {data["code"]} មានរួចហើយ!'}), 400
    customer_id = db.create_customer(data)
    db.log_activity(customer_id, None, 'create', 'បានបង្កើតអតិថិជនថ្មី', user_id=session.get('user_id'))
    return jsonify({'success': True, 'id': customer_id})

@app.route('/api/update_customer', methods=['POST'])
def api_update_customer():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    if not data.get('id'):
        return jsonify({'error': 'Missing customer ID'}), 400
    if not data.get('code') or not data.get('name'):
        return jsonify({'error': 'លេខកូដ និង ឈ្មោះអតិថិជន ត្រូវបានទាមទារ'}), 400
    existing = db.get_customer_by_code(data['code'])
    if existing and existing['id'] != int(data['id']):
        return jsonify({'error': f'លេខកូដ {data["code"]} មានរួចហើយ!'}), 400
    db.update_customer(data['id'], data)
    db.log_activity(data['id'], None, 'update', 'បានកែប្រែព័ត៌មានអតិថិជន', user_id=session.get('user_id'))
    return jsonify({'success': True})

@app.route('/api/delete_customer', methods=['POST'])
def api_delete_customer():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    customer_id = data.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Missing customer_id'}), 400
    db.delete_customer(customer_id)
    db.log_activity(customer_id, None, 'delete', 'បានលុបអតិថិជន', user_id=session.get('user_id'))
    return jsonify({'success': True})

@app.route('/api/generate_customer_code')
def api_generate_customer_code():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    new_code = db.generate_customer_code()
    return jsonify({'code': new_code})

# ===== API: LOANS =====
@app.route('/api/loans')
def api_loans():
    if 'username' not in session:
        return jsonify([])

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status', '')

    user_role = session.get('role', 'user')
    username = session.get('username', '')

    # ===== ប្រសិនបើជា CO ច្រោះតាម co_officer =====
    if user_role == 'officer':
        loan_list = db.get_loans_by_officer(username, page, per_page, status)
    else:
        loan_list = db.get_loans_paginated(page, per_page, status)

    loans_data = []
    for l in loan_list:
        loans_data.append({
            'id': l['id'], 'customer_id': l['customer_id'],
            'customer_code': l['customer_code'], 'customer_name': l['customer_name'],
            'customer_gender': l['customer_gender'], 'customer_phone': l['customer_phone'],
            'customer_id_card': l['customer_id_card'], 'customer_address': l['customer_address'],
            'guarantor_name': l['guarantor_name'], 'guarantor_gender': l['guarantor_gender'],
            'guarantor_id_card': l['guarantor_id_card'], 'guarantor_phone': l['guarantor_phone'],
            'guarantor_address': l['guarantor_address'], 'relation': l['relation'],
            'loan_amount': l['loan_amount'], 'currency': l['currency'],
            'interest_rate': l['interest_rate'], 'total_interest': l['total_interest'],
            'total_amount': l['loan_amount'] + l['total_interest'],
            'amount_paid': l['amount_paid'], 'remaining_balance': l['remaining_balance'],
            'status': l['status'], 'co_officer': l['co_officer'] or '',
            'loan_date': l['loan_date'] or '', 'due_date': l['due_date'] or '',
            'duration_num': l['duration_num'] or 0,
            'duration_type': l['duration_type'] or 'ថ្ងៃ',
            'created_at': l['created_at']
        })
    return jsonify(loans_data)

@app.route('/api/loans/count')
def api_loans_count():
    if 'username' not in session:
        return jsonify({'count': 0})
    status = request.args.get('status', '')
    count = db.count_loans(status)
    return jsonify({'count': count})

@app.route('/api/loans/bad')
def api_loans_bad():
    if 'username' not in session:
        return jsonify([])

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    loan_list = db.get_loans_paginated(page, per_page, 'Bad Debt')

    loans_data = []
    for l in loan_list:
        loans_data.append({
            'id': l['id'], 'customer_id': l['customer_id'],
            'customer_code': l['customer_code'], 'customer_name': l['customer_name'],
            'customer_gender': l['customer_gender'], 'customer_phone': l['customer_phone'],
            'customer_id_card': l['customer_id_card'], 'customer_address': l['customer_address'],
            'guarantor_name': l['guarantor_name'], 'guarantor_gender': l['guarantor_gender'],
            'guarantor_id_card': l['guarantor_id_card'], 'guarantor_phone': l['guarantor_phone'],
            'guarantor_address': l['guarantor_address'], 'relation': l['relation'],
            'loan_amount': l['loan_amount'], 'currency': l['currency'],
            'interest_rate': l['interest_rate'], 'total_interest': l['total_interest'],
            'total_amount': l['loan_amount'] + l['total_interest'],
            'amount_paid': l['amount_paid'], 'remaining_balance': l['remaining_balance'],
            'status': l['status'], 'co_officer': l['co_officer'] or '',
            'loan_date': l['loan_date'] or '', 'due_date': l['due_date'] or '',
            'duration_num': l['duration_num'] or 0,
            'duration_type': l['duration_type'] or 'ថ្ងៃ',
            'created_at': l['created_at']
        })
    return jsonify(loans_data)

@app.route('/api/generate_loan_code')
def api_generate_loan_code():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    loan_code = db.generate_loan_code()
    return jsonify({'loan_code': loan_code})

# ===== API: CALCULATE LOAN =====
@app.route('/api/calculate_loan', methods=['POST'])
def api_calculate_loan():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    loan_amount = float(data.get('loan_amount', 0))
    interest_rate = float(data.get('interest_rate', 0))
    duration_num = int(data.get('duration_num', 0))
    currency = data.get('currency', 'USD')
    start_date_str = data.get('start_date', '')
    service_fee = float(data.get('service_fee', 0))
    calc_type = int(data.get('calc_type', 1))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except:
        start_date = get_cambodia_date()

    if duration_num <= 0:
        return jsonify({'error': 'ចំនួនថ្ងៃមិនត្រឹមត្រូវ'}), 400

    # ============================================================
    # ===== គណនាតាមប្រភេទការគណនា =====
    # ============================================================
    schedule = []
    rate_decimal = interest_rate / 100

    if calc_type == 1:
        # ============================================================
        # ===== ១. រំលោះបង់ថេរ (Equal Installment) =====
        # ============================================================
        # បង់ថេររាល់ថ្ងៃ ប៉ុន្តែការប្រាក់ខ្ពស់ដំបូង ថយក្រោយ
        # ប្រាក់ដើមចុះតិចដំបូង ចុះច្រើនក្រោយ
        
        # គណនាបង់ប្រចាំថ្ងៃតាមរូបមន្ត Annuity
        if rate_decimal > 0:
            daily_payment = loan_amount * (rate_decimal * (1 + rate_decimal) ** duration_num) / ((1 + rate_decimal) ** duration_num - 1)
        else:
            daily_payment = loan_amount / duration_num
        
        balance = loan_amount
        total_interest = 0
        total_payment = 0

        for i in range(1, duration_num + 1):
            due_date = db.get_next_working_day(start_date, i)
            
            # ការប្រាក់គណនាលើសមតុល្យ
            interest = balance * rate_decimal
            principal = daily_payment - interest
            
            # វគ្គចុងក្រោយ
            if i == duration_num:
                principal = balance
                payment = balance + interest
            else:
                payment = daily_payment
            
            balance -= principal
            total_interest += interest
            total_payment += payment

            # បង្គត់
            if currency == 'KHR':
                interest = round(interest / 100) * 100 if interest > 0 else 0
                principal = round(principal / 100) * 100 if principal > 0 else 0
                payment = round(payment / 100) * 100 if payment > 0 else 0
                balance = round(balance / 100) * 100 if balance > 0 else 0
            else:
                interest = round(interest, 2)
                principal = round(principal, 2)
                payment = round(payment, 2)
                balance = round(balance, 2)

            schedule.append({
                'period': i,
                'payment': payment,
                'interest': interest,
                'principal': principal,
                'balance': max(balance, 0),
                'due_date': due_date.strftime('%Y-%m-%d')
            })

    elif calc_type == 2:
        # ============================================================
        # ===== ២. ដើមថេរ ការថេរ (Flat Rate) =====
        # ============================================================
        # ការប្រាក់គណនាលើប្រាក់ដើមដើម (មិនថយ)
        # បង់ថេររាល់ថ្ងៃ
        
        total_interest = loan_amount * rate_decimal * duration_num
        total_payment = loan_amount + total_interest
        daily_payment = total_payment / duration_num
        daily_principal = loan_amount / duration_num
        daily_interest = total_interest / duration_num
        
        balance = loan_amount

        for i in range(1, duration_num + 1):
            due_date = db.get_next_working_day(start_date, i)
            
            if i == duration_num:
                principal = balance
                interest = daily_interest
                payment = balance + interest
            else:
                principal = daily_principal
                interest = daily_interest
                payment = daily_payment
            
            balance -= principal

            # បង្គត់
            if currency == 'KHR':
                interest = round(interest / 100) * 100 if interest > 0 else 0
                principal = round(principal / 100) * 100 if principal > 0 else 0
                payment = round(payment / 100) * 100 if payment > 0 else 0
                balance = round(balance / 100) * 100 if balance > 0 else 0
            else:
                interest = round(interest, 2)
                principal = round(principal, 2)
                payment = round(payment, 2)
                balance = round(balance, 2)

            schedule.append({
                'period': i,
                'payment': payment,
                'interest': interest,
                'principal': principal,
                'balance': max(balance, 0),
                'due_date': due_date.strftime('%Y-%m-%d')
            })

    elif calc_type == 3:
        # ============================================================
        # ===== ៣. បង់តែការ បង់ថយ (Interest Only + Partial Principal) =====
        # ============================================================
        # បង់តែការប្រាក់រាល់ថ្ងៃ + ប្រាក់ដើមបង់ថយៗ ជា ២ ដំណាក់កាល
        # - ដំណាក់កាល ១ (ពាក់កណ្តាល): បង់ប្រាក់ដើម 50%
        # - ដំណាក់កាល ២ (ចប់): បង់ប្រាក់ដើម 50% ដែលនៅសល់
        
        balance = loan_amount
        total_interest = 0
        total_payment = 0
        
        # ===== ចំណុចបង់ប្រាក់ដើម =====
        midpoint = duration_num // 2  # ថ្ងៃកណ្តាល
        principal_payment_1 = loan_amount / 2  # ៥០% ថ្ងៃកណ្តាល
        principal_payment_2 = loan_amount - principal_payment_1  # ៥០% ថ្ងៃចប់

        for i in range(1, duration_num + 1):
            due_date = db.get_next_working_day(start_date, i)
            
            # ===== ការប្រាក់គណនាលើសមតុល្យបច្ចុប្បន្ន =====
            interest = balance * rate_decimal
            
            # ===== កំណត់ប្រាក់ដើមបង់ =====
            if i == midpoint:
                # ថ្ងៃកណ្តាល: បង់ 50%
                principal = principal_payment_1
            elif i == duration_num:
                # ថ្ងៃចប់: បង់អោសដែលនៅសល់
                principal = balance
            else:
                # ថ្ងៃផ្សេងទៀត: បង់តែការប្រាក់
                principal = 0
            
            payment = principal + interest
            balance -= principal
            total_interest += interest
            total_payment += payment

            # ===== បង្គត់តាមរូបិយប័ណ្ណ =====
            if currency == 'KHR':
                interest = round(interest / 100) * 100 if interest > 0 else 0
                principal = round(principal / 100) * 100 if principal > 0 else 0
                payment = round(payment / 100) * 100 if payment > 0 else 0
                balance = round(balance / 100) * 100 if balance > 0 else 0
            else:
                interest = round(interest, 2)
                principal = round(principal, 2)
                payment = round(payment, 2)
                balance = round(balance, 2)

            schedule.append({
                'period': i,
                'payment': payment,
                'interest': interest,
                'principal': principal,
                'balance': max(balance, 0),
                'due_date': due_date.strftime('%Y-%m-%d')
            })

    elif calc_type == 4:
        # ============================================================
        # ===== ៤. បង់តែការប្រាក់ (Interest Only) =====
        # ============================================================
        # បង់តែការប្រាក់ ប្រាក់ដើមមិនបង់
        
        daily_interest = loan_amount * rate_decimal
        total_interest = daily_interest * duration_num
        total_payment = loan_amount + total_interest
        
        balance = loan_amount

        for i in range(1, duration_num + 1):
            due_date = db.get_next_working_day(start_date, i)
            
            principal = 0
            interest = daily_interest
            payment = daily_interest
            
            # មិនបន្ថយ balance ទេ

            # បង្គត់
            if currency == 'KHR':
                interest = round(interest / 100) * 100 if interest > 0 else 0
                payment = round(payment / 100) * 100 if payment > 0 else 0
            else:
                interest = round(interest, 2)
                payment = round(payment, 2)

            schedule.append({
                'period': i,
                'payment': payment,
                'interest': interest,
                'principal': principal,
                'balance': balance,
                'due_date': due_date.strftime('%Y-%m-%d')
            })

    # ===== គណនាសេវារដ្ឋបាល =====
    service_amount = loan_amount * (service_fee / 100)

    # ===== បង្គត់តាមរូបិយប័ណ្ណ =====
    def round_amount(amount):
        if currency == 'KHR':
            if amount < 100 and amount > 0:
                return round(amount)
            return round(amount / 100) * 100
        return round(amount, 2)

    return jsonify({
        'total_payment': round_amount(total_payment),
        'total_interest': round_amount(total_interest),
        'daily_payment': round_amount(daily_payment) if calc_type in [1, 2] else 0,
        'service_amount': round_amount(service_amount),
        'calc_type': calc_type,
        'duration_num': duration_num,
        'schedule': schedule
    })

@app.route('/api/create_loan', methods=['POST'])
def api_create_loan():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if not data.get('customer_id') or not data.get('loan_amount'):
        return jsonify({'error': 'សូមជ្រើសរើសអតិថិជន និងបញ្ចូលទឹកប្រាក់កម្ចី'}), 400

    # ===== គណនាការប្រាក់នៅ Backend (Override Frontend) =====
    loan_amount = float(data.get('loan_amount', 0))
    interest_rate = float(data.get('interest_rate', 0))
    duration_num = int(data.get('duration_num', 0))
    currency = data.get('currency', 'USD')

    # ===== គណនាការប្រាក់សរុប =====
    total_interest = loan_amount * (interest_rate / 100) * duration_num
    total_amount = loan_amount + total_interest

    # ===== បង្គត់តាមរូបិយប័ណ្ណ =====
    if currency == 'KHR':
        total_interest = round(total_interest / 100) * 100
        total_amount = round(total_amount / 100) * 100
    else:
        total_interest = round(total_interest, 2)
        total_amount = round(total_amount, 2)

    # ===== Override Data =====
    data['total_interest'] = total_interest
    data['total_amount'] = total_amount
    data['remaining_balance'] = total_amount
    data['amount_paid'] = 0

    print(f"📊 Creating loan:")
    print(f"   Amount: {loan_amount}")
    print(f"   Rate: {interest_rate}%")
    print(f"   Duration: {duration_num} days")
    print(f"   Interest: {total_interest}")
    print(f"   Total: {total_amount}")

    loan_id = db.create_loan(data)
    db.log_activity(data['customer_id'], loan_id, 'create_loan', 'បានបង្កើតកម្ចីថ្មី', user_id=session.get('user_id'))
    return jsonify({'success': True, 'id': loan_id})

@app.route('/api/update_loan', methods=['POST'])
def api_update_loan():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    if not data.get('id'):
        return jsonify({'error': 'Missing loan ID'}), 400
    if not data.get('customer_id') or not data.get('loan_amount'):
        return jsonify({'error': 'សូមជ្រើសរើសអតិថិជន និងបញ្ចូលទឹកប្រាក់កម្ចី'}), 400
    db.update_loan(data['id'], data)
    db.log_activity(data['customer_id'], data['id'], 'update_loan', 'បានកែប្រែព័ត៌មានកម្ចី', user_id=session.get('user_id'))
    return jsonify({'success': True})

@app.route('/api/update_loan_status', methods=['POST'])
def api_update_loan_status():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    loan_id = data.get('loan_id')
    status = data.get('status')
    if not loan_id or not status:
        return jsonify({'error': 'Missing data'}), 400
    db.update_loan_status(loan_id, status)
    db.log_activity(None, loan_id, 'update_loan_status', f'បានផ្លាស់ប្ដូរស្ថានភាពកម្ចីទៅ {status}', user_id=session.get('user_id'))
    return jsonify({'success': True})

@app.route('/api/delete_loan', methods=['POST'])
def api_delete_loan():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    loan_id = data.get('loan_id')
    if not loan_id:
        return jsonify({'error': 'Missing loan_id'}), 400
    db.delete_loan(loan_id)
    db.log_activity(None, loan_id, 'delete_loan', 'បានលុបកម្ចី', user_id=session.get('user_id'))
    return jsonify({'success': True})

@app.route('/api/customer_for_loan/<int:customer_id>')
def api_customer_for_loan(customer_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    customer = db.get_customer_for_loan(customer_id)
    if not customer:
        return jsonify({'error': 'មិនឃើញអតិថិជន'}), 404
    return jsonify(dict(customer))

# ===== API: COLLECTION =====
@app.route('/api/collection/<string:type>')
def api_collection(type):
    if 'username' not in session:
        return jsonify([])

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)

        user_role = session.get('role', 'user')
        username = session.get('username', '')

        # ===== ប្រសិនបើជា CO ច្រោះតាម co_officer =====
        if user_role == 'officer':
            filtered_loans = db.get_collection_loans_by_officer(type, username, page, per_page)
        else:
            filtered_loans = db.get_collection_loans(type, page, per_page)

        loans_data = []
        for item in filtered_loans:
            loans_data.append({
                'id': item['id'],
                'loan_code': item.get('loan_code') or 'N/A',
                'customer_code': item.get('customer_code') or 'N/A',
                'customer_name': item.get('customer_name') or 'មិនស្គាល់',
                'customer_phone': item.get('customer_phone') or '-',
                'customer_address': item.get('customer_address') or '-',
                'loan_amount': item.get('loan_amount') or 0,
                'currency': item.get('currency') or 'USD',
                'total_interest': item.get('total_interest') or 0,
                'status': item.get('status') or 'Pending',
                'due_date': item.get('due_date') or '',
                'co_officer': item.get('co_officer') or '',
                'days_overdue': item.get('days_overdue') or 0,
                'total_due': item.get('total_due') or 0,
                'principal': item.get('principal_due') or 0,
                'interest': item.get('interest_due') or 0,
                'penalty': item.get('penalty') or 0,
                'remaining_balance': item.get('remaining_balance') or 0
            })

        return jsonify(loans_data)
    except Exception as e:
        import traceback
        print("ERROR in api_collection:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/collection/count/<string:type>')
def api_collection_count(type):
    if 'username' not in session:
        return jsonify({'count': 0})
    count = db.count_collection_loans(type)
    return jsonify({'count': count})

# ===== API: COLLECTION PAYMENT =====
@app.route('/api/collection_payment', methods=['POST'])
def api_collection_payment():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    loan_id = data.get('loan_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method', 'cash')
    penalty = data.get('penalty', 0)
    notes = data.get('notes', '')

    if not loan_id or not amount:
        return jsonify({'error': 'Missing data'}), 400

    loan = db.get_loan_by_id(loan_id)
    if not loan:
        return jsonify({'error': 'មិនឃើញកម្ចីនេះទេ!'}), 404

    from datetime import datetime
    try:
        loan_date = datetime.strptime(loan['loan_date'], '%Y-%m-%d').date()
        today = get_cambodia_date()
        period = (today - loan_date).days + 1
    except:
        period = 1

    total_paid = loan['amount_paid'] + amount
    remaining = loan['remaining_balance'] - amount

    if penalty > 0:
        remaining = remaining + penalty

    status = loan['status']
    if remaining <= 0:
        status = 'Completed'
        remaining = 0

    db.update_loan_payment(loan_id, total_paid, remaining, status)

    db.log_activity(
        loan['customer_id'],
        loan_id,
        'collection_payment',
        f'បានប្រមូលប្រាក់ ${amount:.2f} តាមរយៈ {payment_method}',
        user_id=session.get('user_id')
    )

    try:
        db.record_payment(loan_id, period, amount, payment_method, notes)
    except Exception as e:
        print("⚠️ Could not record payment history:", str(e))

    return jsonify({'success': True})

# ===== API: ACTIVITIES =====
@app.route('/api/activities')
def api_activities():
    if 'username' not in session:
        return jsonify([])
    try:
        activities = db.get_activities(20)
        result = []
        for a in activities:
            # ===== បម្លែង datetime ទៅ string =====
            created = a.get('created_at', '')
            if hasattr(created, 'strftime'):
                created = created.strftime('%Y-%m-%d %H:%M:%S')
            else:
                created = str(created) if created else ''

            result.append({
                'id': a.get('id', ''),
                'action': a.get('action', ''),
                'description': a.get('description', ''),
                'status': a.get('status', 'Pending'),
                'created_at': created
            })
        return jsonify(result)
    except Exception as e:
        print(f"❌ Error in activities: {e}")
        return jsonify([])

# ============================================================
# ===== API: SETTINGS (USERS, OFFICERS, HOLIDAYS, PERMISSIONS) =====
# ============================================================

# ===== API: USERS =====
@app.route('/api/users', methods=['GET'])
def api_get_users():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    users = db.get_all_users()
    return jsonify([dict(user) for user in users])

@app.route('/api/users/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = db.get_user_by_id(user_id)
    if user:
        return jsonify(dict(user))
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/users', methods=['POST'])
def api_create_user():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    try:
        user_id = db.create_user(data)
        return jsonify({'success': True, 'id': user_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def api_update_user(user_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    try:
        db.update_user(user_id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        db.delete_user(user_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ===== API: OFFICERS =====
@app.route('/api/officers', methods=['GET'])
def api_get_officers():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    officers = db.get_all_officers()
    return jsonify([dict(o) for o in officers])

@app.route('/api/officers/<int:officer_id>', methods=['GET'])
def api_get_officer(officer_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    officer = db.get_officer_by_id(officer_id)
    if officer:
        return jsonify(dict(officer))
    return jsonify({'error': 'Officer not found'}), 404

@app.route('/api/officers', methods=['POST'])
def api_create_officer():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    try:
        officer_id = db.create_officer(data)
        return jsonify({'success': True, 'id': officer_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/officers/<int:officer_id>', methods=['PUT'])
def api_update_officer(officer_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    try:
        db.update_officer(officer_id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/officers/<int:officer_id>', methods=['DELETE'])
def api_delete_officer(officer_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        db.delete_officer(officer_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ===== API: HOLIDAYS =====
@app.route('/api/holidays', methods=['GET', 'POST'])
def api_holidays():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        holidays = db.get_holidays()
        return jsonify(holidays)
    else:
        data = request.json
        db.save_holidays(data.get('holidays', []))
        return jsonify({'success': True})

@app.route('/api/special_holidays', methods=['GET', 'POST'])
def api_special_holidays():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'GET':
        holidays = db.get_special_holidays()
        return jsonify(holidays)
    else:
        data = request.json
        try:
            holiday_id = db.add_special_holiday(data)
            return jsonify({'success': True, 'id': holiday_id})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/api/special_holidays/<int:holiday_id>', methods=['DELETE'])
def api_delete_special_holiday(holiday_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    db.delete_special_holiday(holiday_id)
    return jsonify({'success': True})

# ===== API: PERMISSIONS =====
@app.route('/api/permissions', methods=['POST'])
def api_save_permissions():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    db.save_permissions(data.get('role'), data.get('permissions'))
    return jsonify({'success': True})

@app.route('/api/permissions/<string:role>', methods=['GET'])
def api_get_permissions(role):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    permissions = db.get_permissions(role)
    return jsonify(permissions)

# ===== API: PAYMENTS =====
@app.route('/api/payments')
def api_payments():
    if 'username' not in session:
        return jsonify([])

    try:
        payments = db.get_payment_history()
        return jsonify(payments)
    except Exception as e:
        import traceback
        print("ERROR in api_payments:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment_history/<int:loan_id>')
def api_payment_history(loan_id):
    if 'username' not in session:
        return jsonify([])

    payments = db.get_payment_history_by_loan(loan_id)
    return jsonify(payments)

# ===== API: DISBURSEMENT =====
@app.route('/api/disbursement')
def api_disbursement():
    if 'username' not in session:
        return jsonify([])

    try:
        import re
        # ===== ទាញយក Activities ដែលជា collection_payment =====
        activities = list(db.activities_col.find(
            {'action': 'collection_payment'}
        ).sort('_id', -1).limit(100))

        result = []
        for p in activities:
            loan_id = p.get('loan_id')

            # ===== ទាញយកព័ត៌មានកម្ចី =====
            loan = None
            customer = None
            if loan_id:
                loan = db.loans_col.find_one({'_id': int(loan_id)})
                if loan:
                    customer = db.customers_col.find_one({'_id': loan.get('customer_id')})

            # ===== ទាញយកទឹកប្រាក់ពី description =====
            description = p.get('description', '')
            amount = 0
            currency = 'USD'

            # ពិនិត្យរូបិយប័ណ្ណ
            if '៛' in description:
                currency = 'KHR'
                match = re.search(r'៛\s*([0-9,]+)', description)
                if match:
                    amount = float(match.group(1).replace(',', ''))
            else:
                match = re.search(r'\$([0-9.]+)', description)
                if match:
                    amount = float(match.group(1))

            # ===== បង្កើត Result =====
            created_at = p.get('created_at')
            created_str = ''
            if hasattr(created_at, 'strftime'):
                created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            elif created_at:
                created_str = str(created_at)

            result.append({
                'id': p.get('_id'),
                'loan_id': loan_id,
                'loan_code': loan.get('loan_code', 'N/A') if loan else 'N/A',
                'customer_name': customer.get('name', 'មិនស្គាល់') if customer else 'មិនស្គាល់',
                'co_officer': loan.get('co_officer', '-') if loan else '-',
                'amount': amount,
                'currency': currency,
                'created_at': created_str,
                'status': p.get('status', 'Pending')
            })

        return jsonify(result)

    except Exception as e:
        import traceback
        print(f"❌ Error in /api/disbursement: {e}")
        print(traceback.format_exc())
        return jsonify([])  # ត្រឡប់ Array ទទេជំនួស Error

@app.route('/api/approve_disbursement', methods=['POST'])
def api_approve_disbursement():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    activity_ids = data.get('activity_ids', [])

    if not activity_ids:
        return jsonify({'error': 'No activities selected'}), 400

    try:
        approved_count = 0

        for activity_id in activity_ids:
            try:
                # ===== ពិនិត្យមើលថា Activity នេះមានស្រាប់ =====
                activity = db.activities_col.find_one({'_id': int(activity_id)})

                if activity and activity.get('status') == 'Pending':
                    db.activities_col.update_one(
                        {'_id': int(activity_id)},
                        {'$set': {
                            'status': 'Approved',
                            'updated_at': datetime.now()
                        }}
                    )
                    approved_count += 1
            except Exception as inner_e:
                print(f"⚠️ Error approving activity {activity_id}: {inner_e}")
                continue

        return jsonify({
            'success': True,
            'approved_count': approved_count,
            'message': f'បានអនុម័ត {approved_count} ការទូរទាត់'
        })

    except Exception as e:
        import traceback
        print(f"❌ Error in /api/approve_disbursement: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/edit_payment', methods=['POST'])
def api_edit_payment():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    activity_id = data.get('activity_id')
    loan_id = data.get('loan_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method')
    notes = data.get('notes')

    if not activity_id or not loan_id or not amount:
        return jsonify({'error': 'Missing data'}), 400

    conn = db.get_db_connection()
    cursor = conn.cursor()

    old_activity = conn.execute('''
        SELECT * FROM activities WHERE id = ?
    ''', (activity_id,)).fetchone()

    if not old_activity:
        conn.close()
        return jsonify({'error': 'មិនឃើញការទូរទាត់នេះទេ!'}), 404

    loan = conn.execute('''
        SELECT id, amount_paid, remaining_balance, loan_amount, total_interest
        FROM loans WHERE id = ?
    ''', (loan_id,)).fetchone()

    if not loan:
        conn.close()
        return jsonify({'error': 'មិនឃើញកម្ចីនេះទេ!'}), 404

    match = re.search(r'\$([0-9.]+)', old_activity['description'])
    old_amount = float(match.group(1)) if match else 0

    diff = amount - old_amount
    new_amount_paid = loan['amount_paid'] + diff
    new_remaining = loan['remaining_balance'] - diff

    if new_amount_paid < 0:
        new_amount_paid = 0
    if new_remaining < 0:
        new_remaining = 0

    cursor.execute('''
        UPDATE loans SET
            amount_paid = ?,
            remaining_balance = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_amount_paid, new_remaining, loan_id))

    new_description = f'បានប្រមូលប្រាក់ ${amount:.2f} តាមរយៈ {payment_method}'
    if notes:
        new_description += f', កំណត់ចំណាំ: {notes}'

    cursor.execute('''
        UPDATE activities SET
            description = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_description, activity_id))

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': f'បានកែប្រែការទូរទាត់ពី ${old_amount:.2f} ទៅ ${amount:.2f} រួចរាល់!'
    })

@app.route('/api/delete_payment', methods=['POST'])
def api_delete_payment():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    activity_id = data.get('activity_id')

    if not activity_id:
        return jsonify({'error': 'Missing activity_id'}), 400

    conn = db.get_db_connection()
    cursor = conn.cursor()

    activity = conn.execute('SELECT * FROM activities WHERE id = ?', (activity_id,)).fetchone()

    if not activity:
        conn.close()
        return jsonify({'error': 'មិនឃើញការទូរទាត់នេះទេ!'}), 404

    loan_id = activity['loan_id']

    loan = conn.execute('SELECT id, amount_paid, remaining_balance FROM loans WHERE id = ?', (loan_id,)).fetchone()

    import re
    match = re.search(r'\$([0-9.]+)', activity['description'])
    amount = float(match.group(1)) if match else 0

    if amount == 0:
        match_khr = re.search(r'៛\s*([0-9,]+)', activity['description'])
        if match_khr:
            amount_str = match_khr.group(1).replace(',', '')
            amount = float(amount_str)

    if loan:
        new_amount_paid = loan['amount_paid'] - amount
        new_remaining = loan['remaining_balance'] + amount
        if new_amount_paid < 0:
            new_amount_paid = 0

        cursor.execute('''
            UPDATE loans SET amount_paid = ?, remaining_balance = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_amount_paid, new_remaining, loan_id))

    cursor.execute('DELETE FROM activities WHERE id = ?', (activity_id,))

    period_match = re.search(r'វគ្គ\s*(\d+)', activity['description'])
    period = int(period_match.group(1)) if period_match else None

    if period:
        cursor.execute('DELETE FROM payment_history WHERE loan_id = ? AND period = ?', (loan_id, period))
    else:
        cursor.execute('DELETE FROM payment_history WHERE loan_id = ? ORDER BY id DESC LIMIT 1', (loan_id,))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'បានលុបការទូរទាត់រួចរាល់!'})

# ===== TEMPLATE FILTERS =====
@app.template_filter('format_currency')
def format_currency_filter(amount, currency='USD'):
    """Template filter សម្រាប់បង្ហាញរូបិយប័ណ្ណ"""
    if amount is None:
        amount = 0
    if currency == 'KHR':
        if amount == 0:
            return '៛ 0'
        return '៛ ' + '{:,.0f}'.format(round(amount / 100) * 100)
    else:
        return '$ ' + '{:,.2f}'.format(amount)

@app.route('/api/clean_orphan_data', methods=['POST'])
def api_clean_orphan_data():
    """API សម្រាប់សម្អាតទិន្នន័យដែលខូច"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = db.get_db_connection()
    cursor = conn.cursor()

    result = {
        'payment_history_orphan': 0,
        'payment_history_zero': 0,
        'payment_history_no_loan': 0,
        'activities_orphan': 0
    }

    try:
        cursor.execute('''
            DELETE FROM payment_history
            WHERE id IN (
                SELECT ph.id
                FROM payment_history ph
                LEFT JOIN activities a ON a.loan_id = ph.loan_id
                WHERE a.id IS NULL
            )
        ''')
        result['payment_history_orphan'] = cursor.rowcount

        cursor.execute('DELETE FROM payment_history WHERE amount = 0')
        result['payment_history_zero'] = cursor.rowcount

        cursor.execute('''
            DELETE FROM payment_history
            WHERE loan_id NOT IN (SELECT id FROM loans)
        ''')
        result['payment_history_no_loan'] = cursor.rowcount

        cursor.execute('''
            DELETE FROM activities
            WHERE loan_id NOT IN (SELECT id FROM loans) AND loan_id IS NOT NULL
        ''')
        result['activities_orphan'] = cursor.rowcount

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'សម្អាតទិន្នន័យរួចរាល់!',
            'result': result
        })

    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# ============================================================
# ===== REPORT ROUTES =====
# ============================================================

@app.route('/reports')
def reports():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('reports.html', username=session.get('full_name', session['username']))

# ===== API: REPORT SUMMARY =====
@app.route('/api/reports/summary')
def api_report_summary():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = db.get_db_connection()
    cursor = conn.cursor()

    # ===== ស្ថិតិទូទៅ =====
    customer_count = cursor.execute('SELECT COUNT(*) as count FROM customers').fetchone()['count']
    loan_count = cursor.execute('SELECT COUNT(*) as count FROM loans').fetchone()['count']
    active_loans = cursor.execute('''
        SELECT COUNT(*) as count FROM loans
        WHERE status IN ('Approved', 'Pending')
    ''').fetchone()['count']
    bad_loans = cursor.execute('''
        SELECT COUNT(*) as count FROM loans
        WHERE status = 'Bad Debt'
    ''').fetchone()['count']

    # ===== ទឹកប្រាក់សរុប (បែងចែកតាមរូបិយប័ណ្ណ) =====
    # ===== ទឹកប្រាក់កម្ចីសរុប =====
    total_amount_usd = cursor.execute('''
        SELECT SUM(loan_amount) as total FROM loans WHERE currency = 'USD'
    ''').fetchone()['total'] or 0

    total_amount_khr = cursor.execute('''
        SELECT SUM(loan_amount) as total FROM loans WHERE currency = 'KHR'
    ''').fetchone()['total'] or 0

    # ===== បំណុលសរុប =====
    total_debt_usd = cursor.execute('''
        SELECT SUM(remaining_balance) as total FROM loans WHERE currency = 'USD'
    ''').fetchone()['total'] or 0

    total_debt_khr = cursor.execute('''
        SELECT SUM(remaining_balance) as total FROM loans WHERE currency = 'KHR'
    ''').fetchone()['total'] or 0

    conn.close()

    return jsonify({
        'total_customers': customer_count,
        'total_loans': loan_count,
        'active_loans': active_loans,
        'bad_loans': bad_loans,
        'total_amount_usd': total_amount_usd,
        'total_amount_khr': total_amount_khr,
        'total_debt_usd': total_debt_usd,
        'total_debt_khr': total_debt_khr
    })
# ===== API: REPORT LOANS =====
@app.route('/api/reports/loans')
def api_report_loans():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    status = request.args.get('status', 'all')
    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')
    officer = request.args.get('officer', '')

    conn = db.get_db_connection()
    query = '''
        SELECT
            loans.*,
            customers.name as customer_name,
            customers.code as customer_code
        FROM loans
        LEFT JOIN customers ON loans.customer_id = customers.id
        WHERE 1=1
    '''
    params = []

    if status and status != 'all':
        query += ' AND loans.status = ?'
        params.append(status)

    if from_date:
        query += ' AND loans.loan_date >= ?'
        params.append(from_date)

    if to_date:
        query += ' AND loans.loan_date <= ?'
        params.append(to_date)

    if officer:
        query += ' AND loans.co_officer = ?'
        params.append(officer)

    query += ' ORDER BY loans.id DESC LIMIT 500'

    loans = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(l) for l in loans])

# ===== API: REPORT PAYMENTS =====
@app.route('/api/reports/payments')
def api_report_payments():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    method = request.args.get('method', 'all')
    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')

    conn = db.get_db_connection()

    query = '''
        SELECT
            a.id,
            a.loan_id,
            a.description,
            a.created_at,
            l.loan_code,
            l.currency,
            l.co_officer,
            c.name as customer_name
        FROM activities a
        LEFT JOIN loans l ON a.loan_id = l.id
        LEFT JOIN customers c ON l.customer_id = c.id
        WHERE a.action = 'collection_payment'
    '''
    params = []

    if from_date:
        query += ' AND a.created_at >= ?'
        params.append(from_date)

    if to_date:
        query += ' AND a.created_at <= ?'
        params.append(to_date)

    query += ' ORDER BY a.created_at DESC LIMIT 500'

    activities = conn.execute(query, params).fetchall()

    import re
    total_amount = 0
    total_count = 0
    cash_total = 0
    aba_total = 0
    payments = []

    for a in activities:
        match = re.search(r'\$([0-9.]+)', a['description'])
        amount = float(match.group(1)) if match else 0

        if amount == 0:
            match_khr = re.search(r'៛\s*([0-9,]+)', a['description'])
            if match_khr:
                amount_str = match_khr.group(1).replace(',', '')
                amount = float(amount_str)

        p_method = 'cash'
        if 'ABA' in a['description'] or 'aba' in a['description']:
            p_method = 'aba'
        elif 'ACLEDA' in a['description'] or 'acleda' in a['description']:
            p_method = 'acleda'

        if method != 'all' and p_method != method:
            continue

        total_amount += amount
        total_count += 1

        if p_method == 'cash':
            cash_total += amount
        elif p_method == 'aba':
            aba_total += amount

        payments.append({
            'id': a['id'],
            'loan_id': a['loan_id'],
            'loan_code': a['loan_code'] or 'N/A',
            'customer_name': a['customer_name'] or 'មិនស្គាល់',
            'co_officer': a['co_officer'] or '-',
            'amount': amount,
            'currency': a['currency'] or 'USD',
            'payment_method': p_method,
            'created_at': a['created_at']
        })

    conn.close()

    return jsonify({
        'total_amount': total_amount,
        'total_count': total_count,
        'cash_total': cash_total,
        'aba_total': aba_total,
        'payments': payments
    })

# ===== API: REPORT COLLECTION =====
@app.route('/api/reports/collection')
def api_report_collection():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    summary = db.get_collection_summary()
    return jsonify(summary)

# ===== API: REPORT CUSTOMERS =====
@app.route('/api/reports/customers')
def api_report_customers():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = db.get_db_connection()

    customers = conn.execute('''
        SELECT
            c.*,
            COUNT(l.id) as loan_count,
            SUM(l.remaining_balance) as total_debt
        FROM customers c
        LEFT JOIN loans l ON c.id = l.customer_id
        GROUP BY c.id
        ORDER BY c.id DESC
        LIMIT 500
    ''').fetchall()

    total = conn.execute('SELECT COUNT(*) as count FROM customers').fetchone()['count']
    male = conn.execute('SELECT COUNT(*) as count FROM customers WHERE gender = "ប្រុស" OR gender = "male"').fetchone()['count']
    female = conn.execute('SELECT COUNT(*) as count FROM customers WHERE gender = "ស្រី" OR gender = "female"').fetchone()['count']

    from datetime import datetime, timedelta
    date_30_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    new_customers = conn.execute('''
        SELECT COUNT(*) as count FROM customers
        WHERE created_at >= ?
    ''', (date_30_ago,)).fetchone()['count']

    conn.close()

    return jsonify({
        'total': total,
        'male': male,
        'female': female,
        'new_customers': new_customers,
        'customers': [dict(c) for c in customers]
    })

# ===== API: REPORT INCOME =====
@app.route('/api/reports/income')
def api_report_income():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')

    conn = db.get_db_connection()

    query = '''
        SELECT SUM(total_interest) as total_interest
        FROM loans
        WHERE 1=1
    '''
    params = []

    if from_date:
        query += ' AND created_at >= ?'
        params.append(from_date)

    if to_date:
        query += ' AND created_at <= ?'
        params.append(to_date)

    result = conn.execute(query, params).fetchone()
    total_interest = result['total_interest'] if result and result['total_interest'] else 0

    penalty_query = '''
        SELECT SUM(penalty) as total_penalty
        FROM payment_history
        WHERE 1=1
    '''
    penalty_params = []

    if from_date:
        penalty_query += ' AND created_at >= ?'
        penalty_params.append(from_date)

    if to_date:
        penalty_query += ' AND created_at <= ?'
        penalty_params.append(to_date)

    penalty_result = conn.execute(penalty_query, penalty_params).fetchone()
    total_penalty = penalty_result['total_penalty'] if penalty_result and penalty_result['total_penalty'] else 0

    total_expense = 0

    transactions = []

    if total_interest > 0:
        transactions.append({
            'type': 'ចំណូល',
            'amount': total_interest,
            'date': from_date or 'សរុប',
            'note': 'ការប្រាក់ពីកម្ចី'
        })

    if total_penalty > 0:
        transactions.append({
            'type': 'ចំណូល',
            'amount': total_penalty,
            'date': from_date or 'សរុប',
            'note': 'ពិន័យពីការយឺត'
        })

    conn.close()

    return jsonify({
        'total_interest': total_interest,
        'total_penalty': total_penalty,
        'total_expense': total_expense,
        'transactions': transactions
    })

# ===== API: SUMMARY REPORT =====
@app.route('/api/reports/summary_report')
def api_summary_report():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')

    if not from_date or not to_date:
        return jsonify({'error': 'Missing date range'}), 400

    conn = db.get_db_connection()
    cursor = conn.cursor()

    new_customers = cursor.execute('''
        SELECT COUNT(*) as count FROM customers
        WHERE created_at BETWEEN ? AND ?
    ''', (from_date, to_date + ' 23:59:59')).fetchone()['count']

    loan_disbursed = cursor.execute('''
        SELECT loan_amount, currency FROM loans
        WHERE created_at BETWEEN ? AND ?
    ''', (from_date, to_date + ' 23:59:59')).fetchall()

    total_loan_disbursed_usd = 0
    total_loan_disbursed_khr = 0

    for row in loan_disbursed:
        amount = row['loan_amount'] or 0
        currency = row['currency'] or 'USD'
        if currency == 'USD':
            total_loan_disbursed_usd += amount
        else:
            total_loan_disbursed_khr += amount

    payments = cursor.execute('''
        SELECT amount, payment_method FROM payment_history
        WHERE created_at BETWEEN ? AND ?
    ''', (from_date, to_date + ' 23:59:59')).fetchall()

    total_collected_usd = 0
    total_collected_khr = 0
    interest_collected_usd = 0
    interest_collected_khr = 0
    penalty_collected_usd = 0
    penalty_collected_khr = 0
    aba_total_usd = 0
    aba_total_khr = 0
    acleda_total_usd = 0
    acleda_total_khr = 0

    for row in payments:
        amount = row['amount'] or 0
        method = row['payment_method'] or 'cash'

        total_collected_usd += amount

        if method == 'aba':
            aba_total_usd += amount
        elif method == 'acleda':
            acleda_total_usd += amount
        elif method == 'penalty':
            penalty_collected_usd += amount
        else:
            interest_collected_usd += amount

    expenses = cursor.execute('''
        SELECT name, amount FROM expenses
        WHERE created_at BETWEEN ? AND ?
    ''', (from_date, to_date + ' 23:59:59')).fetchall()

    total_expense_usd = 0
    expense_list = []
    for exp in expenses:
        total_expense_usd += exp['amount'] or 0
        expense_list.append({'name': exp['name'], 'amount': exp['amount'] or 0})

    conn.close()

    return jsonify({
        'new_customers': new_customers,
        'total_loan_disbursed_usd': total_loan_disbursed_usd,
        'total_loan_disbursed_khr': total_loan_disbursed_khr,
        'total_collected_usd': total_collected_usd,
        'total_collected_khr': total_collected_khr,
        'interest_collected_usd': interest_collected_usd,
        'interest_collected_khr': interest_collected_khr,
        'penalty_collected_usd': penalty_collected_usd,
        'penalty_collected_khr': penalty_collected_khr,
        'aba_total_usd': aba_total_usd,
        'aba_total_khr': aba_total_khr,
        'acleda_total_usd': acleda_total_usd,
        'acleda_total_khr': acleda_total_khr,
        'total_expense_usd': total_expense_usd,
        'expenses': expense_list
    })

# ============================================================
# ===== EXPENSES API ROUTES =====
# ============================================================

@app.route('/api/expenses', methods=['GET'])
def api_get_expenses():
    """ទាញយកចំណាយទាំងអស់"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from_date = request.args.get('from', '')
        to_date = request.args.get('to', '')

        if from_date and to_date:
            expenses = db.get_expenses_by_date_range(from_date, to_date)
        else:
            expenses = db.get_all_expenses()

        return jsonify(expenses)
    except Exception as e:
        print(f"Error in api_get_expenses: {e}")
        return jsonify([])

@app.route('/api/expenses/<int:expense_id>', methods=['GET'])
def api_get_expense(expense_id):
    """ទាញយកចំណាយតាម ID"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        expense = db.get_expense_by_id(expense_id)
        if not expense:
            return jsonify({'error': 'មិនឃើញចំណាយនេះទេ!'}), 404
        return jsonify(expense)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses', methods=['POST'])
def api_create_expense():
    """បង្កើតចំណាយថ្មី"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.json
        if not data.get('name') or not data.get('amount'):
            return jsonify({'error': 'សូមបំពេញឈ្មោះ និងចំនួនទឹកប្រាក់!'}), 400

        expense_id = db.create_expense(data)
        db.log_activity(None, None, 'create_expense', f'បានបង្កើតចំណាយ: {data["name"]} - ${data["amount"]}', user_id=session.get('user_id'))
        return jsonify({'success': True, 'id': expense_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
def api_update_expense(expense_id):
    """កែប្រែចំណាយ"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.json
        if not data.get('name') or not data.get('amount'):
            return jsonify({'error': 'សូមបំពេញឈ្មោះ និងចំនួនទឹកប្រាក់!'}), 400

        db.update_expense(expense_id, data)
        db.log_activity(None, None, 'update_expense', f'បានកែប្រែចំណាយ: {data["name"]}', user_id=session.get('user_id'))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def api_delete_expense(expense_id):
    """លុបចំណាយ"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        expense = db.get_expense_by_id(expense_id)
        if expense:
            db.delete_expense(expense_id)
            db.log_activity(None, None, 'delete_expense', f'បានលុបចំណាយ: {expense["name"]}', user_id=session.get('user_id'))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/categories', methods=['GET'])
def api_get_expense_categories():
    """ទាញយកប្រភេទចំណាយទាំងអស់"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        categories = db.get_expense_categories()
        return jsonify(categories)
    except Exception as e:
        return jsonify([])

# ============================================================
# ===== PAWN ROUTES =====
# ============================================================

@app.route('/pawn')
def pawn():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('pawn.html', username=session.get('full_name', session['username']))

@app.route('/api/pawns', methods=['GET'])
def api_get_pawns():
    if 'username' not in session:
        return jsonify([])

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status', '')

    pawns = db.get_pawns_paginated(page, per_page, status)
    return jsonify([dict(p) for p in pawns])

@app.route('/api/pawns/count')
def api_pawns_count():
    if 'username' not in session:
        return jsonify({'count': 0})
    status = request.args.get('status', '')
    count = db.count_pawns(status)
    return jsonify({'count': count})

@app.route('/api/pawns/<int:pawn_id>', methods=['GET'])
def api_get_pawn(pawn_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    pawn = db.get_pawn_by_id(pawn_id)
    if not pawn:
        return jsonify({'error': 'មិនឃើញបញ្ចាំនេះទេ!'}), 404
    return jsonify(dict(pawn))

@app.route('/api/pawns', methods=['POST'])
def api_create_pawn():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    if not data.get('customer_id') or not data.get('item_name') or not data.get('loan_amount'):
        return jsonify({'error': 'សូមបំពេញព័ត៌មានឲ្យបានពេញលេញ!'}), 400

    try:
        pawn_id = db.create_pawn(data)
        db.log_activity(data['customer_id'], None, 'create_pawn', f'បានបង្កើតបញ្ចាំ: {data["item_name"]} - ${data["loan_amount"]}', user_id=session.get('user_id'))
        return jsonify({'success': True, 'id': pawn_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pawns/<int:pawn_id>/redeem', methods=['POST'])
def api_redeem_pawn(pawn_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    amount = data.get('amount')

    if not amount or amount <= 0:
        return jsonify({'error': 'សូមបញ្ចូលទឹកប្រាក់ឲ្យបានត្រឹមត្រូវ!'}), 400

    try:
        result = db.redeem_pawn(pawn_id, amount)
        pawn = db.get_pawn_by_id(pawn_id)
        db.log_activity(pawn['customer_id'], None, 'redeem_pawn', f'បានលោះបញ្ចាំ: {pawn["item_name"]} - ${amount}', user_id=session.get('user_id'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pawns/<int:pawn_id>', methods=['DELETE'])
def api_delete_pawn(pawn_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        pawn = db.get_pawn_by_id(pawn_id)
        if pawn:
            db.delete_pawn(pawn_id)
            db.log_activity(pawn['customer_id'], None, 'delete_pawn', f'បានលុបបញ្ចាំ: {pawn["item_name"]}', user_id=session.get('user_id'))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pawns/<int:pawn_id>/forfeit', methods=['POST'])
def api_forfeit_pawn(pawn_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        pawn = db.get_pawn_by_id(pawn_id)
        if pawn:
            db.update_pawn_status(pawn_id, 'Forfeited')
            db.log_activity(pawn['customer_id'], None, 'forfeit_pawn', f'បានបោះបង់បញ្ចាំ: {pawn["item_name"]}', user_id=session.get('user_id'))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pawns/<int:pawn_id>', methods=['PUT'])
def api_update_pawn(pawn_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    try:
        db.update_pawn(pawn_id, data)
        db.log_activity(data['customer_id'], None, 'update_pawn', f'បានកែប្រែបញ្ចាំ: {data["item_name"]}', user_id=session.get('user_id'))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# ===== AUDIT ROUTES =====
# ============================================================

@app.route('/audit')
def audit():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('audit.html', username=session.get('full_name', session['username']))

@app.route('/api/audit')
def api_audit():
    if 'username' not in session:
        return jsonify([])

    limit = request.args.get('limit', 100, type=int)
    action = request.args.get('action', '')
    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')
    user = request.args.get('user', '')

    conn = db.get_db_connection()
    query = '''
        SELECT
            a.*,
            u.username as user_name,
            u.full_name,
            c.name as customer_name,
            l.loan_code
        FROM activities a
        LEFT JOIN users u ON a.user_id = u.id
        LEFT JOIN customers c ON a.customer_id = c.id
        LEFT JOIN loans l ON a.loan_id = l.id
        WHERE 1=1
    '''
    params = []

    if action:
        query += ' AND a.action = ?'
        params.append(action)

    if from_date:
        query += ' AND a.created_at >= ?'
        params.append(from_date + ' 00:00:00')

    if to_date:
        query += ' AND a.created_at <= ?'
        params.append(to_date + ' 23:59:59')

    if user:
        query += ' AND u.username LIKE ?'
        params.append(f'%{user}%')

    query += ' ORDER BY a.created_at DESC LIMIT ?'
    params.append(limit)

    activities = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(a) for a in activities])

@app.route('/api/audit/actions')
def api_audit_actions():
    if 'username' not in session:
        return jsonify([])

    conn = db.get_db_connection()
    actions = conn.execute('''
        SELECT DISTINCT action FROM activities ORDER BY action
    ''').fetchall()
    conn.close()

    return jsonify([a['action'] for a in actions])

@app.route('/api/dashboard_stats')
def api_dashboard_stats():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        stats = db.get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"❌ Error in dashboard_stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'total_loans': 0,
            'active_loans': 0,
            'bad_loans': 0,
            'total_amount_usd': 0,
            'total_amount_khr': 0,
            'total_debt_usd': 0,
            'total_debt_khr': 0
        })

# ============================================================
# ===== CHANGE CO OFFICER API =====
# ============================================================

@app.route('/api/change_co', methods=['POST'])
def api_change_co():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    loan_id = data.get('loan_id')
    new_officer = data.get('new_officer')
    notes = data.get('notes', '')

    if not loan_id or not new_officer:
        return jsonify({'error': 'Missing loan_id or new_officer'}), 400

    conn = db.get_db_connection()
    cursor = conn.cursor()

    # ===== ទាញយកព័ត៌មានកម្ចី =====
    loan = cursor.execute('''
        SELECT id, loan_code, co_officer, customer_id
        FROM loans WHERE id = ?
    ''', (loan_id,)).fetchone()

    if not loan:
        conn.close()
        return jsonify({'error': 'មិនឃើញកម្ចីនេះទេ!'}), 404

    old_officer = loan['co_officer'] or 'គ្មាន'

    # ===== ធ្វើបច្ចុប្បន្នភាព CO =====
    cursor.execute('''
        UPDATE loans
        SET co_officer = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_officer, loan_id))

    # ===== កត់ត្រាសកម្មភាព =====
    db.log_activity(
        loan['customer_id'],
        loan_id,
        'change_co',
        f'បានផ្លាស់ប្តូរ CO ពី "{old_officer}" ទៅ "{new_officer}" (កំណត់ចំណាំ: {notes})',
        user_id=session.get('user_id')
    )

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': f'បានផ្លាស់ប្តូរ CO ពី "{old_officer}" ទៅ "{new_officer}" រួចរាល់!'
    })

@app.route('/api/loans/<int:loan_id>')
def api_get_loan(loan_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    loan = db.get_loan_by_id(loan_id)
    if not loan:
        return jsonify({'error': 'មិនឃើញកម្ចីនេះទេ!'}), 404

    # ===== បន្ថែមព័ត៌មានអតិថិជន =====
    customer = db.get_customer_by_id(loan.get('customer_id'))
    if customer:
        loan['customer_name'] = customer.get('name', 'មិនស្គាល់')
        loan['customer_code'] = customer.get('code', '')
        loan['customer_phone'] = customer.get('phone', '')
        loan['customer_gender'] = customer.get('gender', '')
        loan['customer_address'] = customer.get('address', '')
    else:
        loan['customer_name'] = 'មិនស្គាល់'
        loan['customer_code'] = ''
        loan['customer_phone'] = ''
        loan['customer_gender'] = ''
        loan['customer_address'] = ''

    return jsonify(loan)

@app.route('/api/dashboard_charts')
def api_dashboard_charts():
    """ទាញយកទិន្នន័យសម្រាប់ Charts ក្នុង Dashboard"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        conn_data = db.get_dashboard_charts_data()
        return jsonify(conn_data)
    except Exception as e:
        print(f"❌ Error in dashboard_charts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'loans_by_status': {},
            'loans_by_currency': {},
            'monthly_loans': [],
            'monthly_collections': []
        })

# ============================================================
# ===== DASHBOARD ROUTES ថ្មី =====
# ============================================================

@app.route('/api/dashboard_full_stats')
def api_dashboard_full_stats():
    """ទាញយកស្ថិតិពេញលេញ"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        stats = db.get_dashboard_full_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"❌ Error in dashboard_full_stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/calendar_data')
def api_calendar_data():
    """ទាញយកទិន្នន័យ Calendar"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    from datetime import datetime
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    try:
        data = db.get_calendar_data(year, month)
        return jsonify(data)
    except Exception as e:
        print(f"❌ Error in calendar_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================================
# ===== RUN APP =====
# ============================================================

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, threaded=True, host='0.0.0.0', port=port)
