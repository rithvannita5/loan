# database.py - MongoDB Version
import os
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING

# ===== CONNECT TO MONGODB =====
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/loan_db')
DB_NAME = os.environ.get('DB_NAME', 'loan_db')

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# ===== COLLECTIONS =====
users_col = db['users']
customers_col = db['customers']
loans_col = db['loans']
officers_col = db['officers']
pawns_col = db['pawns']
activities_col = db['activities']
payment_history_col = db['payment_history']
expenses_col = db['expenses']
holidays_col = db['holidays']
special_holidays_col = db['special_holidays']
permissions_col = db['permissions']
counters_col = db['counters']


# ============================================================
# ===== HELPER FUNCTIONS =====
# ============================================================

def _to_dict(doc):
    """បម្លែង MongoDB document ទៅ dict ធម្មតា ដោយបម្លែង _id ទៅ id"""
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['id'] = str(doc['_id'])
    return doc


def _to_dict_list(docs):
    """បម្លែង list នៃ documents"""
    return [_to_dict(d) for d in docs]


def get_next_sequence(name):
    """ទាញយកលេខរៀងបន្ទាប់សម្រាប់ Auto-increment"""
    result = counters_col.find_one_and_update(
        {'_id': name},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=True
    )
    return result['seq']


def get_db_connection():
    """សម្រាប់ភាពឆបគ្នា - ត្រឡប់ db object"""
    return db


# ============================================================
# ===== USER FUNCTIONS =====
# ============================================================

def get_user_by_username(username):
    user = users_col.find_one({'username': username})
    return _to_dict(user)


def get_user_by_id(user_id):
    try:
        user = users_col.find_one({'_id': ObjectId(user_id)})
        return _to_dict(user)
    except:
        return None


def get_all_users():
    users = users_col.find().sort('_id', DESCENDING)
    return _to_dict_list(users)


def create_user(data):
    user_id = get_next_sequence('users')
    doc = {
        '_id': user_id,
        'username': data.get('username'),
        'password': data.get('password'),
        'full_name': data.get('full_name', ''),
        'role': data.get('role', 'user'),
        'created_at': datetime.now()
    }
    users_col.insert_one(doc)
    return user_id


def update_user(user_id, data):
    update_fields = {}
    for key in ['username', 'full_name', 'role']:
        if key in data:
            update_fields[key] = data[key]
    if data.get('password'):
        update_fields['password'] = data['password']

    if update_fields:
        users_col.update_one({'_id': int(user_id)}, {'$set': update_fields})
    return True


def delete_user(user_id):
    users_col.delete_one({'_id': int(user_id)})
    return True


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


def search_customers(keyword, limit=20):
    regex = {'$regex': keyword, '$options': 'i'}
    query = {'$or': [
        {'name': regex}, {'code': regex}, {'phone': regex}
    ]}
    customers = customers_col.find(query).limit(limit)
    return _to_dict_list(customers)


def get_all_customers_simple():
    customers = customers_col.find({}, {'code': 1, 'name': 1}).sort('code', ASCENDING)
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
        'code': data.get('code'),
        'name': data.get('name'),
        'gender': data.get('gender', ''),
        'phone': data.get('phone', ''),
        'dob': data.get('dob', ''),
        'id_card': data.get('id_card', ''),
        'address': data.get('address', ''),
        'guarantor_name': data.get('guarantor_name', ''),
        'guarantor_gender': data.get('guarantor_gender', ''),
        'guarantor_id_card': data.get('guarantor_id_card', ''),
        'guarantor_dob': data.get('guarantor_dob', ''),
        'guarantor_phone': data.get('guarantor_phone', ''),
        'guarantor_address': data.get('guarantor_address', ''),
        'relation': data.get('relation', ''),
        'created_at': datetime.now()
    }
    customers_col.insert_one(doc)
    return customer_id


def update_customer(customer_id, data):
    update_fields = {}
    for key in ['code', 'name', 'gender', 'phone', 'dob', 'id_card', 'address',
                'guarantor_name', 'guarantor_gender', 'guarantor_id_card',
                'guarantor_dob', 'guarantor_phone', 'guarantor_address', 'relation']:
        if key in data:
            update_fields[key] = data[key]

    if update_fields:
        customers_col.update_one({'_id': int(customer_id)}, {'$set': update_fields})
    return True


def delete_customer(customer_id):
    try:
        customers_col.delete_one({'_id': int(customer_id)})
        return True
    except:
        return False


def generate_customer_code():
    """បង្កើតលេខកូដអតិថិជនស្វ័យប្រវត្តិ"""
    last = customers_col.find_one(sort=[('_id', DESCENDING)])
    if last and 'code' in last:
        try:
            last_num = int(last['code'].replace('CUS-', ''))
            return f'CUS-{last_num + 1:03d}'
        except:
            pass
    return 'CUS-001'


# ============================================================
# ===== LOAN FUNCTIONS =====
# ============================================================

def get_loans_paginated(page=1, per_page=50, status=''):
    skip = (page - 1) * per_page
    query = {}
    if status:
        query['status'] = status

    pipeline = [
        {'$match': query},
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

    loans = list(loans_col.aggregate(pipeline))
    result = []
    for loan in loans:
        customer = loan.get('customer_info', {}) or {}
        result.append({
            'id': loan['_id'],
            'customer_id': loan.get('customer_id'),
            'customer_code': customer.get('code', ''),
            'customer_name': customer.get('name', ''),
            'customer_gender': customer.get('gender', ''),
            'customer_phone': customer.get('phone', ''),
            'customer_id_card': customer.get('id_card', ''),
            'customer_address': customer.get('address', ''),
            'guarantor_name': customer.get('guarantor_name', ''),
            'guarantor_gender': customer.get('guarantor_gender', ''),
            'guarantor_id_card': customer.get('guarantor_id_card', ''),
            'guarantor_phone': customer.get('guarantor_phone', ''),
            'guarantor_address': customer.get('guarantor_address', ''),
            'relation': customer.get('relation', ''),
            'loan_amount': loan.get('loan_amount', 0),
            'currency': loan.get('currency', 'USD'),
            'interest_rate': loan.get('interest_rate', 0),
            'total_interest': loan.get('total_interest', 0),
            'amount_paid': loan.get('amount_paid', 0),
            'remaining_balance': loan.get('remaining_balance', 0),
            'status': loan.get('status', 'Pending'),
            'co_officer': loan.get('co_officer', ''),
            'loan_date': loan.get('loan_date', ''),
            'due_date': loan.get('due_date', ''),
            'duration_num': loan.get('duration_num', 0),
            'duration_type': loan.get('duration_type', 'ថ្ងៃ'),
            'loan_code': loan.get('loan_code', ''),
            'created_at': loan.get('created_at', '')
        })
    return result


def get_loans_by_officer(officer_name, page=1, per_page=50, status=''):
    skip = (page - 1) * per_page
    query = {'co_officer': officer_name}
    if status:
        query['status'] = status

    pipeline = [
        {'$match': query},
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

    loans = list(loans_col.aggregate(pipeline))
    result = []
    for loan in loans:
        customer = loan.get('customer_info', {}) or {}
        result.append({
            'id': loan['_id'],
            'customer_id': loan.get('customer_id'),
            'customer_code': customer.get('code', ''),
            'customer_name': customer.get('name', ''),
            'customer_gender': customer.get('gender', ''),
            'customer_phone': customer.get('phone', ''),
            'customer_id_card': customer.get('id_card', ''),
            'customer_address': customer.get('address', ''),
            'guarantor_name': customer.get('guarantor_name', ''),
            'guarantor_gender': customer.get('guarantor_gender', ''),
            'guarantor_id_card': customer.get('guarantor_id_card', ''),
            'guarantor_phone': customer.get('guarantor_phone', ''),
            'guarantor_address': customer.get('guarantor_address', ''),
            'relation': customer.get('relation', ''),
            'loan_amount': loan.get('loan_amount', 0),
            'currency': loan.get('currency', 'USD'),
            'interest_rate': loan.get('interest_rate', 0),
            'total_interest': loan.get('total_interest', 0),
            'amount_paid': loan.get('amount_paid', 0),
            'remaining_balance': loan.get('remaining_balance', 0),
            'status': loan.get('status', 'Pending'),
            'co_officer': loan.get('co_officer', ''),
            'loan_date': loan.get('loan_date', ''),
            'due_date': loan.get('due_date', ''),
            'duration_num': loan.get('duration_num', 0),
            'duration_type': loan.get('duration_type', 'ថ្ងៃ'),
            'loan_code': loan.get('loan_code', ''),
            'created_at': loan.get('created_at', '')
        })
    return result


def count_loans(status=''):
    query = {}
    if status:
        query['status'] = status
    return loans_col.count_documents(query)


def get_loan_by_id(loan_id):
    try:
        loan = loans_col.find_one({'_id': int(loan_id)})
        return _to_dict(loan)
    except:
        return None


def create_loan(data):
    loan_id = get_next_sequence('loans')
    doc = {
        '_id': loan_id,
        'customer_id': int(data.get('customer_id', 0)),
        'loan_code': data.get('loan_code') or generate_loan_code(),
        'loan_amount': float(data.get('loan_amount', 0)),
        'currency': data.get('currency', 'USD'),
        'interest_rate': float(data.get('interest_rate', 0)),
        'duration_num': int(data.get('duration_num', 0)),
        'duration_type': data.get('duration_type', 'ថ្ងៃ'),
        'calc_type': int(data.get('calc_type', 1)),
        'service_fee': float(data.get('service_fee', 0)),
        'total_interest': float(data.get('total_interest', 0)),
        'total_amount': float(data.get('total_amount', 0)),
        'amount_paid': float(data.get('amount_paid', 0)),
        'remaining_balance': float(data.get('remaining_balance', 0)),
        'loan_date': data.get('loan_date', ''),
        'due_date': data.get('due_date', ''),
        'co_officer': data.get('co_officer', ''),
        'purpose': data.get('purpose', ''),
        'status': data.get('status', 'Pending'),
        'created_at': datetime.now()
    }
    loans_col.insert_one(doc)
    return loan_id


def update_loan(loan_id, data):
    update_fields = {}
    for key in ['customer_id', 'loan_amount', 'currency', 'interest_rate',
                'duration_num', 'duration_type', 'calc_type', 'service_fee',
                'total_interest', 'total_amount', 'amount_paid',
                'remaining_balance', 'loan_date', 'due_date', 'co_officer',
                'purpose', 'status']:
        if key in data:
            update_fields[key] = data[key]

    update_fields['updated_at'] = datetime.now()

    if update_fields:
        loans_col.update_one({'_id': int(loan_id)}, {'$set': update_fields})
    return True


def update_loan_status(loan_id, status):
    loans_col.update_one(
        {'_id': int(loan_id)},
        {'$set': {'status': status, 'updated_at': datetime.now()}}
    )
    return True


def update_loan_payment(loan_id, amount_paid, remaining, status):
    loans_col.update_one(
        {'_id': int(loan_id)},
        {'$set': {
            'amount_paid': amount_paid,
            'remaining_balance': remaining,
            'status': status,
            'updated_at': datetime.now()
        }}
    )
    return True


def delete_loan(loan_id):
    try:
        loans_col.delete_one({'_id': int(loan_id)})
        return True
    except:
        return False


def generate_loan_code():
    """បង្កើតលេខកូដកម្ចីស្វ័យប្រវត្តិ"""
    last = loans_col.find_one(sort=[('_id', DESCENDING)])
    if last and 'loan_code' in last:
        try:
            last_num = int(last['loan_code'].replace('LN-', ''))
            return f'LN-{last_num + 1:04d}'
        except:
            pass
    return 'LN-0001'


# ============================================================
# ===== OFFICER FUNCTIONS =====
# ============================================================

def get_all_officers():
    officers = officers_col.find().sort('_id', DESCENDING)
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
        'code': data.get('code', ''),
        'name': data.get('name', ''),
        'phone': data.get('phone', ''),
        'address': data.get('address', ''),
        'created_at': datetime.now()
    }
    officers_col.insert_one(doc)
    return officer_id


def update_officer(officer_id, data):
    update_fields = {}
    for key in ['code', 'name', 'phone', 'address']:
        if key in data:
            update_fields[key] = data[key]

    if update_fields:
        officers_col.update_one({'_id': int(officer_id)}, {'$set': update_fields})
    return True


def delete_officer(officer_id):
    officers_col.delete_one({'_id': int(officer_id)})
    return True


# ============================================================
# ===== ACTIVITY FUNCTIONS =====
# ============================================================

def log_activity(customer_id, loan_id, action, description, user_id=None):
    activity_id = get_next_sequence('activities')
    doc = {
        '_id': activity_id,
        'user_id': user_id,
        'customer_id': customer_id,
        'loan_id': loan_id,
        'action': action,
        'description': description,
        'status': 'Pending',
        'created_at': datetime.now()
    }
    activities_col.insert_one(doc)
    return activity_id


def get_activities(limit=20):
    activities = activities_col.find().sort('_id', DESCENDING).limit(limit)
    return _to_dict_list(activities)


# ============================================================
# ===== PAYMENT HISTORY =====
# ============================================================

def record_payment(loan_id, period, amount, payment_method='cash', notes='', penalty=0):
    payment_id = get_next_sequence('payment_history')
    doc = {
        '_id': payment_id,
        'loan_id': int(loan_id),
        'period': int(period),
        'amount': float(amount),
        'payment_method': payment_method,
        'penalty': float(penalty),
        'notes': notes,
        'created_at': datetime.now()
    }
    payment_history_col.insert_one(doc)
    return payment_id


def get_payment_history():
    pipeline = [
        {'$sort': {'_id': DESCENDING}},
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

    payments = list(payment_history_col.aggregate(pipeline))
    result = []
    for p in payments:
        loan = p.get('loan_info', {}) or {}
        customer = p.get('customer_info', {}) or {}
        result.append({
            'id': p['_id'],
            'loan_id': p.get('loan_id'),
            'loan_code': loan.get('loan_code', ''),
            'customer_name': customer.get('name', ''),
            'amount': p.get('amount', 0),
            'currency': loan.get('currency', 'USD'),
            'payment_method': p.get('payment_method', 'cash'),
            'co_officer': loan.get('co_officer', ''),
            'penalty': p.get('penalty', 0),
            'notes': p.get('notes', ''),
            'created_at': p.get('created_at', '').strftime('%Y-%m-%d %H:%M') if hasattr(p.get('created_at'), 'strftime') else str(p.get('created_at', ''))
        })
    return result


def get_payment_history_by_loan(loan_id):
    payments = payment_history_col.find({'loan_id': int(loan_id)}).sort('period', ASCENDING)
    result = []
    for p in payments:
        result.append({
            'period': p.get('period'),
            'amount': p.get('amount'),
            'payment_method': p.get('payment_method', 'cash'),
            'payment_date': p.get('created_at', '').strftime('%Y-%m-%d') if hasattr(p.get('created_at'), 'strftime') else '',
        })
    return result


# ============================================================
# ===== COLLECTION FUNCTIONS =====
# ============================================================

def get_collection_loans(type='good', page=1, per_page=100):
    """ទាញយកកម្ចីសម្រាប់ការប្រមូលប្រាក់"""
    from datetime import datetime
    today = datetime.now().date()
    skip = (page - 1) * per_page

    if type == 'good':
        # កម្ចីល្អ - due_date >= today
        query = {
            'status': {'$in': ['Approved', 'Pending']},
            'remaining_balance': {'$gt': 0},
            'due_date': {'$gte': today.isoformat()}
        }
    elif type == 'late':
        # កម្ចីយឺត - ហួសកំណត់ 1-30 ថ្ងៃ
        query = {
            'status': {'$in': ['Approved', 'Pending']},
            'remaining_balance': {'$gt': 0},
            'due_date': {'$lt': today.isoformat()}
        }
    elif type == 'bad':
        # កម្ចីខូច - status = Bad Debt
        query = {'status': 'Bad Debt'}
    else:
        return []

    pipeline = [
        {'$match': query},
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

    loans = list(loans_col.aggregate(pipeline))
    result = []

    for loan in loans:
        customer = loan.get('customer_info', {}) or {}

        # ===== គណនាថ្ងៃយឺត =====
        days_overdue = 0
        try:
            if loan.get('due_date'):
                due = datetime.strptime(loan['due_date'], '%Y-%m-%d').date()
                if today > due:
                    days_overdue = (today - due).days
        except:
            pass

        # ===== គណនាទឹកប្រាក់ត្រូវបង់ =====
        remaining = loan.get('remaining_balance', 0)
        principal = loan.get('loan_amount', 0)
        interest = loan.get('total_interest', 0)

        # ===== ពិន័យ =====
        penalty = 0
        if type in ['late', 'bad'] and days_overdue > 0:
            if days_overdue > 30:
                penalty = days_overdue * 5000  # សម្រាប់ខូច
            else:
                penalty = days_overdue * 3000  # សម្រាប់យឺត

        result.append({
            'id': loan['_id'],
            'loan_code': loan.get('loan_code', ''),
            'customer_code': customer.get('code', ''),
            'customer_name': customer.get('name', ''),
            'customer_phone': customer.get('phone', ''),
            'customer_address': customer.get('address', ''),
            'loan_amount': principal,
            'currency': loan.get('currency', 'USD'),
            'total_interest': interest,
            'remaining_balance': remaining,
            'due_date': loan.get('due_date', ''),
            'co_officer': loan.get('co_officer', ''),
            'status': loan.get('status', 'Pending'),
            'days_overdue': days_overdue,
            'total_due': remaining,
            'principal_due': principal,
            'interest_due': interest,
            'penalty': penalty
        })

    return result


def get_collection_loans_by_officer(type, officer_name, page=1, per_page=100):
    """ទាញយកកម្ចីសម្រាប់ការប្រមូលប្រាក់ តាម CO"""
    from datetime import datetime
    today = datetime.now().date()
    skip = (page - 1) * per_page

    if type == 'good':
        query = {
            'status': {'$in': ['Approved', 'Pending']},
            'remaining_balance': {'$gt': 0},
            'due_date': {'$gte': today.isoformat()},
            'co_officer': officer_name
        }
    elif type == 'late':
        query = {
            'status': {'$in': ['Approved', 'Pending']},
            'remaining_balance': {'$gt': 0},
            'due_date': {'$lt': today.isoformat()},
            'co_officer': officer_name
        }
    elif type == 'bad':
        query = {'status': 'Bad Debt', 'co_officer': officer_name}
    else:
        return []

    pipeline = [
        {'$match': query},
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

    loans = list(loans_col.aggregate(pipeline))
    result = []

    for loan in loans:
        customer = loan.get('customer_info', {}) or {}

        days_overdue = 0
        try:
            if loan.get('due_date'):
                due = datetime.strptime(loan['due_date'], '%Y-%m-%d').date()
                if today > due:
                    days_overdue = (today - due).days
        except:
            pass

        penalty = 0
        if type in ['late', 'bad'] and days_overdue > 0:
            penalty = days_overdue * (5000 if days_overdue > 30 else 3000)

        result.append({
            'id': loan['_id'],
            'loan_code': loan.get('loan_code', ''),
            'customer_code': customer.get('code', ''),
            'customer_name': customer.get('name', ''),
            'customer_phone': customer.get('phone', ''),
            'customer_address': customer.get('address', ''),
            'loan_amount': loan.get('loan_amount', 0),
            'currency': loan.get('currency', 'USD'),
            'total_interest': loan.get('total_interest', 0),
            'remaining_balance': loan.get('remaining_balance', 0),
            'due_date': loan.get('due_date', ''),
            'co_officer': loan.get('co_officer', ''),
            'status': loan.get('status', 'Pending'),
            'days_overdue': days_overdue,
            'total_due': loan.get('remaining_balance', 0),
            'principal_due': loan.get('loan_amount', 0),
            'interest_due': loan.get('total_interest', 0),
            'penalty': penalty
        })

    return result


def count_collection_loans(type='good'):
    from datetime import datetime
    today = datetime.now().date()

    if type == 'good':
        query = {
            'status': {'$in': ['Approved', 'Pending']},
            'remaining_balance': {'$gt': 0},
            'due_date': {'$gte': today.isoformat()}
        }
    elif type == 'late':
        query = {
            'status': {'$in': ['Approved', 'Pending']},
            'remaining_balance': {'$gt': 0},
            'due_date': {'$lt': today.isoformat()}
        }
    elif type == 'bad':
        query = {'status': 'Bad Debt'}
    else:
        return 0

    return loans_col.count_documents(query)


def get_collection_summary():
    """សង្ខេបការប្រមូលប្រាក់"""
    good_count = count_collection_loans('good')
    late_count = count_collection_loans('late')
    bad_count = count_collection_loans('bad')

    return {
        'good': {'count': good_count, 'total': 0},
        'late': {'count': late_count, 'total': 0},
        'bad': {'count': bad_count, 'total': 0}
    }


# ============================================================
# ===== PAWN FUNCTIONS =====
# ============================================================

def get_pawns_paginated(page=1, per_page=50, status=''):
    skip = (page - 1) * per_page
    query = {}
    if status:
        query['status'] = status

    pipeline = [
        {'$match': query},
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
        result.append({
            'id': p['_id'],
            'pawn_code': p.get('pawn_code', ''),
            'customer_id': p.get('customer_id'),
            'customer_name': customer.get('name', ''),
            'customer_phone': customer.get('phone', ''),
            'item_name': p.get('item_name', ''),
            'item_category': p.get('item_category', ''),
            'item_value': p.get('item_value', 0),
            'loan_amount': p.get('loan_amount', 0),
            'currency': p.get('currency', 'USD'),
            'interest_rate': p.get('interest_rate', 0),
            'interest_amount': p.get('interest_amount', 0),
            'total_amount': p.get('total_amount', 0),
            'amount_paid': p.get('amount_paid', 0),
            'remaining_balance': p.get('remaining_balance', 0),
            'pawn_date': p.get('pawn_date', ''),
            'due_date': p.get('due_date', ''),
            'status': p.get('status', 'Active'),
            'notes': p.get('notes', '')
        })
    return result


def count_pawns(status=''):
    query = {}
    if status:
        query['status'] = status
    return pawns_col.count_documents(query)


def get_pawn_by_id(pawn_id):
    try:
        pawn = pawns_col.find_one({'_id': int(pawn_id)})
        return _to_dict(pawn)
    except:
        return None


def create_pawn(data):
    pawn_id = get_next_sequence('pawns')
    doc = {
        '_id': pawn_id,
        'pawn_code': data.get('pawn_code') or f'PN-{pawn_id:04d}',
        'customer_id': int(data.get('customer_id', 0)),
        'item_name': data.get('item_name', ''),
        'item_category': data.get('item_category', ''),
        'item_value': float(data.get('item_value', 0)),
        'item_description': data.get('item_description', ''),
        'loan_amount': float(data.get('loan_amount', 0)),
        'currency': data.get('currency', 'USD'),
        'interest_rate': float(data.get('interest_rate', 0)),
        'interest_amount': float(data.get('interest_amount', 0)),
        'total_amount': float(data.get('total_amount', 0)),
        'amount_paid': 0,
        'remaining_balance': float(data.get('total_amount', 0)),
        'pawn_date': data.get('pawn_date', ''),
        'due_date': data.get('due_date', ''),
        'co_officer': data.get('co_officer', ''),
        'notes': data.get('notes', ''),
        'status': 'Active',
        'created_at': datetime.now()
    }
    pawns_col.insert_one(doc)
    return pawn_id


def update_pawn(pawn_id, data):
    update_fields = {}
    for key in ['customer_id', 'item_name', 'item_category', 'item_value',
                'item_description', 'loan_amount', 'currency', 'interest_rate',
                'interest_amount', 'total_amount', 'pawn_date', 'due_date',
                'co_officer', 'notes']:
        if key in data:
            update_fields[key] = data[key]

    update_fields['updated_at'] = datetime.now()

    if update_fields:
        pawns_col.update_one({'_id': int(pawn_id)}, {'$set': update_fields})
    return True


def update_pawn_status(pawn_id, status):
    pawns_col.update_one(
        {'_id': int(pawn_id)},
        {'$set': {'status': status, 'updated_at': datetime.now()}}
    )
    return True


def redeem_pawn(pawn_id, amount):
    pawn = pawns_col.find_one({'_id': int(pawn_id)})
    if not pawn:
        return {'error': 'មិនឃើញបញ្ចាំនេះទេ!'}

    new_paid = pawn.get('amount_paid', 0) + amount
    new_remaining = pawn.get('remaining_balance', 0) - amount

    if new_remaining <= 0:
        new_remaining = 0
        status = 'Redeemed'
    else:
        status = 'Active'

    pawns_col.update_one(
        {'_id': int(pawn_id)},
        {'$set': {
            'amount_paid': new_paid,
            'remaining_balance': new_remaining,
            'status': status,
            'updated_at': datetime.now()
        }}
    )
    return {'success': True, 'remaining': new_remaining, 'status': status}


def delete_pawn(pawn_id):
    try:
        pawns_col.delete_one({'_id': int(pawn_id)})
        return True
    except:
        return False


# ============================================================
# ===== EXPENSE FUNCTIONS =====
# ============================================================

def get_all_expenses():
    expenses = expenses_col.find().sort('_id', DESCENDING)
    result = []
    for e in expenses:
        result.append({
            'id': e['_id'],
            'name': e.get('name', ''),
            'amount': e.get('amount', 0),
            'category': e.get('category', ''),
            'expense_date': e.get('expense_date', ''),
            'description': e.get('description', ''),
            'created_at': e.get('created_at', '').strftime('%Y-%m-%d %H:%M') if hasattr(e.get('created_at'), 'strftime') else ''
        })
    return result


def get_expenses_by_date_range(from_date, to_date):
    query = {'expense_date': {'$gte': from_date, '$lte': to_date}}
    expenses = expenses_col.find(query).sort('_id', DESCENDING)
    result = []
    for e in expenses:
        result.append({
            'id': e['_id'],
            'name': e.get('name', ''),
            'amount': e.get('amount', 0),
            'category': e.get('category', ''),
            'expense_date': e.get('expense_date', ''),
            'description': e.get('description', '')
        })
    return result


def get_expense_by_id(expense_id):
    try:
        expense = expenses_col.find_one({'_id': int(expense_id)})
        if expense:
            return {
                'id': expense['_id'],
                'name': expense.get('name', ''),
                'amount': expense.get('amount', 0),
                'category': expense.get('category', ''),
                'expense_date': expense.get('expense_date', ''),
                'description': expense.get('description', '')
            }
        return None
    except:
        return None


def create_expense(data):
    expense_id = get_next_sequence('expenses')
    doc = {
        '_id': expense_id,
        'name': data.get('name', ''),
        'amount': float(data.get('amount', 0)),
        'category': data.get('category', ''),
        'expense_date': data.get('expense_date', datetime.now().strftime('%Y-%m-%d')),
        'description': data.get('description', ''),
        'created_at': datetime.now()
    }
    expenses_col.insert_one(doc)
    return expense_id


def update_expense(expense_id, data):
    update_fields = {}
    for key in ['name', 'amount', 'category', 'expense_date', 'description']:
        if key in data:
            update_fields[key] = data[key]

    if update_fields:
        expenses_col.update_one({'_id': int(expense_id)}, {'$set': update_fields})
    return True


def delete_expense(expense_id):
    try:
        expenses_col.delete_one({'_id': int(expense_id)})
        return True
    except:
        return False


def get_expense_categories():
    categories = expenses_col.distinct('category')
    return [c for c in categories if c]


# ============================================================
# ===== HOLIDAY FUNCTIONS =====
# ============================================================

def get_holidays():
    holidays = holidays_col.find()
    return [h['day'] for h in holidays]


def save_holidays(holidays_list):
    holidays_col.delete_many({})
    if holidays_list:
        holidays_col.insert_many([{'day': d} for d in holidays_list])
    return True


def get_special_holidays():
    holidays = special_holidays_col.find().sort('date', ASCENDING)
    result = []
    for h in holidays:
        result.append({
            'id': h['_id'],
            'name': h.get('name', ''),
            'date': h.get('date', '')
        })
    return result


def add_special_holiday(data):
    holiday_id = get_next_sequence('special_holidays')
    doc = {
        '_id': holiday_id,
        'name': data.get('name', ''),
        'date': data.get('date', '')
    }
    special_holidays_col.insert_one(doc)
    return holiday_id


def delete_special_holiday(holiday_id):
    try:
        special_holidays_col.delete_one({'_id': int(holiday_id)})
        return True
    except:
        return False


def get_next_working_day(start_date, days_offset):
    """ទាញយកថ្ងៃធ្វើការបន្ទាប់ (មិនរាប់ថ្ងៃឈប់សម្រាក)"""
    holidays = get_holidays()
    special_holidays = get_special_holidays()
    special_dates = [h['date'] for h in special_holidays]

    day_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}

    current = start_date
    count = 0
    max_iterations = days_offset * 3 + 100

    while count < days_offset and max_iterations > 0:
        current = current + timedelta(days=1)
        max_iterations -= 1

        day_name = day_map[current.weekday()]
        date_str = current.strftime('%Y-%m-%d')

        if day_name in holidays:
            continue
        if date_str in special_dates:
            continue
        count += 1

    return current


# ============================================================
# ===== PERMISSIONS FUNCTIONS =====
# ============================================================

def save_permissions(role, permissions):
    permissions_col.update_one(
        {'role': role},
        {'$set': {'role': role, 'permissions': permissions}},
        upsert=True
    )
    return True


def get_permissions(role):
    result = permissions_col.find_one({'role': role})
    if result:
        return result.get('permissions', {})
    return {}


# ============================================================
# ===== DASHBOARD FUNCTIONS =====
# ============================================================

def get_dashboard_stats():
    """ទាញយកស្ថិតិសម្រាប់ Dashboard"""
    total_loans = loans_col.count_documents({})
    active_loans = loans_col.count_documents({'status': {'$in': ['Approved', 'Pending']}})
    bad_loans = loans_col.count_documents({'status': 'Bad Debt'})

    # ===== ប្រាក់កម្ចី USD =====
    pipeline_usd = [
        {'$match': {'currency': 'USD'}},
        {'$group': {'_id': None, 'total': {'$sum': '$loan_amount'}}}
    ]
    result_usd = list(loans_col.aggregate(pipeline_usd))
    total_amount_usd = result_usd[0]['total'] if result_usd else 0

    # ===== ប្រាក់កម្ចី KHR =====
    pipeline_khr = [
        {'$match': {'currency': 'KHR'}},
        {'$group': {'_id': None, 'total': {'$sum': '$loan_amount'}}}
    ]
    result_khr = list(loans_col.aggregate(pipeline_khr))
    total_amount_khr = result_khr[0]['total'] if result_khr else 0

    # ===== បំណុល USD =====
    pipeline_debt_usd = [
        {'$match': {'currency': 'USD', 'status': {'$ne': 'Completed'}}},
        {'$group': {'_id': None, 'total': {'$sum': '$remaining_balance'}}}
    ]
    result_debt_usd = list(loans_col.aggregate(pipeline_debt_usd))
    total_debt_usd = result_debt_usd[0]['total'] if result_debt_usd else 0

    # ===== បំណុល KHR =====
    pipeline_debt_khr = [
        {'$match': {'currency': 'KHR', 'status': {'$ne': 'Completed'}}},
        {'$group': {'_id': None, 'total': {'$sum': '$remaining_balance'}}}
    ]
    result_debt_khr = list(loans_col.aggregate(pipeline_debt_khr))
    total_debt_khr = result_debt_khr[0]['total'] if result_debt_khr else 0

    return {
        'total_loans': total_loans,
        'active_loans': active_loans,
        'bad_loans': bad_loans,
        'total_amount_usd': total_amount_usd or 0,
        'total_amount_khr': total_amount_khr or 0,
        'total_debt_usd': total_debt_usd or 0,
        'total_debt_khr': total_debt_khr or 0
    }


def get_dashboard_charts_data():
    """ទាញយកទិន្នន័យសម្រាប់ Charts"""
    from datetime import datetime, timedelta

    # ===== កម្ចីតាមស្ថានភាព =====
    pipeline_status = [
        {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
    ]
    status_result = list(loans_col.aggregate(pipeline_status))
    loans_by_status = {item['_id']: item['count'] for item in status_result if item['_id']}

    # ===== កម្ចីតាមរូបិយប័ណ្ណ =====
    pipeline_currency = [
        {'$group': {'_id': '$currency', 'count': {'$sum': 1}, 'total': {'$sum': '$loan_amount'}}}
    ]
    currency_result = list(loans_col.aggregate(pipeline_currency))
    loans_by_currency = {}
    for item in currency_result:
        if item['_id']:
            loans_by_currency[item['_id']] = {
                'count': item['count'],
                'total': item.get('total', 0)
            }

    # ===== កម្ចីប្រចាំខែ (6 ខែចុងក្រោយ) =====
    six_months_ago = datetime.now() - timedelta(days=180)
    pipeline_monthly = [
        {'$match': {'created_at': {'$gte': six_months_ago}}},
        {'$group': {
            '_id': {'$dateToString': {'format': '%Y-%m', 'date': '$created_at'}},
            'count': {'$sum': 1},
            'total': {'$sum': '$loan_amount'}
        }},
        {'$sort': {'_id': 1}}
    ]
    monthly_result = list(loans_col.aggregate(pipeline_monthly))
    monthly_loans = [
        {'month': item['_id'], 'count': item['count'], 'total': item.get('total', 0)}
        for item in monthly_result
    ]

    # ===== ការប្រមូលប្រាក់ប្រចាំខែ =====
    pipeline_collection = [
        {'$match': {'created_at': {'$gte': six_months_ago}}},
        {'$group': {
            '_id': {'$dateToString': {'format': '%Y-%m', 'date': '$created_at'}},
            'count': {'$sum': 1},
            'total': {'$sum': '$amount'}
        }},
        {'$sort': {'_id': 1}}
    ]
    collection_result = list(payment_history_col.aggregate(pipeline_collection))
    monthly_collections = [
        {'month': item['_id'], 'count': item['count'], 'total': item.get('total', 0)}
        for item in collection_result
    ]

    return {
        'loans_by_status': loans_by_status,
        'loans_by_currency': loans_by_currency,
        'monthly_loans': monthly_loans,
        'monthly_collections': monthly_collections
    }

# ============================================================
# ===== DASHBOARD ADVANCED FUNCTIONS =====
# ============================================================

def get_dashboard_full_stats():
    """ទាញយកស្ថិតិពេញលេញសម្រាប់ Dashboard"""
    from datetime import datetime, timedelta

    # ===== ១. ទុនទំលាក់សរុប (Disbursement) =====
    pipeline_disb_usd = [
        {'$match': {'currency': 'USD'}},
        {'$group': {'_id': None, 'total': {'$sum': '$loan_amount'}}}
    ]
    disb_usd = list(loans_col.aggregate(pipeline_disb_usd))
    total_disbursement_usd = disb_usd[0]['total'] if disb_usd else 0

    pipeline_disb_khr = [
        {'$match': {'currency': 'KHR'}},
        {'$group': {'_id': None, 'total': {'$sum': '$loan_amount'}}}
    ]
    disb_khr = list(loans_col.aggregate(pipeline_disb_khr))
    total_disbursement_khr = disb_khr[0]['total'] if disb_khr else 0

    # ===== ២. ការប្រាក់សរុប (Total Interest) =====
    pipeline_interest_usd = [
        {'$match': {'currency': 'USD'}},
        {'$group': {'_id': None, 'total': {'$sum': '$total_interest'}}}
    ]
    interest_usd = list(loans_col.aggregate(pipeline_interest_usd))
    total_interest_usd = interest_usd[0]['total'] if interest_usd else 0

    pipeline_interest_khr = [
        {'$match': {'currency': 'KHR'}},
        {'$group': {'_id': None, 'total': {'$sum': '$total_interest'}}}
    ]
    interest_khr = list(loans_col.aggregate(pipeline_interest_khr))
    total_interest_khr = interest_khr[0]['total'] if interest_khr else 0

    # ===== ៣. ទឹកប្រាក់សងសរុប (Total Collected) =====
    pipeline_collect_usd = [
        {'$match': {'currency': 'USD'}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount_paid'}}}
    ]
    collect_usd = list(loans_col.aggregate(pipeline_collect_usd))
    total_collection_usd = collect_usd[0]['total'] if collect_usd else 0

    pipeline_collect_khr = [
        {'$match': {'currency': 'KHR'}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount_paid'}}}
    ]
    collect_khr = list(loans_col.aggregate(pipeline_collect_khr))
    total_collection_khr = collect_khr[0]['total'] if collect_khr else 0

    # ===== ៤. បំណុលសរុបរួមការប្រាក់ (Total Debt with Interest) =====
    pipeline_debt_usd = [
        {'$match': {'currency': 'USD', 'status': {'$nin': ['Completed', 'Rejected']}}},
        {'$group': {'_id': None, 'total': {'$sum': '$remaining_balance'}}}
    ]
    debt_usd = list(loans_col.aggregate(pipeline_debt_usd))
    total_debt_usd = debt_usd[0]['total'] if debt_usd else 0

    pipeline_debt_khr = [
        {'$match': {'currency': 'KHR', 'status': {'$nin': ['Completed', 'Rejected']}}},
        {'$group': {'_id': None, 'total': {'$sum': '$remaining_balance'}}}
    ]
    debt_khr = list(loans_col.aggregate(pipeline_debt_khr))
    total_debt_khr = debt_khr[0]['total'] if debt_khr else 0

    # ===== ៥. ចំណាយសរុប (Total Expense) =====
    pipeline_expense = [
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    expense_result = list(expenses_col.aggregate(pipeline_expense))
    total_expense = expense_result[0]['total'] if expense_result else 0

    # ===== ៦. ចំណូលសុទ្ធ (Net Income) =====
    net_income = (total_interest_usd + total_interest_khr) - total_expense

    return {
        'total_disbursement_usd': total_disbursement_usd or 0,
        'total_disbursement_khr': total_disbursement_khr or 0,
        'total_interest_usd': total_interest_usd or 0,
        'total_interest_khr': total_interest_khr or 0,
        'total_collection_usd': total_collection_usd or 0,
        'total_collection_khr': total_collection_khr or 0,
        'total_debt_usd': total_debt_usd or 0,
        'total_debt_khr': total_debt_khr or 0,
        'total_expense': total_expense or 0,
        'net_income': net_income or 0,
        'total_loans': loans_col.count_documents({}),
        'active_loans': loans_col.count_documents({'status': {'$in': ['Approved', 'Pending']}}),
        'bad_loans': loans_col.count_documents({'status': 'Bad Debt'}),
        'total_customers': customers_col.count_documents({})
    }


def get_calendar_data(year, month):
    """ទាញយកទិន្នន័យសម្រាប់ Calendar តាមខែ/ឆ្នាំ"""
    from datetime import datetime, timedelta

    # ===== ថ្ងៃទី ១ និងចុងក្រោយនៃខែ =====
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    start_str = first_day.strftime('%Y-%m-%d')
    end_str = last_day.strftime('%Y-%m-%d')

    # ===== ១. កម្ចីថ្មីក្នុងខែ =====
    loans_in_month = list(loans_col.find({
        'loan_date': {'$gte': start_str, '$lte': end_str}
    }))

    # ===== ២. ការប្រមូលប្រាក់ក្នុងខែ =====
    payments_in_month = list(payment_history_col.find({
        '$expr': {
            '$and': [
                {'$gte': [{'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}}, start_str]},
                {'$lte': [{'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}}, end_str]}
            ]
        }
    }))

    # ===== ៣. ចំណាយក្នុងខែ =====
    expenses_in_month = list(expenses_col.find({
        'expense_date': {'$gte': start_str, '$lte': end_str}
    }))

    # ===== ៤. បង្កើត Daily Summary =====
    daily_data = {}
    current = first_day
    while current <= last_day:
        date_str = current.strftime('%Y-%m-%d')
        daily_data[date_str] = {
            'date': date_str,
            'day': current.day,
            'loans_count': 0,
            'loans_amount_usd': 0,
            'loans_amount_khr': 0,
            'collections_usd': 0,
            'collections_khr': 0,
            'expenses': 0,
            'events': []
        }
        current += timedelta(days=1)

    # ===== បន្ថែមកម្ចី =====
    for loan in loans_in_month:
        date_str = loan.get('loan_date', '')
        if date_str in daily_data:
            daily_data[date_str]['loans_count'] += 1
            if loan.get('currency') == 'USD':
                daily_data[date_str]['loans_amount_usd'] += loan.get('loan_amount', 0)
            else:
                daily_data[date_str]['loans_amount_khr'] += loan.get('loan_amount', 0)

    # ===== បន្ថែមការប្រមូល =====
    for payment in payments_in_month:
        created = payment.get('created_at')
        if created:
            date_str = created.strftime('%Y-%m-%d') if hasattr(created, 'strftime') else str(created)[:10]
            if date_str in daily_data:
                amount = payment.get('amount', 0)
                # ===== ពិនិត្យ currency =====
                daily_data[date_str]['collections_usd'] += amount

    # ===== បន្ថែមចំណាយ =====
    for exp in expenses_in_month:
        date_str = exp.get('expense_date', '')
        if date_str in daily_data:
            daily_data[date_str]['expenses'] += exp.get('amount', 0)
            daily_data[date_str]['events'].append({
                'type': 'expense',
                'name': exp.get('name', ''),
                'amount': exp.get('amount', 0)
            })

    # ===== បន្ថែមព្រឹត្តិការណ៍កម្ចី =====
    for loan in loans_in_month:
        date_str = loan.get('loan_date', '')
        if date_str in daily_data:
            daily_data[date_str]['events'].append({
                'type': 'loan',
                'code': loan.get('loan_code', ''),
                'amount': loan.get('loan_amount', 0),
                'currency': loan.get('currency', 'USD')
            })

    # ===== សរុបខែ =====
    monthly_summary = {
        'total_loans': len(loans_in_month),
        'total_loans_usd': sum(l.get('loan_amount', 0) for l in loans_in_month if l.get('currency') == 'USD'),
        'total_loans_khr': sum(l.get('loan_amount', 0) for l in loans_in_month if l.get('currency') == 'KHR'),
        'total_collections': sum(p.get('amount', 0) for p in payments_in_month),
        'total_expenses': sum(e.get('amount', 0) for e in expenses_in_month),
    }

    return {
        'year': year,
        'month': month,
        'days': list(daily_data.values()),
        'summary': monthly_summary
    }

# ============================================================
# ===== INITIALIZATION =====
# ============================================================

def init_db():
    """បង្កើត Index និង Admin User ដំបូង"""
    # ===== បង្កើត Index =====
    users_col.create_index('username', unique=True)
    customers_col.create_index('code', unique=True)
    loans_col.create_index('loan_code', unique=True)
    pawns_col.create_index('pawn_code', unique=True)

    # ===== បង្កើត Admin User ដំបូង =====
    if users_col.count_documents({}) == 0:
        create_user({
            'username': 'admin',
            'password': 'admin123',
            'full_name': 'Administrator',
            'role': 'admin'
        })
        print("✅ Created default admin user: admin / admin123")

    print(f"✅ MongoDB initialized: {DB_NAME}")


# ===== ហៅ init ពេល Import =====
try:
    init_db()
except Exception as e:
    print(f"⚠️ Init DB warning: {e}")
