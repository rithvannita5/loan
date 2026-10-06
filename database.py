# database.py - MongoDB Version
import os
import re
import json
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING

# ============================================================
# ===== CONNECT TO MONGODB =====
# ============================================================

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/loan_db')
DB_NAME = os.environ.get('DB_NAME', 'loan_db')

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# ============================================================
# ===== COLLECTIONS =====
# ============================================================

customers_col = db['customers']
loans_col = db['loans']
users_col = db['users']
activities_col = db['activities']
payment_history_col = db['payment_history']
officers_col = db['officers']
settings_col = db['settings']
special_holidays_col = db['special_holidays']
permissions_col = db['permissions']
expenses_col = db['expenses']
pawns_col = db['pawns']
counters_col = db['counters']


# ============================================================
# ===== HELPER FUNCTIONS =====
# ============================================================

def get_cambodia_date():
    """ទាញយកថ្ងៃបច្ចុប្បន្នតាមម៉ោងកម្ពុជា (UTC+7)"""
    return (datetime.utcnow() + timedelta(hours=7)).date()


def get_db_connection():
    """សម្រាប់ភាពឆបគ្នា - ត្រឡប់ db object"""
    return db


def get_next_sequence(name):
    """ទាញយកលេខរៀងបន្ទាប់សម្រាប់ Auto-increment"""
    result = counters_col.find_one_and_update(
        {'_id': name},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=True
    )
    return result['seq']


def _to_dict(doc):
    """បម្លែង MongoDB document ទៅ dict ធម្មតា"""
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['id'] = doc['_id']
    return doc


def _to_dict_list(docs):
    """បម្លែង list នៃ documents"""
    return [_to_dict(d) for d in docs]


# ============================================================
# ===== INIT DATABASE =====
# ============================================================

def init_database():
    """បង្កើត Index និង Admin User ដំបូង"""
    # ===== បង្កើត Index =====
    try:
        customers_col.create_index('code', unique=True)
        loans_col.create_index('loan_code', unique=True)
        users_col.create_index('username', unique=True)
        officers_col.create_index('code', unique=True)
        pawns_col.create_index('pawn_code', unique=True)
        loans_col.create_index('status')
        loans_col.create_index('due_date')
        loans_col.create_index('customer_id')
        loans_col.create_index('remaining_balance')
        customers_col.create_index('name')
        customers_col.create_index('phone')
        activities_col.create_index('loan_id')
        activities_col.create_index('customer_id')
        activities_col.create_index('created_at')
        payment_history_col.create_index([('loan_id', 1), ('period', 1)])
        expenses_col.create_index('expense_date')
        pawns_col.create_index('customer_id')
        pawns_col.create_index('status')
        pawns_col.create_index('due_date')
    except Exception as e:
        print(f"⚠️ Index warning: {e}")

    # ===== បង្កើត Admin User ដំបូង =====
    if users_col.count_documents({}) == 0:
        user_id = get_next_sequence('users')
        users_col.insert_one({
            '_id': user_id,
            'username': 'admin',
            'password': '123456',
            'full_name': 'អ្នកគ្រប់គ្រងប្រព័ន្ធ',
            'role': 'admin',
            'created_at': datetime.now()
        })
        print("✅ Created default admin user: admin / 123456")

    print(f"✅ MongoDB Database initialized: {DB_NAME}")


# ============================================================
# ===== WORKING DAYS CALCULATION =====
# ============================================================

def get_holidays():
    """ទាញយកថ្ងៃឈប់សម្រាកប្រចាំសប្តាហ៍"""
    result = settings_col.find_one({'_id': 'holidays'})
    if result and result.get('value'):
        return result['value'].split(',')
    return []


def get_special_holidays():
    """ទាញយកបញ្ជីថ្ងៃបុណ្យពិសេស"""
    holidays = special_holidays_col.find().sort('date', ASCENDING)
    return _to_dict_list(holidays)


def get_next_working_day(start_date, days_to_add):
    """គណនាថ្ងៃធ្វើការបន្ទាប់"""
    holidays = get_holidays()
    special_holidays = get_special_holidays()

    day_mapping = {
        'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3,
        'Fri': 4, 'Sat': 5, 'Sun': 6
    }

    holiday_weekdays = set()
    for holiday in holidays:
        if holiday in day_mapping:
            holiday_weekdays.add(day_mapping[holiday])

    special_dates = set()
    for sh in special_holidays:
        try:
            date_obj = datetime.strptime(sh['date'], '%Y-%m-%d').date()
            special_dates.add(date_obj)
        except:
            pass

    current = start_date
    days_added = 0

    while days_added < days_to_add:
        current += timedelta(days=1)
        weekday = current.weekday()
        is_working_day = True

        if weekday in holiday_weekdays:
            is_working_day = False
        if current in special_dates:
            is_working_day = False

        if is_working_day:
            days_added += 1

    return current


# ============================================================
# ===== CUSTOMER FUNCTIONS =====
# ============================================================

def get_customers_paginated(page=1, per_page=50):
    skip = (page - 1) * per_page
    customers = customers_col.find().sort('_id', DESCENDING).skip(skip).limit(per_page)
    return _to_dict_list(customers)


def count_customers():
    return customers_col.count_documents({})


def search_customers_paginated(keyword, page=1, per_page=50):
    skip = (page - 1) * per_page
    regex = {'$regex': keyword, '$options': 'i'}
    query = {'$or': [
        {'name': regex}, {'code': regex}, {'phone': regex}, {'address': regex}
    ]}
    customers = customers_col.find(query).sort('_id', DESCENDING).skip(skip).limit(per_page)
    return _to_dict_list(customers)


def count_search_customers(keyword):
    regex = {'$regex': keyword, '$options': 'i'}
    query = {'$or': [
        {'name': regex}, {'code': regex}, {'phone': regex}, {'address': regex}
    ]}
    return customers_col.count_documents(query)


def get_all_customers():
    customers = customers_col.find().sort('_id', DESCENDING)
    return _to_dict_list(customers)


def get_all_customers_simple():
    customers = customers_col.find({}, {
        'code': 1, 'name': 1, 'gender': 1, 'phone': 1, 'address': 1,
        'guarantor_name': 1, 'guarantor_gender': 1,
        'guarantor_phone': 1, 'guarantor_address': 1
    }).sort('name', ASCENDING)
    return _to_dict_list(customers)


def get_customer_by_id(customer_id):
    try:
        customer = customers_col.find_one({'_id': int(customer_id)})
        return _to_dict(customer)
    except:
        return None


def get_customer_by_code(code):
    customer = customers_col.find_one({'code': code})
    return _to_dict(customer)


def get_customer_for_loan(customer_id):
    try:
        customer = customers_col.find_one({'_id': int(customer_id)})
        return _to_dict(customer)
    except:
        return None


def create_customer(data):
    customer_id = get_next_sequence('customers')
    doc = {
        '_id': customer_id,
        'code': data['code'],
        'name': data['name'],
        'gender': data.get('gender', ''),
        'phone': data.get('phone', ''),
        'id_card': data.get('id_card', ''),
        'address': data.get('address', ''),
        'guarantor_name': data.get('guarantor_name', ''),
        'guarantor_gender': data.get('guarantor_gender', ''),
        'guarantor_id_card': data.get('guarantor_id_card', ''),
        'guarantor_address': data.get('guarantor_address', ''),
        'guarantor_phone': data.get('guarantor_phone', ''),
        'relation': data.get('relation', ''),
        'dob': data.get('dob', ''),
        'guarantor_dob': data.get('guarantor_dob', ''),
        'created_at': datetime.now()
    }
    customers_col.insert_one(doc)
    return customer_id


def update_customer(customer_id, data):
    update_fields = {
        'name': data.get('name', ''),
        'gender': data.get('gender', ''),
        'phone': data.get('phone', ''),
        'id_card': data.get('id_card', ''),
        'address': data.get('address', ''),
        'guarantor_name': data.get('guarantor_name', ''),
        'guarantor_gender': data.get('guarantor_gender', ''),
        'guarantor_id_card': data.get('guarantor_id_card', ''),
        'guarantor_address': data.get('guarantor_address', ''),
        'guarantor_phone': data.get('guarantor_phone', ''),
        'relation': data.get('relation', ''),
        'dob': data.get('dob', ''),
        'guarantor_dob': data.get('guarantor_dob', ''),
        'updated_at': datetime.now()
    }
    customers_col.update_one({'_id': int(customer_id)}, {'$set': update_fields})


def delete_customer(customer_id):
    try:
        customers_col.delete_one({'_id': int(customer_id)})
    except:
        pass


def search_customers(keyword, limit=20):
    regex = {'$regex': keyword, '$options': 'i'}
    query = {'$or': [
        {'name': regex}, {'code': regex}, {'phone': regex}, {'address': regex}
    ]}
    customers = customers_col.find(query).sort('_id', DESCENDING).limit(limit)
    return _to_dict_list(customers)


def generate_customer_code():
    last = customers_col.find_one(sort=[('_id', DESCENDING)])
    if not last or not last.get('code'):
        return 'CUS-001'
    match = re.search(r'CUS-(\d+)', last['code'])
    if match:
        last_num = int(match.group(1))
        return f'CUS-{last_num + 1:03d}'
    return 'CUS-001'


# ============================================================
# ===== LOAN FUNCTIONS =====
# ============================================================

def _build_loan_pipeline(match_query, skip=0, limit=50):
    """បង្កើត Aggregation Pipeline សម្រាប់ Loans"""
    pipeline = [
        {'$match': match_query},
        {'$sort': {'_id': DESCENDING}},
        {'$skip': skip},
        {'$limit': limit},
        {'$lookup': {
            'from': 'customers',
            'localField': 'customer_id',
            'foreignField': '_id',
            'as': 'customer_info'
        }},
        {'$unwind': {'path': '$customer_info', 'preserveNullAndEmptyArrays': True}}
    ]
    return pipeline


def _format_loan_doc(loan):
    """បម្លែង Loan Document ទៅ Format ដែល Frontend ចង់បាន"""
    customer = loan.get('customer_info', {}) or {}
    doc = dict(loan)
    doc['id'] = doc.pop('_id', None)
    doc['customer_code'] = customer.get('code', '')
    doc['customer_name'] = customer.get('name', '')
    doc['customer_gender'] = customer.get('gender', '')
    doc['customer_phone'] = customer.get('phone', '')
    doc['customer_id_card'] = customer.get('id_card', '')
    doc['customer_address'] = customer.get('address', '')
    doc['guarantor_name'] = customer.get('guarantor_name', '')
    doc['guarantor_gender'] = customer.get('guarantor_gender', '')
    doc['guarantor_id_card'] = customer.get('guarantor_id_card', '')
    doc['guarantor_address'] = customer.get('guarantor_address', '')
    doc['guarantor_phone'] = customer.get('guarantor_phone', '')
    doc['relation'] = customer.get('relation', '')
    # ===== លុប customer_info ចេញ =====
    doc.pop('customer_info', None)
    return doc


def get_loans_paginated(page=1, per_page=50, status=None):
    skip = (page - 1) * per_page

    if status:
        match_query = {'status': status}
    else:
        match_query = {'status': {'$ne': 'Bad Debt'}}

    pipeline = _build_loan_pipeline(match_query, skip, per_page)
    loans = list(loans_col.aggregate(pipeline))
    return [_format_loan_doc(l) for l in loans]


def count_loans(status=None):
    if status:
        return loans_col.count_documents({'status': status})
    else:
        return loans_col.count_documents({'status': {'$ne': 'Bad Debt'}})


def generate_loan_code():
    last = loans_col.find_one(sort=[('_id', DESCENDING)])
    if not last or not last.get('loan_code'):
        return 'LN-001'
    match = re.search(r'LN-(\d+)', last['loan_code'])
    if match:
        last_num = int(match.group(1))
        return f'LN-{last_num + 1:03d}'
    return 'LN-001'


def get_all_loans():
    pipeline = [
        {'$sort': {'_id': DESCENDING}},
        {'$lookup': {
            'from': 'customers',
            'localField': 'customer_id',
            'foreignField': '_id',
            'as': 'customer_info'
        }},
        {'$unwind': {'path': '$customer_info', 'preserveNullAndEmptyArrays': True}}
    ]
    loans = list(loans_col.aggregate(pipeline))
    return [_format_loan_doc(l) for l in loans]


def get_loan_by_id(loan_id):
    try:
        pipeline = [
            {'$match': {'_id': int(loan_id)}},
            {'$lookup': {
                'from': 'customers',
                'localField': 'customer_id',
                'foreignField': '_id',
                'as': 'customer_info'
            }},
            {'$unwind': {'path': '$customer_info', 'preserveNullAndEmptyArrays': True}}
        ]
        result = list(loans_col.aggregate(pipeline))
        if not result:
            return None
        return _format_loan_doc(result[0])
    except:
        return None


def create_loan(data):
    loan_id = get_next_sequence('loans')
    loan_code = data.get('loan_code') or generate_loan_code()

    loan_amount = float(data['loan_amount'])
    interest_rate = float(data['interest_rate'])
    duration_num = int(data['duration_num'])
    currency = data.get('currency', 'USD')

    total_interest = loan_amount * (interest_rate / 100) * duration_num
    total_amount = loan_amount + total_interest

    if currency == 'KHR':
        total_interest = round(total_interest / 100) * 100
        total_amount = round(total_amount / 100) * 100

    doc = {
        '_id': loan_id,
        'loan_code': loan_code,
        'customer_id': int(data['customer_id']),
        'loan_amount': loan_amount,
        'currency': currency,
        'interest_rate': interest_rate,
        'total_interest': total_interest,
        'total_amount': total_amount,
        'amount_paid': 0,
        'remaining_balance': total_amount,
        'status': data.get('status', 'Pending'),
        'co_officer': data.get('co_officer', ''),
        'loan_date': data.get('loan_date', ''),
        'due_date': data.get('due_date', ''),
        'duration_num': duration_num,
        'duration_type': data.get('duration_type', 'ថ្ងៃ'),
        'calc_type': int(data.get('calc_type', 1)),
        'service_fee': float(data.get('service_fee', 0)),
        'service_fee_amount': float(data.get('service_fee_amount', 0)),
        'insurance_fee': float(data.get('insurance_fee', 0)),
        'insurance_amount': float(data.get('insurance_amount', 0)),
        'purpose': data.get('purpose', ''),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    loans_col.insert_one(doc)
    return loan_id


def update_loan(loan_id, data):
    loan_amount = float(data['loan_amount'])
    interest_rate = float(data['interest_rate'])
    duration_num = int(data['duration_num'])
    currency = data.get('currency', 'USD')

    total_interest = loan_amount * (interest_rate / 100) * duration_num
    total_amount = loan_amount + total_interest

    if currency == 'KHR':
        total_interest = round(total_interest / 100) * 100
        total_amount = round(total_amount / 100) * 100

    update_fields = {
        'loan_amount': loan_amount,
        'currency': currency,
        'interest_rate': interest_rate,
        'total_interest': total_interest,
        'total_amount': total_amount,
        'amount_paid': float(data.get('amount_paid', 0)),
        'remaining_balance': float(data.get('remaining_balance', total_amount)),
        'status': data.get('status', 'Pending'),
        'co_officer': data.get('co_officer', ''),
        'loan_date': data.get('loan_date', ''),
        'due_date': data.get('due_date', ''),
        'duration_num': duration_num,
        'duration_type': data.get('duration_type', 'ថ្ងៃ'),
        'calc_type': int(data.get('calc_type', 1)),
        'service_fee': float(data.get('service_fee', 0)),
        'service_fee_amount': float(data.get('service_fee_amount', 0)),
        'insurance_fee': float(data.get('insurance_fee', 0)),
        'insurance_amount': float(data.get('insurance_amount', 0)),
        'purpose': data.get('purpose', ''),
        'updated_at': datetime.now()
    }
    loans_col.update_one({'_id': int(loan_id)}, {'$set': update_fields})


def delete_loan(loan_id):
    try:
        loans_col.delete_one({'_id': int(loan_id)})
    except:
        pass


def update_loan_status(loan_id, status):
    loans_col.update_one(
        {'_id': int(loan_id)},
        {'$set': {'status': status, 'updated_at': datetime.now()}}
    )


def get_loans_by_customer(customer_id):
    pipeline = [
        {'$match': {'customer_id': int(customer_id)}},
        {'$sort': {'_id': DESCENDING}},
        {'$lookup': {
            'from': 'customers',
            'localField': 'customer_id',
            'foreignField': '_id',
            'as': 'customer_info'
        }},
        {'$unwind': {'path': '$customer_info', 'preserveNullAndEmptyArrays': True}}
    ]
    loans = list(loans_col.aggregate(pipeline))
    return [_format_loan_doc(l) for l in loans]


def update_loan_payment(loan_id, amount_paid, remaining_balance, status):
    loans_col.update_one(
        {'_id': int(loan_id)},
        {'$set': {
            'amount_paid': float(amount_paid),
            'remaining_balance': float(remaining_balance),
            'status': status,
            'updated_at': datetime.now()
        }}
    )


# ============================================================
# ===== PAYMENT HISTORY FUNCTIONS =====
# ============================================================

def record_payment(loan_id, period, amount, payment_method, notes):
    payment_id = get_next_sequence('payment_history')
    today = datetime.now().date().isoformat()

    doc = {
        '_id': payment_id,
        'loan_id': int(loan_id),
        'period': int(period),
        'amount': float(amount),
        'payment_date': today,
        'payment_method': payment_method,
        'notes': notes,
        'created_at': datetime.now()
    }
    payment_history_col.insert_one(doc)
    return payment_id


def get_payment_history_by_loan(loan_id):
    payments = payment_history_col.find({'loan_id': int(loan_id)}).sort('period', ASCENDING)
    return _to_dict_list(payments)


def get_payment_history(limit=100):
    pipeline = [
        {'$match': {'action': 'collection_payment'}},
        {'$sort': {'created_at': DESCENDING}},
        {'$limit': limit},
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

    payments = list(activities_col.aggregate(pipeline))
    result = []
    for p in payments:
        loan = p.get('loan_info', {}) or {}
        customer = p.get('customer_info', {}) or {}
        description = p.get('description', '')

        # ===== ទាញយកចំនួនទឹកប្រាក់ =====
        match = re.search(r'\$([0-9.]+)', description)
        amount = float(match.group(1)) if match else 0

        currency = loan.get('currency') or 'USD'
        if '៛' in description:
            currency = 'KHR'
            match_khr = re.search(r'៛\s*([0-9,]+)', description)
            if match_khr:
                amount = float(match_khr.group(1).replace(',', ''))

        method_match = re.search(r'តាមរយៈ\s+(\S+)', description)
        method = method_match.group(1) if method_match else 'cash'

        penalty_match = re.search(r'ពិន័យ:\s*\$?([0-9.]+)', description)
        penalty = float(penalty_match.group(1)) if penalty_match else 0

        notes_match = re.search(r'កំណត់ចំណាំ:\s*([^)]+)', description)
        notes = notes_match.group(1) if notes_match else ''

        created = p.get('created_at', '')
        if hasattr(created, 'strftime'):
            created = created.strftime('%Y-%m-%d %H:%M:%S')

        result.append({
            'id': p['_id'],
            'loan_id': p.get('loan_id'),
            'loan_code': loan.get('loan_code', 'N/A'),
            'customer_name': customer.get('name', 'មិនស្គាល់'),
            'co_officer': loan.get('co_officer', '-') or '-',
            'amount': amount,
            'currency': currency,
            'payment_method': method,
            'penalty': penalty,
            'notes': notes,
            'created_at': created
        })

    return result


# ============================================================
# ===== COLLECTION FUNCTIONS =====
# ============================================================

def get_collection_loans(collection_type, page=1, per_page=50):
    offset = (page - 1) * per_page
    today = get_cambodia_date()

    # ===== ទាញយកកម្ចីទាំងអស់ =====
    query = {
        'status': {'$in': ['Approved', 'Pending', 'Bad Debt']},
        'remaining_balance': {'$gt': 0}
    }

    loans = list(loans_col.find(query).sort('due_date', ASCENDING))

    # ===== បន្ថែមព័ត៌មានអតិថិជន =====
    result = []
    for loan in loans:
        # ===== ទាញយកអតិថិជន =====
        customer = customers_col.find_one({'_id': loan.get('customer_id')}) or {}

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
                    days_overdue = days_diff - 1
                    if days_overdue < 0:
                        days_overdue = 0
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

        if total_due < 0:
            total_due = 0
        if total_principal < 0:
            total_principal = 0
        if total_interest_due < 0:
            total_interest_due = 0

        if total_due == 0:
            continue

        # ===== ច្រោះតាមប្រភេទ =====
        if collection_type == 'good':
            if loan.get('status') == 'Bad Debt':
                continue
            if days_overdue > 0 and total_due > daily_payment:
                continue

        elif collection_type == 'late':
            if loan.get('status') == 'Bad Debt':
                continue
            if days_overdue < 1 or days_overdue > 30:
                continue
            if total_due <= daily_payment:
                continue

        else:  # 'bad'
            if loan.get('status') != 'Bad Debt':
                continue

        loan_dict = dict(loan)
        loan_dict['id'] = loan_dict.pop('_id', None)
        loan_dict['customer_code'] = customer.get('code', '')
        loan_dict['customer_name'] = customer.get('name', '')
        loan_dict['customer_phone'] = customer.get('phone', '')
        loan_dict['customer_address'] = customer.get('address', '')
        loan_dict['days_overdue'] = days_overdue
        loan_dict['total_due'] = total_due
        loan_dict['principal_due'] = total_principal
        loan_dict['interest_due'] = total_interest_due
        loan_dict['principal'] = total_principal
        loan_dict['interest'] = total_interest_due
        loan_dict['penalty'] = 0
        result.append(loan_dict)

    # ===== Pagination =====
    return result[offset:offset + per_page]


# ============================================================
# ===== DISBURSEMENT FUNCTIONS =====
# ============================================================

def get_disbursement_payments(limit=100):
    pipeline = [
        {'$match': {'action': 'collection_payment'}},
        {'$sort': {'created_at': DESCENDING}},
        {'$limit': limit},
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

    payments = list(activities_col.aggregate(pipeline))
    result = []
    for p in payments:
        loan = p.get('loan_info', {}) or {}
        customer = p.get('customer_info', {}) or {}
        description = p.get('description', '')

        match = re.search(r'\$([0-9.]+)', description)
        amount = float(match.group(1)) if match else 0

        currency = loan.get('currency') or 'USD'
        if '៛' in description:
            currency = 'KHR'
            match_khr = re.search(r'៛\s*([0-9,]+)', description)
            if match_khr:
                amount = float(match_khr.group(1).replace(',', ''))

        created = p.get('created_at', '')
        if hasattr(created, 'strftime'):
            created = created.strftime('%Y-%m-%d %H:%M:%S')

        result.append({
            'id': p['_id'],
            'loan_id': p.get('loan_id'),
            'loan_code': loan.get('loan_code', 'N/A'),
            'customer_name': customer.get('name', 'មិនស្គាល់'),
            'co_officer': loan.get('co_officer', '-') or '-',
            'amount': amount,
            'currency': currency,
            'created_at': created,
            'status': p.get('status', 'Pending') or 'Pending'
        })

    return result


# ============================================================
# ===== USER MANAGEMENT =====
# ============================================================

def get_user_by_username(username):
    user = users_col.find_one({'username': username})
    return _to_dict(user)


def get_all_users():
    users = users_col.find({}, {
        'username': 1, 'full_name': 1, 'role': 1, 'created_at': 1
    }).sort('_id', ASCENDING)
    return _to_dict_list(users)


def get_user_by_id(user_id):
    try:
        user = users_col.find_one({'_id': int(user_id)})
        return _to_dict(user)
    except:
        return None


def create_user(data):
    user_id = get_next_sequence('users')
    doc = {
        '_id': user_id,
        'username': data['username'],
        'password': data['password'],
        'full_name': data.get('full_name', ''),
        'role': data.get('role', 'user'),
        'created_at': datetime.now()
    }
    users_col.insert_one(doc)
    return user_id


def update_user(user_id, data):
    update_fields = {
        'username': data['username'],
        'full_name': data.get('full_name', ''),
        'role': data.get('role', 'user')
    }
    if data.get('password'):
        update_fields['password'] = data['password']

    users_col.update_one({'_id': int(user_id)}, {'$set': update_fields})


def delete_user(user_id):
    try:
        users_col.delete_one({'_id': int(user_id)})
    except:
        pass


# ============================================================
# ===== OFFICER MANAGEMENT =====
# ============================================================

def get_all_officers():
    officers = officers_col.find().sort('_id', ASCENDING)
    return _to_dict_list(officers)


def get_officer_by_id(officer_id):
    try:
        officer = officers_col.find_one({'_id': int(officer_id)})
        return _to_dict(officer)
    except:
        return None


def create_officer(data):
    officer_id = get_next_sequence('officers')
    doc = {
        '_id': officer_id,
        'code': data['code'],
        'name': data['name'],
        'phone': data.get('phone', ''),
        'address': data.get('address', ''),
        'status': 'active',
        'created_at': datetime.now()
    }
    officers_col.insert_one(doc)
    return officer_id


def update_officer(officer_id, data):
    update_fields = {
        'code': data['code'],
        'name': data['name'],
        'phone': data.get('phone', ''),
        'address': data.get('address', '')
    }
    officers_col.update_one({'_id': int(officer_id)}, {'$set': update_fields})


def delete_officer(officer_id):
    try:
        officers_col.delete_one({'_id': int(officer_id)})
    except:
        pass


# ============================================================
# ===== HOLIDAY MANAGEMENT =====
# ============================================================

def save_holidays(holidays):
    settings_col.update_one(
        {'_id': 'holidays'},
        {'$set': {'value': ','.join(holidays), 'updated_at': datetime.now()}},
        upsert=True
    )


def add_special_holiday(data):
    holiday_id = get_next_sequence('special_holidays')
    doc = {
        '_id': holiday_id,
        'date': data['date'],
        'name': data['name'],
        'created_at': datetime.now()
    }
    special_holidays_col.insert_one(doc)
    return holiday_id


def delete_special_holiday(holiday_id):
    try:
        special_holidays_col.delete_one({'_id': int(holiday_id)})
    except:
        pass


# ============================================================
# ===== PERMISSIONS MANAGEMENT =====
# ============================================================

def save_permissions(role, permissions):
    permissions_col.update_one(
        {'_id': role},
        {'$set': {
            'permissions': json.dumps(permissions),
            'updated_at': datetime.now()
        }},
        upsert=True
    )


def get_permissions(role):
    result = permissions_col.find_one({'_id': role})
    if result and result.get('permissions'):
        return json.loads(result['permissions'])
    return {}


# ============================================================
# ===== ACTIVITY FUNCTIONS =====
# ============================================================

def log_activity(customer_id, loan_id, action, description, status=None, user_id=None):
    """កត់ត្រាសកម្មភាព"""
    if user_id is None:
        try:
            from flask import session
            if 'user_id' in session:
                user_id = session['user_id']
        except:
            pass

    activity_id = get_next_sequence('activities')
    doc = {
        '_id': activity_id,
        'customer_id': customer_id,
        'loan_id': loan_id,
        'user_id': user_id,
        'action': action,
        'description': description,
        'status': status or 'Pending',
        'created_at': datetime.now()
    }
    activities_col.insert_one(doc)
    return activity_id


def get_activities(limit=20):
    activities = activities_col.find().sort('created_at', DESCENDING).limit(limit)
    result = []
    for a in activities:
        doc = dict(a)
        doc['id'] = doc.pop('_id', None)
        if hasattr(doc.get('created_at'), 'strftime'):
            doc['created_at'] = doc['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        result.append(doc)
    return result


def get_activities_by_loan(loan_id, limit=20):
    activities = activities_col.find({'loan_id': int(loan_id)}).sort('created_at', DESCENDING).limit(limit)
    return _to_dict_list(activities)


def get_activities_by_customer(customer_id, limit=20):
    activities = activities_col.find({'customer_id': int(customer_id)}).sort('created_at', DESCENDING).limit(limit)
    return _to_dict_list(activities)


# ============================================================
# ===== STATS FUNCTIONS =====
# ============================================================

def get_loan_count():
    return loans_col.count_documents({})


def get_bad_loan_count():
    return loans_col.count_documents({'status': 'Bad Debt'})


def get_total_loan_amount():
    pipeline = [
        {'$group': {'_id': None, 'total': {'$sum': '$loan_amount'}}}
    ]
    result = list(loans_col.aggregate(pipeline))
    return result[0]['total'] if result else 0


def get_total_remaining_balance():
    pipeline = [
        {'$group': {'_id': None, 'total': {'$sum': '$remaining_balance'}}}
    ]
    result = list(loans_col.aggregate(pipeline))
    return result[0]['total'] if result else 0


def get_dashboard_stats():
    customer_count = customers_col.count_documents({})
    loan_count = loans_col.count_documents({})
    active_loans = loans_col.count_documents({'status': {'$in': ['Approved', 'Pending']}})
    bad_loans = loans_col.count_documents({'status': 'Bad Debt'})

    total_amount_result = list(loans_col.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': '$loan_amount'}}}
    ]))
    total_amount = total_amount_result[0]['total'] if total_amount_result else 0

    total_debt_result = list(loans_col.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': '$remaining_balance'}}}
    ]))
    total_debt = total_debt_result[0]['total'] if total_debt_result else 0

    return {
        'total_customers': customer_count,
        'total_loans': loan_count,
        'active_loans': active_loans,
        'bad_loans': bad_loans,
        'total_amount': total_amount or 0,
        'total_debt': total_debt or 0
    }


def get_collection_summary():
    """ទាញយកសង្ខេបស្ថានភាពប្រមូលប្រាក់"""
    today = get_cambodia_date()
    today_str = today.isoformat()

    # ===== កម្ចីល្អ =====
    good_loans = list(loans_col.find({
        'status': {'$in': ['Approved', 'Pending']},
        'remaining_balance': {'$gt': 0},
        'due_date': {'$gte': today_str}
    }))
    good_total = sum(l.get('remaining_balance', 0) for l in good_loans)

    # ===== កម្ចីយឺត =====
    thirty_days_ago = (today - timedelta(days=30)).isoformat()
    late_loans = list(loans_col.find({
        'status': {'$in': ['Approved', 'Pending']},
        'remaining_balance': {'$gt': 0},
        'due_date': {'$lt': today_str, '$gte': thirty_days_ago}
    }))
    late_total = sum(l.get('remaining_balance', 0) for l in late_loans)

    # ===== កម្ចីខូច =====
    bad_loans = list(loans_col.find({
        '$or': [
            {'status': 'Bad Debt'},
            {'remaining_balance': {'$gt': 0}, 'due_date': {'$lt': thirty_days_ago}}
        ]
    }))
    bad_total = sum(l.get('remaining_balance', 0) for l in bad_loans)

    return {
        'good': {'count': len(good_loans), 'total': good_total or 0},
        'late': {'count': len(late_loans), 'total': late_total or 0},
        'bad': {'count': len(bad_loans), 'total': bad_total or 0}
    }


def get_recent_loans(limit=100):
    pipeline = [
        {'$sort': {'_id': DESCENDING}},
        {'$limit': limit},
        {'$lookup': {
            'from': 'customers',
            'localField': 'customer_id',
            'foreignField': '_id',
            'as': 'customer_info'
        }},
        {'$unwind': {'path': '$customer_info', 'preserveNullAndEmptyArrays': True}}
    ]
    loans = list(loans_col.aggregate(pipeline))
    return [_format_loan_doc(l) for l in loans]


# ============================================================
# ===== EXPENSES FUNCTIONS =====
# ============================================================

def get_all_expenses(limit=500):
    expenses = expenses_col.find().sort([('expense_date', DESCENDING), ('_id', DESCENDING)]).limit(limit)
    result = []
    for e in expenses:
        doc = dict(e)
        doc['id'] = doc.pop('_id', None)
        if hasattr(doc.get('created_at'), 'strftime'):
            doc['created_at'] = doc['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if hasattr(doc.get('updated_at'), 'strftime'):
            doc['updated_at'] = doc['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        result.append(doc)
    return result


def get_expenses_by_date_range(from_date, to_date):
    expenses = expenses_col.find({
        'expense_date': {'$gte': from_date, '$lte': to_date}
    }).sort('expense_date', DESCENDING)
    return _to_dict_list(expenses)


def get_expense_by_id(expense_id):
    try:
        expense = expenses_col.find_one({'_id': int(expense_id)})
        return _to_dict(expense)
    except:
        return None


def create_expense(data):
    expense_id = get_next_sequence('expenses')
    doc = {
        '_id': expense_id,
        'name': data['name'],
        'amount': float(data['amount']),
        'category': data.get('category', ''),
        'description': data.get('description', ''),
        'expense_date': data.get('expense_date', datetime.now().date().isoformat()),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    expenses_col.insert_one(doc)
    return expense_id


def update_expense(expense_id, data):
    update_fields = {
        'name': data['name'],
        'amount': float(data['amount']),
        'category': data.get('category', ''),
        'description': data.get('description', ''),
        'expense_date': data.get('expense_date', datetime.now().date().isoformat()),
        'updated_at': datetime.now()
    }
    expenses_col.update_one({'_id': int(expense_id)}, {'$set': update_fields})


def delete_expense(expense_id):
    try:
        expenses_col.delete_one({'_id': int(expense_id)})
    except:
        pass


def get_total_expenses_by_date_range(from_date, to_date):
    pipeline = [
        {'$match': {'expense_date': {'$gte': from_date, '$lte': to_date}}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    result = list(expenses_col.aggregate(pipeline))
    return result[0]['total'] if result else 0


def get_expense_categories():
    categories = expenses_col.distinct('category')
    return [c for c in categories if c]


def get_loans_paginated_excluding_status(page=1, per_page=50, exclude_status='Bad Debt'):
    skip = (page - 1) * per_page
    match_query = {'status': {'$ne': exclude_status}}
    pipeline = _build_loan_pipeline(match_query, skip, per_page)
    loans = list(loans_col.aggregate(pipeline))
    return [_format_loan_doc(l) for l in loans]


# ============================================================
# ===== PAWN FUNCTIONS =====
# ============================================================

def generate_pawn_code():
    last = pawns_col.find_one(sort=[('_id', DESCENDING)])
    if not last or not last.get('pawn_code'):
        return 'PWN-001'
    match = re.search(r'PWN-(\d+)', last['pawn_code'])
    if match:
        last_num = int(match.group(1))
        return f'PWN-{last_num + 1:04d}'
    return 'PWN-001'


def create_pawn(data):
    pawn_id = get_next_sequence('pawns')
    pawn_code = generate_pawn_code()

    doc = {
        '_id': pawn_id,
        'pawn_code': pawn_code,
        'customer_id': int(data['customer_id']),
        'item_name': data['item_name'],
        'item_description': data.get('item_description', ''),
        'item_category': data.get('item_category', ''),
        'item_value': float(data['item_value']),
        'loan_amount': float(data['loan_amount']),
        'currency': data.get('currency', 'USD'),
        'interest_rate': float(data.get('interest_rate', 0)),
        'interest_amount': float(data.get('interest_amount', 0)),
        'total_amount': float(data['total_amount']),
        'amount_paid': 0,
        'remaining_balance': float(data['total_amount']),
        'pawn_date': data['pawn_date'],
        'due_date': data['due_date'],
        'status': data.get('status', 'Active'),
        'co_officer': data.get('co_officer', ''),
        'notes': data.get('notes', ''),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    pawns_col.insert_one(doc)
    return pawn_id


def get_pawns_paginated(page=1, per_page=50, status=None):
    skip = (page - 1) * per_page
    match_query = {}
    if status:
        match_query['status'] = status

    pipeline = [
        {'$match': match_query},
        {'$sort': {'_id': DESCENDING}},
        {'$skip': skip},
        {'$limit': per_page},
        {'$lookup': {
            'from': 'customers',
            'localField': 'customer_id',
            'foreignField': '_id',
            'as': 'customer_info'
        }},
        {'$unwind': {'path': '$customer_info', 'preserveNullAndEmptyArrays': True}}
    ]

    pawns = list(pawns_col.aggregate(pipeline))
    result = []
    for p in pawns:
        customer = p.get('customer_info', {}) or {}
        doc = dict(p)
        doc['id'] = doc.pop('_id', None)
        doc['customer_code'] = customer.get('code', '')
        doc['customer_name'] = customer.get('name', '')
        doc['customer_phone'] = customer.get('phone', '')
        doc.pop('customer_info', None)
        result.append(doc)
    return result


def count_pawns(status=None):
    if status:
        return pawns_col.count_documents({'status': status})
    return pawns_col.count_documents({})


def get_pawn_by_id(pawn_id):
    try:
        pipeline = [
            {'$match': {'_id': int(pawn_id)}},
            {'$lookup': {
                'from': 'customers',
                'localField': 'customer_id',
                'foreignField': '_id',
                'as': 'customer_info'
            }},
            {'$unwind': {'path': '$customer_info', 'preserveNullAndEmptyArrays': True}}
        ]
        result = list(pawns_col.aggregate(pipeline))
        if not result:
            return None
        p = result[0]
        customer = p.get('customer_info', {}) or {}
        doc = dict(p)
        doc['id'] = doc.pop('_id', None)
        doc['customer_code'] = customer.get('code', '')
        doc['customer_name'] = customer.get('name', '')
        doc['customer_phone'] = customer.get('phone', '')
        doc['customer_address'] = customer.get('address', '')
        doc.pop('customer_info', None)
        return doc
    except:
        return None


def update_pawn_status(pawn_id, status):
    pawns_col.update_one(
        {'_id': int(pawn_id)},
        {'$set': {'status': status, 'updated_at': datetime.now()}}
    )


def redeem_pawn(pawn_id, amount_paid):
    pawn = pawns_col.find_one({'_id': int(pawn_id)})
    if not pawn:
        return {'success': False, 'error': 'មិនឃើញបញ្ចាំ'}

    new_amount_paid = (pawn.get('amount_paid', 0) or 0) + amount_paid
    new_remaining = (pawn.get('remaining_balance', 0) or 0) - amount_paid

    if new_remaining <= 0:
        new_remaining = 0
        status = 'Redeemed'
    else:
        status = 'Active'

    pawns_col.update_one(
        {'_id': int(pawn_id)},
        {'$set': {
            'amount_paid': new_amount_paid,
            'remaining_balance': new_remaining,
            'status': status,
            'updated_at': datetime.now()
        }}
    )
    return {'success': True, 'status': status}


def delete_pawn(pawn_id):
    try:
        pawns_col.delete_one({'_id': int(pawn_id)})
    except:
        pass


def update_pawn(pawn_id, data):
    update_fields = {
        'customer_id': int(data['customer_id']),
        'item_name': data['item_name'],
        'item_description': data.get('item_description', ''),
        'item_category': data.get('item_category', ''),
        'item_value': float(data['item_value']),
        'loan_amount': float(data['loan_amount']),
        'currency': data.get('currency', 'USD'),
        'interest_rate': float(data.get('interest_rate', 0)),
        'interest_amount': float(data.get('interest_amount', 0)),
        'total_amount': float(data['total_amount']),
        'pawn_date': data['pawn_date'],
        'due_date': data['due_date'],
        'co_officer': data.get('co_officer', ''),
        'notes': data.get('notes', ''),
        'updated_at': datetime.now()
    }
    pawns_col.update_one({'_id': int(pawn_id)}, {'$set': update_fields})


def get_loans_by_officer(officer_name, page=1, per_page=50, status=None):
    skip = (page - 1) * per_page
    match_query = {'co_officer': officer_name}
    if status:
        match_query['status'] = status

    pipeline = _build_loan_pipeline(match_query, skip, per_page)
    loans = list(loans_col.aggregate(pipeline))
    return [_format_loan_doc(l) for l in loans]

# ============================================================
# ===== AUDIT FUNCTIONS (MongoDB) =====
# ============================================================

def get_audit_logs(action='', user='', from_date='', to_date='', limit=500):
    """ទាញយក Audit Logs ជាមួយ Filter"""
    # ===== Build Match Query =====
    match_query = {}

    if action:
        match_query['action'] = action

    if from_date or to_date:
        date_query = {}
        if from_date:
            try:
                date_query['$gte'] = datetime.strptime(from_date, '%Y-%m-%d')
            except:
                pass
        if to_date:
            try:
                # ===== បន្ថែម ១ ថ្ងៃ ដើម្បីរាប់បញ្ចូលថ្ងៃចុងក្រោយ =====
                to_dt = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
                date_query['$lt'] = to_dt
            except:
                pass
        if date_query:
            match_query['created_at'] = date_query

    # ===== Aggregation Pipeline =====
    pipeline = [
        {'$match': match_query},
        {'$sort': {'created_at': DESCENDING}},
        {'$limit': limit},
        # ===== Lookup User =====
        {'$lookup': {
            'from': 'users',
            'localField': 'user_id',
            'foreignField': '_id',
            'as': 'user_info'
        }},
        {'$unwind': {'path': '$user_info', 'preserveNullAndEmptyArrays': True}},
        # ===== Lookup Customer =====
        {'$lookup': {
            'from': 'customers',
            'localField': 'customer_id',
            'foreignField': '_id',
            'as': 'customer_info'
        }},
        {'$unwind': {'path': '$customer_info', 'preserveNullAndEmptyArrays': True}},
        # ===== Lookup Loan =====
        {'$lookup': {
            'from': 'loans',
            'localField': 'loan_id',
            'foreignField': '_id',
            'as': 'loan_info'
        }},
        {'$unwind': {'path': '$loan_info', 'preserveNullAndEmptyArrays': True}}
    ]

    activities = list(activities_col.aggregate(pipeline))

    # ===== Format Result =====
    result = []
    for a in activities:
        user_info = a.get('user_info', {}) or {}
        customer_info = a.get('customer_info', {}) or {}
        loan_info = a.get('loan_info', {}) or {}

        # ===== Format Date =====
        created = a.get('created_at', '')
        if hasattr(created, 'strftime'):
            created = created.strftime('%Y-%m-%d %H:%M:%S')

        result.append({
            'id': a['_id'],
            'user_id': a.get('user_id'),
            'user_name': user_info.get('username', ''),
            'full_name': user_info.get('full_name', ''),
            'action': a.get('action', ''),
            'description': a.get('description', ''),
            'customer_id': a.get('customer_id'),
            'customer_name': customer_info.get('name', ''),
            'loan_id': a.get('loan_id'),
            'loan_code': loan_info.get('loan_code', ''),
            'status': a.get('status', 'Pending') or 'Pending',
            'created_at': created
        })

    # ===== Filter by User (បើមាន) =====
    if user:
        user_lower = user.lower()
        result = [r for r in result if user_lower in (r['user_name'] or '').lower()
                  or user_lower in (r['full_name'] or '').lower()]

    return result


def get_audit_actions():
    """ទាញយកបញ្ជី Action Types ទាំងអស់"""
    actions = activities_col.distinct('action')
    return sorted([a for a in actions if a])

# ============================================================
# ===== INITIALIZE DATABASE =====
# ============================================================

if __name__ == '__main__':
    init_database()
else:
    # ===== ហៅ init ពេល Import =====
    try:
        init_database()
    except Exception as e:
        print(f"⚠️ Init warning: {e}")
