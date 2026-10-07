from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from bson import ObjectId          # ✅ បន្ថែមបន្ទាត់នេះ
import database as db
import re
import pytz
import os


# ===== SET TIMEZONE TO CAMBODIA =====
CAMBODIA_TZ = pytz.timezone('Asia/Phnom_Penh')


def get_cambodia_time():
    """ទាញយកពេលវេលាបច្ចុប្បន្នតាមម៉ោងកម្ពុជា"""
    return datetime.now(CAMBODIA_TZ)


def get_cambodia_date():
    """ទាញយកថ្ងៃបច្ចុប្បន្នតាមម៉ោងកម្ពុជា"""
    return datetime.now(CAMBODIA_TZ).date()


# ===== CREATE FLASK APP =====
import os
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-it-12345')

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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username')
    password = request.form.get('password')
    user = db.get_user_by_username(username)
    if user and user['password'] == password:
        session['username'] = username
        session['user_id'] = user['id']
        session['full_name'] = user['full_name']
        session['role'] = user['role']
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
    return render_template('collection.html', username=session.get('full_name', session['username']))


@app.route('/collection_good')
def collection_good():
    return redirect(url_for('collection', tab='good'))


@app.route('/collection_late')
def collection_late():
    return redirect(url_for('collection', tab='late'))


@app.route('/collection_bad')
def collection_bad():
    return redirect(url_for('collection', tab='bad'))


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
    session.pop('role', None)
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
            'name': 'មិនស្គាល់', 'code': '', 'gender': '', 'phone': '',
            'address': '', 'dob': '', 'id_card': '',
            'guarantor_name': '', 'guarantor_gender': '', 'guarantor_id_card': '',
            'guarantor_dob': '', 'guarantor_phone': '', 'guarantor_address': '',
            'relation': ''
        }

    schedule_data = []
    if loan.get('duration_num') and loan['duration_num'] > 0:
        total_payment = (loan.get('loan_amount', 0) or 0) + (loan.get('total_interest', 0) or 0)
        daily_payment = total_payment / loan['duration_num']

        if loan.get('currency') == 'KHR':
            daily_payment = round(daily_payment / 100) * 100
        else:
            daily_payment = round(daily_payment, 2)

        schedule_data = [{'payment': daily_payment, 'period': 1}]

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
    # ===== គណនា Schedule តាម calc_type =====
    # ============================================================
    schedule_data = []
    loan_amount = float(loan.get('loan_amount', 0))
    interest_rate = float(loan.get('interest_rate', 0))
    duration_num = int(loan.get('duration_num', 0))
    currency = loan.get('currency', 'USD')
    calc_type = int(loan.get('calc_type', 1))

    if duration_num > 0 and loan_amount > 0:
        rate_decimal = interest_rate / 100

        try:
            start_date = datetime.strptime(loan['loan_date'], '%Y-%m-%d').date()
        except:
            start_date = get_cambodia_date()

        # ===== ១. រំលោះបង់ថេរ =====
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
                    'period': i, 'payment': payment, 'interest': interest,
                    'principal': principal, 'balance': max(balance, 0),
                    'due_date': due_date.strftime('%Y-%m-%d')
                })

        # ===== ២. ដើមថេរ ការថេរ =====
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
                    'period': i, 'payment': payment, 'interest': interest,
                    'principal': principal, 'balance': max(balance, 0),
                    'due_date': due_date.strftime('%Y-%m-%d')
                })

        # ===== ៣. បង់តែការ បង់ថយ =====
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
                    'period': i, 'payment': payment, 'interest': interest,
                    'principal': principal, 'balance': max(balance, 0),
                    'due_date': due_date.strftime('%Y-%m-%d')
                })

        # ===== ៤. បង់តែការប្រាក់ =====
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
                    'period': i, 'payment': payment, 'interest': interest,
                    'principal': principal, 'balance': balance,
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

    user_role = session.get('role', 'user')
    username = session.get('username', '')

    # ===== CO ឃើញតែអតិថិជនដែលខ្លួនទទួលខុសត្រូវ =====
    if user_role == 'officer':
        # ===== ទាញយកបញ្ជី customer_id ពី loans ដែល co_officer = username =====
        loans = list(db.loans_col.find({'co_officer': username}, {'customer_id': 1}))
        customer_ids = list(set([l.get('customer_id') for l in loans if l.get('customer_id')]))

        if not customer_ids:
            return jsonify([])

        # ===== ច្រោះអតិថិជនតាម customer_ids =====
        query = {'_id': {'$in': customer_ids}}
        if search:
            regex = {'$regex': search, '$options': 'i'}
            query['$or'] = [
                {'name': regex}, {'code': regex},
                {'phone': regex}, {'address': regex}
            ]

        skip = (page - 1) * per_page
        customers = list(db.customers_col.find(query).sort('_id', -1).skip(skip).limit(per_page))

        customers_data = []
        for c in customers:
            customers_data.append({
                'id': c['_id'], 'code': c.get('code', ''), 'name': c.get('name', ''),
                'gender': c.get('gender', ''), 'phone': c.get('phone', ''),
                'id_card': c.get('id_card', ''), 'address': c.get('address', ''),
                'guarantor_name': c.get('guarantor_name', ''),
                'guarantor_gender': c.get('guarantor_gender', ''),
                'guarantor_id_card': c.get('guarantor_id_card', ''),
                'guarantor_address': c.get('guarantor_address', ''),
                'guarantor_phone': c.get('guarantor_phone', ''),
                'relation': c.get('relation', ''),
                'dob': c.get('dob', ''), 'guarantor_dob': c.get('guarantor_dob', '')
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
            'calc_type': l.get('calc_type', 1),
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
            'calc_type': l.get('calc_type', 1),
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

    schedule = []
    rate_decimal = interest_rate / 100
    total_interest = 0
    total_payment = 0
    daily_payment = 0

    # ===== ១. រំលោះបង់ថេរ =====
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
            total_interest += interest
            total_payment += payment

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
                'period': i, 'payment': payment, 'interest': interest,
                'principal': principal, 'balance': max(balance, 0),
                'due_date': due_date.strftime('%Y-%m-%d')
            })

    # ===== ២. ដើមថេរ ការថេរ =====
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

            schedule.append({
                'period': i, 'payment': payment, 'interest': interest,
                'principal': principal, 'balance': max(balance, 0),
                'due_date': due_date.strftime('%Y-%m-%d')
            })

    # ===== ៣. បង់តែការ បង់ថយ =====
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
            total_interest += interest
            total_payment += payment

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
                'period': i, 'payment': payment, 'interest': interest,
                'principal': principal, 'balance': max(balance, 0),
                'due_date': due_date.strftime('%Y-%m-%d')
            })

    # ===== ៤. បង់តែការប្រាក់ =====
    elif calc_type == 4:
        daily_interest = loan_amount * rate_decimal
        total_interest = daily_interest * duration_num
        total_payment = loan_amount + total_interest
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

            schedule.append({
                'period': i, 'payment': payment, 'interest': interest,
                'principal': principal, 'balance': balance,
                'due_date': due_date.strftime('%Y-%m-%d')
            })

    service_amount = loan_amount * (service_fee / 100)

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

    loan_amount = float(data.get('loan_amount', 0))
    interest_rate = float(data.get('interest_rate', 0))
    duration_num = int(data.get('duration_num', 0))
    currency = data.get('currency', 'USD')

    total_interest = loan_amount * (interest_rate / 100) * duration_num
    total_amount = loan_amount + total_interest

    if currency == 'KHR':
        total_interest = round(total_interest / 100) * 100
        total_amount = round(total_amount / 100) * 100
    else:
        total_interest = round(total_interest, 2)
        total_amount = round(total_amount, 2)

    data['total_interest'] = total_interest
    data['total_amount'] = total_amount
    data['remaining_balance'] = total_amount
    data['amount_paid'] = 0

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

@app.route('/api/collection/customer/<int:customer_id>')
def api_collection_customer(customer_id):
    """ទាញយកកម្ចីទាំងអស់របស់អតិថិជន សម្រាប់ការទូរទាត់"""
    if 'username' not in session:
        return jsonify([])

    try:
        # ===== ទាញយកកម្ចីទាំងអស់របស់អតិថិជន =====
        loans = list(db.loans_col.find({
            'customer_id': int(customer_id),
            'status': {'$in': ['Approved', 'Pending', 'Bad Debt']},
            'remaining_balance': {'$gt': 0}
        }).sort('_id', -1))

        today = db.get_cambodia_date()
        result = []

        for loan in loans:
            customer = db.customers_col.find_one({'_id': loan.get('customer_id')}) or {}

            # ===== គណនា days_overdue =====
            days_overdue = 0
            days_to_pay = 0

            loan_date_str = loan.get('loan_date', '')
            if loan_date_str:
                try:
                    loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
                    days_diff = (today - loan_date).days
                    if days_diff <= 0:
                        days_overdue = 0
                        days_to_pay = 0
                    else:
                        days_overdue = max(days_diff - 1, 0)
                        days_to_pay = days_diff
                except:
                    pass

            # ===== គណនាប្រាក់ =====
            duration_num = loan.get('duration_num', 1) or 1
            loan_amount = loan.get('loan_amount', 0)
            total_interest = loan.get('total_interest', 0)
            total_amount = loan_amount + total_interest
            daily_payment = total_amount / duration_num
            daily_principal = loan_amount / duration_num
            daily_interest = total_interest / duration_num

            total_due = daily_payment * days_to_pay
            total_principal = daily_principal * days_to_pay
            total_interest_due = daily_interest * days_to_pay

            amount_paid = loan.get('amount_paid', 0) or 0
            total_due = total_due - amount_paid

            remaining_balance = loan.get('remaining_balance', 0) or 0
            if remaining_balance < total_due:
                total_due = remaining_balance
                if (daily_payment * days_to_pay) > 0:
                    ratio = total_due / (daily_payment * days_to_pay)
                    total_principal = total_principal * ratio
                    total_interest_due = total_interest_due * ratio
                else:
                    total_principal = 0
                    total_interest_due = 0

            # ===== បង្គត់តម្លៃ =====
            currency = loan.get('currency', 'USD')
            if currency == 'KHR':
                total_due = round(total_due / 100) * 100
                total_principal = round(total_principal / 100) * 100
                total_interest_due = round(total_interest_due / 100) * 100
            else:
                total_due = round(total_due, 2)
                total_principal = round(total_principal, 2)
                total_interest_due = round(total_interest_due, 2)

            result.append({
                'id': loan['_id'],
                'loan_code': loan.get('loan_code', ''),
                'customer_name': customer.get('name', ''),
                'loan_amount': loan_amount,
                'currency': currency,
                'total_interest': total_interest,
                'amount_paid': amount_paid,
                'remaining_balance': remaining_balance,
                'days_overdue': days_overdue,
                'total_due': max(total_due, 0),
                'principal': max(total_principal, 0),
                'interest': max(total_interest_due, 0),
                'status': loan.get('status', 'Pending'),
                'penalty': 0
            })

        return jsonify(result)

    except Exception as e:
        import traceback
        print(f"❌ Error in api_collection_customer: {e}")
        print(traceback.format_exc())
        return jsonify([])

@app.route('/api/collection/count/<string:type>')
def api_collection_count(type):
    if 'username' not in session:
        return jsonify({'count': 0})
    try:
        loans = db.get_collection_loans(type, 1, 10000)
        return jsonify({'count': len(loans)})
    except:
        return jsonify({'count': 0})


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
    payment_date = data.get('payment_date', '')

    if not loan_id or not amount:
        return jsonify({'error': 'Missing data'}), 400

    loan = db.get_loan_by_id(loan_id)
    if not loan:
        return jsonify({'error': 'មិនឃើញកម្ចីនេះទេ!'}), 404

    try:
        loan_date = datetime.strptime(loan['loan_date'], '%Y-%m-%d').date()
        today = get_cambodia_date()
        period = (today - loan_date).days + 1
    except:
        period = 1

    total_paid = (loan.get('amount_paid', 0) or 0) + amount
    remaining = (loan.get('remaining_balance', 0) or 0) - amount

    if penalty > 0:
        remaining = remaining + penalty

    status = loan['status']
    if remaining <= 0:
        status = 'Completed'
        remaining = 0

    db.update_loan_payment(loan_id, total_paid, remaining, status)

    # ===== បង្កើត description ត្រឹមត្រូវ =====
    currency = loan.get('currency', 'USD')
    if currency == 'KHR':
        amount_str = f'៛ {round(amount/100)*100:,.0f}'
    else:
        amount_str = f'${amount:.2f}'

    db.log_activity(
        loan['customer_id'],
        loan_id,
        'collection_payment',
        f'បានប្រមូលប្រាក់ {amount_str} តាមរយៈ {payment_method}',
        user_id=session.get('user_id')
    )

    # ===== រក្សាទុកក្នុង payment_history =====
    try:
        db.record_payment(
            loan_id, period, amount, payment_method, notes,
            payment_date=payment_date or get_cambodia_date().strftime('%Y-%m-%d'),
            penalty=penalty,
            currency=currency
        )
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
# ===== API: PAYMENTS =====
@app.route('/api/payments')
def api_payments():
    """ទាញយកប្រវត្តិទូរទាត់ថ្មីៗ"""
    if 'username' not in session:
        return jsonify([])

    try:
        payments = db.get_payment_history()
        result = []
        for p in payments:
            doc = dict(p) if not isinstance(p, dict) else p
            
            # ===== បំប្លែង ObjectId ទៅ string =====
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
                doc['id'] = doc['_id']
            
            # ===== Format កាលបរិច្ឆេទ =====
            created = doc.get('created_at')
            if hasattr(created, 'strftime'):
                doc['created_at'] = created.strftime('%Y-%m-%d %H:%M:%S')
            elif created:
                doc['created_at'] = str(created)
            else:
                doc['created_at'] = ''
            
            result.append(doc)
        
        return jsonify(result)
    except Exception as e:
        import traceback
        print("ERROR in api_payments:", str(e))
        print(traceback.format_exc())
        return jsonify([])


# ===== API: LOAN PAYMENTS (សម្រាប់ Modal មើលប្រវត្តិ) =====
@app.route('/api/loan_payments/<loan_id>')
def api_loan_payments(loan_id):
    """ទាញយកប្រវត្តិទូរទាត់ទាំងអស់នៃកម្ចីជាក់លាក់"""
    if 'username' not in session:
        return jsonify([])

    try:
        # ===== ស្វែងរកតាម loan_id (គាំទ្រទាំង int និង string) =====
        queries = [
            {'loan_id': loan_id},
            {'loan_id': int(loan_id) if str(loan_id).isdigit() else loan_id},
        ]
        
        # បើ loan_id ជា ObjectId
        try:
            queries.append({'loan_id': ObjectId(loan_id)})
        except:
            pass

        payments = []
        for q in queries:
            try:
                found = list(db.payment_history_col.find(q).sort('created_at', -1))
                if found:
                    payments = found
                    break
            except Exception:
                continue

        # ===== បើរកមិនឃើញក្នុង payment_history → ព្យាយាមក្នុង activities =====
        if not payments:
            try:
                activities = list(db.activities_col.find({
                    'loan_id': int(loan_id) if str(loan_id).isdigit() else loan_id,
                    'action': 'collection_payment'
                }).sort('_id', -1))
                
                for a in activities:
                    description = a.get('description', '')
                    amount = 0
                    currency = 'USD'
                    
                    # ទាញចំនួនពី description
                    match = re.search(r'\$([0-9.]+)', description)
                    if match:
                        amount = float(match.group(1))
                    else:
                        match_khr = re.search(r'៛\s*([0-9,]+)', description)
                        if match_khr:
                            amount = float(match_khr.group(1).replace(',', ''))
                            currency = 'KHR'
                    
                    # ទាញ method
                    method = 'cash'
                    if 'ABA' in description:
                        method = 'aba'
                    elif 'ACLEDA' in description:
                        method = 'acleda'
                    elif 'WING' in description:
                        method = 'wing'
                    
                    payments.append({
                        '_id': str(a.get('_id')),
                        'id': str(a.get('_id')),
                        'loan_id': a.get('loan_id'),
                        'amount': amount,
                        'currency': currency,
                        'payment_method': method,
                        'penalty': 0,
                        'notes': '',
                        'payment_date': a.get('created_at').strftime('%Y-%m-%d') if hasattr(a.get('created_at'), 'strftime') else '',
                        'created_at': a.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if hasattr(a.get('created_at'), 'strftime') else str(a.get('created_at', ''))
                    })
            except Exception as e:
                print(f"⚠️ Could not fallback to activities: {e}")

        # ===== បំប្លែង ObjectId និង Format កាលបរិច្ឆេទ =====
        result = []
        for p in payments:
            doc = dict(p) if not isinstance(p, dict) else p
            
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
                doc['id'] = doc['_id']
            
            created = doc.get('created_at')
            if hasattr(created, 'strftime'):
                doc['created_at'] = created.strftime('%Y-%m-%d %H:%M:%S')
            elif created:
                doc['created_at'] = str(created)
            
            # បើគ្មាន payment_date ប្រើ created_at
            if not doc.get('payment_date') and doc.get('created_at'):
                doc['payment_date'] = doc['created_at'].split(' ')[0]
            
            result.append(doc)
        
        return jsonify(result)

    except Exception as e:
        import traceback
        print(f"❌ Error in api_loan_payments: {e}")
        print(traceback.format_exc())
        return jsonify([])


# ===== API: PAYMENT HISTORY (ជំនួស version ចាស់) =====
@app.route('/api/payment_history/<int:loan_id>')
def api_payment_history(loan_id):
    """API ជំនួស — ហៅ api_loan_payments ដូចគ្នា"""
    return api_loan_payments(loan_id)


# ===== API: PAYMENTS BY LOAN (ជំនួស version ចាស់ដែលមាន ObjectId ខូច) =====
@app.route('/api/payments/loan/<loan_id>')
def get_payments_by_loan(loan_id):
    """API ជំនួស — ដូច api_loan_payments"""
    return api_loan_payments(loan_id)


# ===== API: DISBURSEMENT =====
@app.route('/api/disbursement')
def api_disbursement():
    if 'username' not in session:
        return jsonify([])

    try:
        activities = list(db.activities_col.find(
            {'action': 'collection_payment'}
        ).sort('_id', -1).limit(100))

        result = []
        for p in activities:
            loan_id = p.get('loan_id')

            loan = None
            customer = None
            if loan_id:
                loan = db.loans_col.find_one({'_id': int(loan_id)})
                if loan:
                    customer = db.customers_col.find_one({'_id': loan.get('customer_id')})

            description = p.get('description', '')
            amount = 0
            currency = 'USD'

            if '៛' in description:
                currency = 'KHR'
                match = re.search(r'៛\s*([0-9,]+)', description)
                if match:
                    amount = float(match.group(1).replace(',', ''))
            else:
                match = re.search(r'\$([0-9.]+)', description)
                if match:
                    amount = float(match.group(1))

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
        return jsonify([])


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

    try:
        # ===== ទាញយក Activity ចាស់ =====
        old_activity = db.activities_col.find_one({'_id': int(activity_id)})
        if not old_activity:
            return jsonify({'error': 'មិនឃើញការទូរទាត់នេះទេ!'}), 404

        # ===== ទាញយកកម្ចី =====
        loan = db.loans_col.find_one({'_id': int(loan_id)})
        if not loan:
            return jsonify({'error': 'មិនឃើញកម្ចីនេះទេ!'}), 404

        # ===== ទាញយកចំនួនចាស់ =====
        old_desc = old_activity.get('description', '')
        match = re.search(r'\$([0-9.]+)', old_desc)
        old_amount = float(match.group(1)) if match else 0

        if old_amount == 0:
            match_khr = re.search(r'៛\s*([0-9,]+)', old_desc)
            if match_khr:
                old_amount = float(match_khr.group(1).replace(',', ''))

        # ===== គណនា Difference =====
        diff = amount - old_amount
        new_amount_paid = (loan.get('amount_paid', 0) or 0) + diff
        new_remaining = (loan.get('remaining_balance', 0) or 0) - diff

        if new_amount_paid < 0:
            new_amount_paid = 0
        if new_remaining < 0:
            new_remaining = 0

        # ===== Update Loan =====
        db.loans_col.update_one(
            {'_id': int(loan_id)},
            {'$set': {
                'amount_paid': new_amount_paid,
                'remaining_balance': new_remaining,
                'updated_at': datetime.now()
            }}
        )

        # ===== Update Activity =====
        new_description = f'បានប្រមូលប្រាក់ ${amount:.2f} តាមរយៈ {payment_method}'
        if notes:
            new_description += f', កំណត់ចំណាំ: {notes}'

        db.activities_col.update_one(
            {'_id': int(activity_id)},
            {'$set': {
                'description': new_description,
                'updated_at': datetime.now()
            }}
        )

        return jsonify({
            'success': True,
            'message': f'បានកែប្រែការទូរទាត់ពី ${old_amount:.2f} ទៅ ${amount:.2f} រួចរាល់!'
        })

    except Exception as e:
        import traceback
        print(f"❌ Error in edit_payment: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete_payment', methods=['POST'])
def api_delete_payment():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    activity_id = data.get('activity_id')

    if not activity_id:
        return jsonify({'error': 'Missing activity_id'}), 400

    try:
        # ===== ទាញយក Activity =====
        activity = db.activities_col.find_one({'_id': int(activity_id)})
        if not activity:
            return jsonify({'error': 'មិនឃើញការទូរទាត់នេះទេ!'}), 404

        loan_id = activity.get('loan_id')

        # ===== ទាញយកចំនួន =====
        description = activity.get('description', '')
        match = re.search(r'\$([0-9.]+)', description)
        amount = float(match.group(1)) if match else 0

        if amount == 0:
            match_khr = re.search(r'៛\s*([0-9,]+)', description)
            if match_khr:
                amount = float(match_khr.group(1).replace(',', ''))

        # ===== Update Loan =====
        if loan_id:
            loan = db.loans_col.find_one({'_id': int(loan_id)})
            if loan:
                new_amount_paid = (loan.get('amount_paid', 0) or 0) - amount
                new_remaining = (loan.get('remaining_balance', 0) or 0) + amount
                if new_amount_paid < 0:
                    new_amount_paid = 0

                db.loans_col.update_one(
                    {'_id': int(loan_id)},
                    {'$set': {
                        'amount_paid': new_amount_paid,
                        'remaining_balance': new_remaining,
                        'updated_at': datetime.now()
                    }}
                )

        # ===== Delete Activity =====
        db.activities_col.delete_one({'_id': int(activity_id)})

        return jsonify({'success': True, 'message': 'បានលុបការទូរទាត់រួចរាល់!'})

    except Exception as e:
        import traceback
        print(f"❌ Error in delete_payment: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# ===== TEMPLATE FILTERS =====
@app.template_filter('format_currency')
def format_currency_filter(amount, currency='USD'):
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
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    result = {
        'payment_history_orphan': 0,
        'payment_history_zero': 0,
        'payment_history_no_loan': 0,
        'activities_orphan': 0
    }

    try:
        # ===== លុប Payment History ដែលមិនមាន Loan =====
        all_loan_ids = [l['_id'] for l in db.loans_col.find({}, {'_id': 1})]
        deleted = db.payment_history_col.delete_many({
            'loan_id': {'$nin': all_loan_ids}
        })
        result['payment_history_no_loan'] = deleted.deleted_count

        # ===== លុប Payment History ដែល amount = 0 =====
        deleted2 = db.payment_history_col.delete_many({'amount': 0})
        result['payment_history_zero'] = deleted2.deleted_count

        # ===== លុប Activities ដែលមិនមាន Loan =====
        deleted3 = db.activities_col.delete_many({
            'loan_id': {'$ne': None, '$nin': all_loan_ids}
        })
        result['activities_orphan'] = deleted3.deleted_count

        return jsonify({
            'success': True,
            'message': 'សម្អាតទិន្នន័យរួចរាល់!',
            'result': result
        })

    except Exception as e:
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

    try:
        customer_count = db.customers_col.count_documents({})
        loan_count = db.loans_col.count_documents({})
        active_loans = db.loans_col.count_documents({'status': {'$in': ['Approved', 'Pending']}})
        bad_loans = db.loans_col.count_documents({'status': 'Bad Debt'})

        # ===== ទឹកប្រាក់កម្ចីសរុប =====
        usd_result = list(db.loans_col.aggregate([
            {'$match': {'currency': 'USD'}},
            {'$group': {'_id': None, 'total': {'$sum': '$loan_amount'}}}
        ]))
        total_amount_usd = usd_result[0]['total'] if usd_result else 0

        khr_result = list(db.loans_col.aggregate([
            {'$match': {'currency': 'KHR'}},
            {'$group': {'_id': None, 'total': {'$sum': '$loan_amount'}}}
        ]))
        total_amount_khr = khr_result[0]['total'] if khr_result else 0

        # ===== បំណុលសរុប =====
        debt_usd = list(db.loans_col.aggregate([
            {'$match': {'currency': 'USD'}},
            {'$group': {'_id': None, 'total': {'$sum': '$remaining_balance'}}}
        ]))
        total_debt_usd = debt_usd[0]['total'] if debt_usd else 0

        debt_khr = list(db.loans_col.aggregate([
            {'$match': {'currency': 'KHR'}},
            {'$group': {'_id': None, 'total': {'$sum': '$remaining_balance'}}}
        ]))
        total_debt_khr = debt_khr[0]['total'] if debt_khr else 0

        return jsonify({
            'total_customers': customer_count,
            'total_loans': loan_count,
            'active_loans': active_loans,
            'bad_loans': bad_loans,
            'total_amount_usd': total_amount_usd or 0,
            'total_amount_khr': total_amount_khr or 0,
            'total_debt_usd': total_debt_usd or 0,
            'total_debt_khr': total_debt_khr or 0
        })
    except Exception as e:
        print(f"❌ Error in report_summary: {e}")
        return jsonify({
            'total_customers': 0, 'total_loans': 0, 'active_loans': 0, 'bad_loans': 0,
            'total_amount_usd': 0, 'total_amount_khr': 0,
            'total_debt_usd': 0, 'total_debt_khr': 0
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

    query = {}
    if status and status != 'all':
        query['status'] = status
    if from_date:
        query['loan_date'] = {'$gte': from_date}
    if to_date:
        if 'loan_date' in query:
            query['loan_date']['$lte'] = to_date
        else:
            query['loan_date'] = {'$lte': to_date}
    if officer:
        query['co_officer'] = officer

    pipeline = [
        {'$match': query},
        {'$sort': {'_id': -1}},
        {'$limit': 500},
        {'$lookup': {
            'from': 'customers',
            'localField': 'customer_id',
            'foreignField': '_id',
            'as': 'customer_info'
        }},
        {'$unwind': {'path': '$customer_info', 'preserveNullAndEmptyArrays': True}}
    ]

    loans = list(db.loans_col.aggregate(pipeline))
    result = []
    for l in loans:
        customer = l.get('customer_info', {}) or {}
        doc = dict(l)
        doc['id'] = doc.pop('_id', None)
        doc['customer_name'] = customer.get('name', '')
        doc['customer_code'] = customer.get('code', '')
        doc.pop('customer_info', None)
        result.append(doc)

    return jsonify(result)


# ===== API: REPORT PAYMENTS =====
@app.route('/api/reports/payments')
def api_report_payments():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    method = request.args.get('method', 'all')
    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')

    query = {'action': 'collection_payment'}
    if from_date or to_date:
        date_query = {}
        if from_date:
            try:
                date_query['$gte'] = datetime.strptime(from_date, '%Y-%m-%d')
            except:
                pass
        if to_date:
            try:
                to_dt = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
                date_query['$lt'] = to_dt
            except:
                pass
        if date_query:
            query['created_at'] = date_query

    pipeline = [
        {'$match': query},
        {'$sort': {'created_at': -1}},
        {'$limit': 500},
        {'$lookup': {
            'from': 'loans',
            'localField': 'loan_id',
            'foreignField': '_id',
            'as': 'loan_info'
        }},
        {'$unwind': {'path': '$loan_info', 'preserveNullAndEmptyArrays': True}},
        {'$lookup': {
            'from': 'customers',
            'localField': 'loan_info.customer_id',
            'foreignField': '_id',
            'as': 'customer_info'
        }},
        {'$unwind': {'path': '$customer_info', 'preserveNullAndEmptyArrays': True}}
    ]

    activities = list(db.activities_col.aggregate(pipeline))

    total_amount = 0
    total_count = 0
    cash_total = 0
    aba_total = 0
    payments = []

    for a in activities:
        loan = a.get('loan_info', {}) or {}
        customer = a.get('customer_info', {}) or {}
        description = a.get('description', '')

        match = re.search(r'\$([0-9.]+)', description)
        amount = float(match.group(1)) if match else 0

        if amount == 0:
            match_khr = re.search(r'៛\s*([0-9,]+)', description)
            if match_khr:
                amount = float(match_khr.group(1).replace(',', ''))

        p_method = 'cash'
        if 'ABA' in description or 'aba' in description:
            p_method = 'aba'
        elif 'ACLEDA' in description or 'acleda' in description:
            p_method = 'acleda'

        if method != 'all' and p_method != method:
            continue

        total_amount += amount
        total_count += 1

        if p_method == 'cash':
            cash_total += amount
        elif p_method == 'aba':
            aba_total += amount

        created = a.get('created_at', '')
        if hasattr(created, 'strftime'):
            created = created.strftime('%Y-%m-%d %H:%M:%S')

        payments.append({
            'id': a['_id'],
            'loan_id': a.get('loan_id'),
            'loan_code': loan.get('loan_code', 'N/A'),
            'customer_name': customer.get('name', 'មិនស្គាល់'),
            'co_officer': loan.get('co_officer', '-') or '-',
            'amount': amount,
            'currency': loan.get('currency', 'USD'),
            'payment_method': p_method,
            'created_at': created
        })

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

    pipeline = [
        {'$sort': {'_id': -1}},
        {'$limit': 500},
        {'$lookup': {
            'from': 'loans',
            'localField': '_id',
            'foreignField': 'customer_id',
            'as': 'loans_info'
        }}
    ]

    customers = list(db.customers_col.aggregate(pipeline))

    result_customers = []
    for c in customers:
        loans_info = c.get('loans_info', [])
        loan_count = len(loans_info)
        total_debt = sum(l.get('remaining_balance', 0) or 0 for l in loans_info)

        doc = {
            'id': c['_id'],
            'code': c.get('code', ''),
            'name': c.get('name', ''),
            'gender': c.get('gender', ''),
            'phone': c.get('phone', ''),
            'address': c.get('address', ''),
            'loan_count': loan_count,
            'total_debt': total_debt,
            'created_at': c.get('created_at', '')
        }
        result_customers.append(doc)

    total = db.customers_col.count_documents({})
    male = db.customers_col.count_documents({'$or': [{'gender': 'ប្រុស'}, {'gender': 'male'}]})
    female = db.customers_col.count_documents({'$or': [{'gender': 'ស្រី'}, {'gender': 'female'}]})

    date_30_ago = datetime.now() - timedelta(days=30)
    new_customers = db.customers_col.count_documents({'created_at': {'$gte': date_30_ago}})

    return jsonify({
        'total': total,
        'male': male,
        'female': female,
        'new_customers': new_customers,
        'customers': result_customers
    })


# ===== API: REPORT INCOME =====
@app.route('/api/reports/income')
def api_report_income():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')

    # ===== ការប្រាក់សរុប =====
    match_query = {}
    if from_date or to_date:
        date_query = {}
        if from_date:
            try:
                date_query['$gte'] = datetime.strptime(from_date, '%Y-%m-%d')
            except:
                pass
        if to_date:
            try:
                to_dt = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
                date_query['$lt'] = to_dt
            except:
                pass
        if date_query:
            match_query['created_at'] = date_query

    interest_result = list(db.loans_col.aggregate([
        {'$match': match_query},
        {'$group': {'_id': None, 'total': {'$sum': '$total_interest'}}}
    ]))
    total_interest = interest_result[0]['total'] if interest_result else 0

    # ===== ពិន័យសរុប =====
    penalty_result = list(db.payment_history_col.aggregate([
        {'$match': match_query},
        {'$group': {'_id': None, 'total': {'$sum': '$penalty'}}}
    ]))
    total_penalty = penalty_result[0]['total'] if penalty_result else 0

    total_expense = 0
    transactions = []

    if total_interest > 0:
        transactions.append({
            'type': 'ចំណូល', 'amount': total_interest,
            'date': from_date or 'សរុប', 'note': 'ការប្រាក់ពីកម្ចី'
        })

    if total_penalty > 0:
        transactions.append({
            'type': 'ចំណូល', 'amount': total_penalty,
            'date': from_date or 'សរុប', 'note': 'ពិន័យពីការយឺត'
        })

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

    try:
        from_dt = datetime.strptime(from_date, '%Y-%m-%d')
        to_dt = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)

        # ===== អតិថិជនថ្មី =====
        new_customers = db.customers_col.count_documents({
            'created_at': {'$gte': from_dt, '$lt': to_dt}
        })

        # ===== ទុនទំលាក់ =====
        loans = list(db.loans_col.find({'created_at': {'$gte': from_dt, '$lt': to_dt}}))
        total_loan_disbursed_usd = 0
        total_loan_disbursed_khr = 0

        for l in loans:
            amount = l.get('loan_amount', 0) or 0
            if l.get('currency') == 'USD':
                total_loan_disbursed_usd += amount
            else:
                total_loan_disbursed_khr += amount

        # ===== ការប្រមូល =====
        payments = list(db.payment_history_col.find({
            'created_at': {'$gte': from_dt, '$lt': to_dt}
        }))

        total_collected_usd = 0
        total_collected_khr = 0
        interest_collected_usd = 0
        penalty_collected_usd = 0
        aba_total_usd = 0
        acleda_total_usd = 0

        for p in payments:
            amount = p.get('amount', 0) or 0
            method = p.get('payment_method', 'cash') or 'cash'

            total_collected_usd += amount

            if method == 'aba':
                aba_total_usd += amount
            elif method == 'acleda':
                acleda_total_usd += amount
            elif method == 'penalty':
                penalty_collected_usd += amount
            else:
                interest_collected_usd += amount

        # ===== ចំណាយ =====
        expenses = list(db.expenses_col.find({
            'expense_date': {'$gte': from_date, '$lte': to_date}
        }))

        total_expense_usd = 0
        expense_list = []
        for exp in expenses:
            amount = exp.get('amount', 0) or 0
            total_expense_usd += amount
            expense_list.append({
                'name': exp.get('name', ''),
                'amount': amount
            })

        return jsonify({
            'new_customers': new_customers,
            'total_loan_disbursed_usd': total_loan_disbursed_usd,
            'total_loan_disbursed_khr': total_loan_disbursed_khr,
            'total_collected_usd': total_collected_usd,
            'total_collected_khr': total_collected_khr,
            'interest_collected_usd': interest_collected_usd,
            'interest_collected_khr': 0,
            'penalty_collected_usd': penalty_collected_usd,
            'penalty_collected_khr': 0,
            'aba_total_usd': aba_total_usd,
            'aba_total_khr': 0,
            'acleda_total_usd': acleda_total_usd,
            'acleda_total_khr': 0,
            'total_expense_usd': total_expense_usd,
            'expenses': expense_list
        })

    except Exception as e:
        print(f"❌ Error in summary_report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================
# ===== EXPENSES API ROUTES =====
# ============================================================

@app.route('/api/expenses', methods=['GET'])
def api_get_expenses():
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

    pawns = db.get_pawns_paginated(page, per_page, status if status else None)
    return jsonify(pawns)


@app.route('/api/pawns/count')
def api_pawns_count():
    if 'username' not in session:
        return jsonify({'count': 0})
    status = request.args.get('status', '')
    count = db.count_pawns(status if status else None)
    return jsonify({'count': count})


@app.route('/api/pawns/<int:pawn_id>', methods=['GET'])
def api_get_pawn(pawn_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    pawn = db.get_pawn_by_id(pawn_id)
    if not pawn:
        return jsonify({'error': 'មិនឃើញបញ្ចាំនេះទេ!'}), 404
    return jsonify(pawn)


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

    try:
        limit = request.args.get('limit', 500, type=int)
        action = request.args.get('action', '')
        from_date = request.args.get('from', '')
        to_date = request.args.get('to', '')
        user = request.args.get('user', '')

        logs = db.get_audit_logs(
            action=action,
            user=user,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )
        return jsonify(logs)

    except Exception as e:
        print(f"❌ Error in api_audit: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/audit/actions')
def api_audit_actions():
    if 'username' not in session:
        return jsonify([])

    try:
        actions = db.get_audit_actions()
        return jsonify(actions)
    except Exception as e:
        print(f"❌ Error in api_audit_actions: {e}")
        return jsonify([])


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
            'total_loans': 0, 'active_loans': 0, 'bad_loans': 0,
            'total_amount_usd': 0, 'total_amount_khr': 0,
            'total_debt_usd': 0, 'total_debt_khr': 0
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

    try:
        loan = db.loans_col.find_one({'_id': int(loan_id)})
        if not loan:
            return jsonify({'error': 'មិនឃើញកម្ចីនេះទេ!'}), 404

        old_officer = loan.get('co_officer') or 'គ្មាន'

        # ===== Update CO =====
        db.loans_col.update_one(
            {'_id': int(loan_id)},
            {'$set': {
                'co_officer': new_officer,
                'updated_at': datetime.now()
            }}
        )

        # ===== Log Activity =====
        db.log_activity(
            loan.get('customer_id'),
            loan_id,
            'change_co',
            f'បានផ្លាស់ប្តូរ CO ពី "{old_officer}" ទៅ "{new_officer}" (កំណត់ចំណាំ: {notes})',
            user_id=session.get('user_id')
        )

        return jsonify({
            'success': True,
            'message': f'បានផ្លាស់ប្តូរ CO ពី "{old_officer}" ទៅ "{new_officer}" រួចរាល់!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/loans/<int:loan_id>')
def api_get_loan(loan_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    loan = db.get_loan_by_id(loan_id)
    if not loan:
        return jsonify({'error': 'មិនឃើញកម្ចីនេះទេ!'}), 404

    return jsonify(loan)


@app.route('/api/dashboard_charts')
def api_dashboard_charts():
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
# ===== DASHBOARD ROUTES =====
# ============================================================

@app.route('/api/dashboard_full_stats')
def api_dashboard_full_stats():
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
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

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
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, threaded=True, host='0.0.0.0', port=port)
