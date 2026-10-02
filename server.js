const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(cors());

// ==========================================
// ១. MONGODB CONNECTION & SCHEMAS
// ==========================================
mongoose.connect(process.env.MONGO_URI)
.then(() => console.log('MongoDB Connected Successfully!'))
.catch((err) => console.log('DB Connection Error:', err));

// Borrower Schema
const borrowerSchema = new mongoose.Schema({
    code: String,
    name: String,
    gender: String,
    phone: String,
    dob: String,
    nationalId: String,
    address: String,
    guarantor: { name: String, phone: String, relation: String }
});
const Borrower = mongoose.model('Borrower', borrowerSchema);

// Loan Schema
const loanSchema = new mongoose.Schema({
    loanCode: String,
    borrowerId: { type: mongoose.Schema.Types.ObjectId, ref: 'Borrower' },
    amount: Number,
    interestRate: Number,
    duration: Number,
    paymentFrequency: String, // Daily, Weekly, Monthly
    coOfficer: String,
    status: { type: String, default: 'Pending' }, // Pending, Active, Bad Loan, Closed, Rejected
    schedule: [{ installmentNumber: Number, dueDate: String, totalDue: Number, status: { type: String, default: 'Unpaid' } }],
    createdAt: { type: Date, default: Date.now }
});
const Loan = mongoose.model('Loan', loanSchema);

// Transaction (Repayment & Cashier) Schema
const transactionSchema = new mongoose.Schema({
    receiptNo: String,
    loanId: { type: mongoose.Schema.Types.ObjectId, ref: 'Loan' },
    coOfficer: String,
    totalPaid: Number,
    receivedByCashier: { type: Boolean, default: false }, // Pending or Approved by Cashier
    paymentDate: { type: Date, default: Date.now }
});
const Transaction = mongoose.model('Transaction', transactionSchema);

// Expense Schema
const expenseSchema = new mongoose.Schema({ title: String, amount: Number, date: { type: Date, default: Date.now } });
const Expense = mongoose.model('Expense', expenseSchema);

// User & Staff Schema
const userSchema = new mongoose.Schema({ username: String, password: String, role: String, active: { type: Boolean, default: true } });
const User = mongoose.model('User', userSchema);

const staffSchema = new mongoose.Schema({ name: String, role: String, phone: String, address: String });
const Staff = mongoose.model('Staff', staffSchema);


// ==========================================
// ២. API ROUTES
// ==========================================
app.get('/api/stats', async (req, res) => {
    try {
        const borrowersCount = await Borrower.countDocuments();
        const activeLoans = await Loan.countDocuments({ status: 'Active' });
        const badLoans = await Loan.countDocuments({ status: 'Bad Loan' });
        const totalCollected = await Transaction.aggregate([{ $group: { _id: null, total: { $sum: '$totalPaid' } } }]);
        res.json({ borrowersCount, activeLoans, badLoans, totalCollected: totalCollected[0]?.total || 0 });
    } catch(err) { res.status(500).json({ error: err.message }); }
});

app.get('/api/borrowers', async (req, res) => res.json(await Borrower.find()));
app.post('/api/borrowers', async (req, res) => res.status(201).json(await new Borrower(req.body).save()));
app.delete('/api/borrowers/:id', async (req, res) => res.json(await Borrower.findByIdAndDelete(req.params.id)));

app.get('/api/loans', async (req, res) => res.json(await Loan.find().populate('borrowerId')));
app.post('/api/loans', async (req, res) => {
    try {
        const data = req.body;
        data.schedule = [{ installmentNumber: 1, dueDate: '2026-05-01', totalDue: data.amount + (data.amount * data.interestRate / 100) }];
        res.status(201).json(await new Loan(data).save());
    } catch(err) { res.status(400).json({ error: err.message }); }
});
app.put('/api/loans/:id/status', async (req, res) => res.json(await Loan.findByIdAndUpdate(req.params.id, { status: req.body.status }, { new: true })));
app.delete('/api/loans/:id', async (req, res) => res.json(await Loan.findByIdAndDelete(req.params.id)));

app.get('/api/transactions', async (req, res) => res.json(await Transaction.find().populate({ path: 'loanId', populate: { path: 'borrowerId' } })));
app.post('/api/transactions', async (req, res) => res.status(201).json(await new Transaction(req.body).save()));
app.put('/api/transactions/approve/:id', async (req, res) => res.json(await Transaction.findByIdAndUpdate(req.params.id, { receivedByCashier: true }, { new: true })));

app.get('/api/expenses', async (req, res) => res.json(await Expense.find()));
app.post('/api/expenses', async (req, res) => res.status(201).json(await new Expense(req.body).save()));

app.get('/api/staff', async (req, res) => res.json(await Staff.find()));
app.post('/api/staff', async (req, res) => res.status(201).json(await new Staff(req.body).save()));


// ==========================================
// ៣. FRONTEND SIDEBAR & UI INTERFACE
// ==========================================
app.get('/', (req, res) => {
    res.send(`
        <!DOCTYPE html>
        <html lang="km">
        <head>
            <meta charset="UTF-8">
            <title>ប្រព័ន្ធគ្រប់គ្រងកម្ចី MFI</title>
            <style>
                * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Khmer OS Battambang', sans-serif; }
                body { display: flex; height: 100vh; background: #f4f6f9; overflow: hidden; }
                /* Sidebar */
                .sidebar { width: 260px; background: #1e293b; color: white; display: flex; flex-direction: column; }
                .sidebar h2 { padding: 20px; font-size: 18px; text-align: center; background: #0f172a; border-bottom: 1px solid #334155; }
                .sidebar a { padding: 12px 20px; color: #cbd5e1; text-decoration: none; display: block; transition: 0.3s; cursor: pointer; font-size: 14px; border-left: 4px solid transparent; }
                .sidebar a:hover, .sidebar a.active { background: #334155; color: white; border-left-color: #38bdf8; }
                .submenu { padding-left: 20px; background: #0f172a; display: none; }
                .submenu.show { display: block; }
                /* Main Content */
                .main-content { flex: 1; display: flex; flex-direction: column; overflow-y: auto; }
                header { background: white; padding: 15px 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 18px; font-weight: bold; color: #334155; }
                .content-body { padding: 25px; flex: 1; }
                .section { display: none; }
                .section.active { display: block; }
                /* UI Elements */
                .card-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 25px; }
                .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }
                .card h3 { font-size: 24px; color: #0284c7; margin-top: 5px; }
                table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
                th, td { padding: 12px 15px; border-bottom: 1px solid #e2e8f0; text-align: center; font-size: 13px; }
                th { background: #f8fafc; color: #475569; }
                .btn { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; color: white; margin: 2px; }
                .btn-green { background: #10b981; } .btn-blue { background: #0284c7; } .btn-red { background: #ef4444; } .btn-yellow { background: #f59e0b; }
                .form-group { margin-bottom: 15px; }
                .form-group label { display: block; margin-bottom: 5px; font-size: 13px; font-weight: bold; }
                .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="sidebar">
                <h2>ប្រព័ន្ធគ្រប់គ្រងកម្ចី</h2>
                <a onclick="showSection('dashboard', this)">1. Dashboard</a>
                <a onclick="showSection('borrowers', this)">2. អតិថិជន</a>
                <a onclick="showSection('loans', this)">3. កម្ចី (សកម្ម / ខូច)</a>
                <a onclick="showSection('collections', this)">4. ប្រមូលប្រាក់</a>
                <a onclick="showSection('payments', this)">5. ទូរទាត់</a>
                <a onclick="toggleSubmenu()">6. របាយការណ៍ ▾</a>
                <div id="reportSub" class="submenu">
                    <a onclick="showSection('rep-collection', this)">- របាយការណ៍ប្រមូលប្រាក់</a>
                    <a onclick="showSection('rep-expense', this)">- របាយការណ៍ចំណាយ</a>
                    <a onclick="showSection('rep-cashier', this)">- របាយការណ៍បេឡា</a>
                    <a onclick="showSection('rep-balance', this)">- សមតុល្យសរុប</a>
                </div>
                <a onclick="showSection('settings', this)">7. ការកំណត់</a>
                <a onclick="alert('ប្ដូរពាក្យសម្ងាត់')">8. ប្ដូរពាក្យសម្ងាត់</a>
                <a onclick="alert('ចាកចេញដោយជោគជ័យ')" style="color: #ef4444;">9. ចាកចេញ</a>
            </div>

            <div class="main-content">
                <header id="headerTitle">Dashboard</header>
                <div class="content-body">
                    
                    <!-- 1. DASHBOARD -->
                    <div id="dashboard" class="section active">
                        <div class="card-container">
                            <div class="card">អតិថិជនសរុប<h3 id="dBorrowers">0</h3></div>
                            <div class="card">កម្ចីសកម្ម<h3 id="dActive">0</h3></div>
                            <div class="card">កម្ចីខូច<h3 id="dBad">0</h3></div>
                            <div class="card">ប្រាក់ប្រមូលបានសរុប<h3 id="dCollected">$0</h3></div>
                        </div>
                    </div>

                    <!-- 2. BORROWERS -->
                    <div id="borrowers" class="section">
                        <h3>បញ្ជីឈ្មោះអតិថិជន</h3>
                        <br>
                        <table>
                            <thead>
                                <tr><th>លេខកូដ</th><th>ឈ្មោះ</th><th>ភេទ</th><th>ទូរស័ព្ទ</th><th>អត្តសញ្ញាណប័ណ្ណ</th><th>អាសយដ្ឋាន</th><th>សកម្មភាព</th></tr>
                            </thead>
                            <tbody id="borrowerTable"></tbody>
                        </table>
                    </div>

                    <!-- 3. LOANS -->
                    <div id="loans" class="section">
                        <h3>បញ្ជីកម្ចី (សកម្ម / ខូច)</h3>
                        <br>
                        <table>
                            <thead>
                                <tr><th>លេខកូដកម្ចី</th><th>ឈ្មោះអតិថិជន</th><th>ទឹកប្រាក់</th><th>អត្រាការប្រាក់</th><th>មន្ត្រី CO</th><th>ស្ថានភាព</th><th>សកម្មភាព</th></tr>
                            </thead>
                            <tbody id="loanTable"></tbody>
                        </table>
                    </div>

                    <!-- 4. COLLECTIONS -->
                    <div id="collections" class="section">
                        <h3>តារាងប្រមូលប្រាក់</h3>
                        <br>
                        <table>
                            <thead>
                                <tr><th>វិក្កយបត្រ</th><th>ឈ្មោះអតិថិជន</th><th>ទឹកប្រាក់បង់</th><th>មន្ត្រី CO</th><th>ស្ថានភាពបេឡា</th><th>សកម្មភាព</th></tr>
                            </thead>
                            <tbody id="collectionTable"></tbody>
                        </table>
                    </div>

                    <!-- 5. PAYMENTS -->
                    <div id="payments" class="section">
                        <h3>ការទូទាត់ប្រាក់នៅក្រុមហ៊ុន</h3>
                        <p>កន្លែងទទួលប្រាក់ផ្ទាល់ពីអតិថិជន...</p>
                    </div>

                    <!-- 6. REPORTS -->
                    <div id="rep-collection" class="section"><h3>របាយការណ៍ប្រមូលប្រាក់</h3><div id="repCollectionContent"></div></div>
                    <div id="rep-expense" class="section"><h3>របាយការណ៍ចំណាយ</h3></div>
                    <div id="rep-cashier" class="section"><h3>របាយការណ៍បេឡាទទួលប្រាក់</h3></div>
                    <div id="rep-balance" class="section"><h3>របាយការណ៍សមតុល្យសរុប</h3></div>

                    <!-- 7. SETTINGS -->
                    <div id="settings" class="section">
                        <h3>ការកំណត់ប្រព័ន្ធ</h3>
                        <br>
                        <button class="btn btn-blue" onclick="loadStaff()">គ្រប់គ្រងបុគ្គលិក / មន្ត្រីឥណទាន</button>
                        <div id="staffList" style="margin-top:15px;"></div>
                    </div>

                </div>
            </div>

            <script>
                function showSection(id, element) {
                    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
                    document.getElementById(id).classList.add('active');
                    document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove('active'));
                    if(element) element.classList.add('active');
                    document.getElementById('headerTitle').innerText = element ? element.innerText : 'Dashboard';
                }

                function toggleSubmenu() {
                    document.getElementById('reportSub').classList.toggle('show');
                }

                async function loadDashboard() {
                    const res = await fetch('/api/stats');
                    const data = await res.json();
                    document.getElementById('dBorrowers').innerText = data.borrowersCount;
                    document.getElementById('dActive').innerText = data.activeLoans;
                    document.getElementById('dBad').innerText = data.badLoans;
                    document.getElementById('dCollected').innerText = '$' + data.totalCollected;
                    
                    // Load Borrowers
                    const bRes = await fetch('/api/borrowers');
                    const borrowers = await bRes.json();
                    let bHtml = '';
                    borrowers.forEach(b => {
                        bHtml += \`<tr><td>\${b.code||''}</td><td>\${b.name||''}</td><td>\${b.gender||''}</td><td>\${b.phone||''}</td><td>\${b.nationalId||''}</td><td>\${b.address||''}</td><td><button class="btn btn-red" onclick="deleteBorrower('\${b._id}')">លុប</button></td></tr>\`;
                    });
                    document.getElementById('borrowerTable').innerHTML = bHtml || '<tr><td colspan="7">មិនមានទិន្នន័យ</td></tr>';

                    // Load Loans
                    const lRes = await fetch('/api/loans');
                    const loans = await lRes.json();
                    let lHtml = '';
                    loans.forEach(l => {
                        lHtml += \`<tr><td>\${l.loanCode}</td><td>\${l.borrowerId?.name || 'N/A'}</td><td>$\${l.amount}</td><td>\${l.interestRate}%</td><td>\${l.coOfficer}</td><td>\${l.status}</td><td>
                            <button class="btn btn-green" onclick="updateLoanStatus('\${l._id}', 'Active')">Approve</button>
                            <button class="btn btn-yellow" onclick="updateLoanStatus('\${l._id}', 'Bad Loan')">កម្ចីខូច</button>
                            <button class="btn btn-red" onclick="deleteLoan('\${l._id}')">លុប</button>
                        </td></tr>\`;
                    });
                    document.getElementById('loanTable').innerHTML = lHtml || '<tr><td colspan="7">មិនមានទិន្នន័យកម្ចី</td></tr>';

                    // Load Collections / Transactions
                    const tRes = await fetch('/api/transactions');
                    const txs = await tRes.json();
                    let tHtml = '';
                    txs.forEach(t => {
                        let statusText = t.receivedByCashier ? '<span style="color:green">Approved</span>' : '<span style="color:orange">Pending</span>';
                        tHtml += \`<tr><td>\${t.receiptNo}</td><td>\${t.loanId?.borrowerId?.name || 'N/A'}</td><td>$\${t.totalPaid}</td><td>\${t.coOfficer}</td><td>\${statusText}</td><td>
                            \${!t.receivedByCashier ? '<button class="btn btn-green" onclick="approveCashier(\\\`' + t._id + '\\\`)">ទទួលប្រាក់</button>' : ''}
                        </td></tr>\`;
                    });
                    document.getElementById('collectionTable').innerHTML = tHtml || '<tr><td colspan="6">មិនមានទិន្នន័យប្រមូលប្រាក់</td></tr>';
                }

                async function deleteBorrower(id) { if(confirm('លុបមែនទេ?')) { await fetch('/api/borrowers/'+id, {method:'DELETE'}); loadDashboard(); } }
                async function deleteLoan(id) { if(confirm('លុបកម្ចីនេះមែនទេ?')) { await fetch('/api/loans/'+id, {method:'DELETE'}); loadDashboard(); } }
                async function updateLoanStatus(id, status) { await fetch('/api/loans/'+id+'/status', {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({status})}); loadDashboard(); }
                async function approveCashier(id) { await fetch('/api/transactions/approve/'+id, {method:'PUT'}); loadDashboard(); }

                async function loadStaff() {
                    const res = await fetch('/api/staff');
                    const staff = await res.json();
                    let html = '<h4>បញ្ជីបុគ្គលិក</h4><table><tr><th>ឈ្មោះ</th><th>តួនាទី</th><th>ទូរស័ព្ទ</th></tr>';
                    staff.forEach(s => html += \`<tr><td>\${s.name}</td><td>\${s.role}</td><td>\${s.phone}</td></tr>\`);
                    html += '</table>';
                    document.getElementById('staffList').innerHTML = html;
                }

                loadDashboard();
            </script>
        </body>
        </html>
    `);
});

// ==========================================
// ៤. START SERVER
// ==========================================
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
