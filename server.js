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
    paymentFrequency: String,
    coOfficer: String,
    status: { type: String, default: 'Pending' },
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
    receivedByCashier: { type: Boolean, default: false },
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
// API Login
app.post('/api/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        // ពិនិត្យគណនី Admin លំនាំដើម ឬទាញពី Database
        if(username === 'admin' && password === '123456') {
            return res.json({ success: true, message: 'Login successful', role: 'Admin' });
        }
        const user = await User.findOne({ username, password, active: true });
        if(user) {
            res.json({ success: true, message: 'Login successful', role: user.role });
        } else {
            res.status(401).json({ success: false, message: 'ឈ្មោះអ្នកប្រើប្រាស់ ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ!' });
        }
    } catch(err) {
        res.status(500).json({ error: err.message });
    }
});

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
app.get('/api/loans', async (req, res) => res.json(await Loan.find().populate('borrowerId')));
app.get('/api/transactions', async (req, res) => res.json(await Transaction.find().populate({ path: 'loanId', populate: { path: 'borrowerId' } })));
app.get('/api/staff', async (req, res) => res.json(await Staff.find()));


// ==========================================
// ៣. FRONTEND (LOGIN + SIDEBAR UI)
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
                
                /* Login Page Overlay */
                #loginOverlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #1e293b; display: flex; justify-content: center; align-items: center; z-index: 999; }
                .login-card { background: white; padding: 30px; border-radius: 8px; width: 350px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
                .login-card h2 { text-align: center; margin-bottom: 20px; color: #1e293b; }
                .login-card input { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #cbd5e1; border-radius: 4px; }
                .login-card button { width: 100%; padding: 10px; background: #0284c7; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
                .login-card button:hover { background: #0369a1; }
                .error-msg { color: red; font-size: 12px; text-align: center; margin-bottom: 10px; }

                /* Main App Layout (Hidden until login) */
                #appContainer { display: none; width: 100%; height: 100%; }
                .sidebar { width: 260px; background: #1e293b; color: white; display: flex; flex-direction: column; height: 100%; }
                .sidebar h2 { padding: 20px; font-size: 16px; text-align: center; background: #0f172a; border-bottom: 1px solid #334155; }
                .sidebar a { padding: 12px 20px; color: #cbd5e1; text-decoration: none; display: block; cursor: pointer; font-size: 14px; border-left: 4px solid transparent; }
                .sidebar a:hover, .sidebar a.active { background: #334155; color: white; border-left-color: #38bdf8; }
                .submenu { padding-left: 20px; background: #0f172a; display: none; }
                .submenu.show { display: block; }
                
                .main-content { flex: 1; display: flex; flex-direction: column; overflow-y: auto; height: 100%; }
                header { background: white; padding: 15px 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 18px; font-weight: bold; color: #334155; display: flex; justify-content: space-between; align-items: center; }
                .content-body { padding: 25px; flex: 1; }
                .section { display: none; }
                .section.active { display: block; }
                
                .card-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 25px; }
                .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }
                .card h3 { font-size: 24px; color: #0284c7; margin-top: 5px; }
                table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
                th, td { padding: 12px 15px; border-bottom: 1px solid #e2e8f0; text-align: center; font-size: 13px; }
                th { background: #f8fafc; color: #475569; }
                .btn { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; color: white; margin: 2px; }
                .btn-green { background: #10b981; } .btn-blue { background: #0284c7; } .btn-red { background: #ef4444; } .btn-yellow { background: #f59e0b; }
            </style>
        </head>
        <body>

            <!-- ផ្ទាំង Login -->
            <div id="loginOverlay">
                <div class="login-card">
                    <h2>ចូលគណនី (Login)</h2>
                    <div id="errorMsg" class="error-msg"></div>
                    <input type="text" id="username" placeholder="ឈ្មោះអ្នកប្រើប្រាស់ (Username)">
                    <input type="password" id="password" placeholder="ពាក្យសម្ងាត់ (Password)">
                    <button onclick="handleLogin()">ចូលប្រព័ន្ធ</button>
                    <p style="text-align: center; font-size: 11px; color: #64748b; margin-top: 15px;">គណនីដើម: admin / 123456</p>
                </div>
            </div>

            <!-- ប្រព័ន្ធគោល (បង្ហាញក្រោយពេល Login ជាប់) -->
            <div id="appContainer" style="display: none;">
                <div style="display: flex; width: 100%; height: 100%;">
                    <div class="sidebar">
                        <h2>ប្រព័ន្ធគ្រប់គ្រងកម្ចី</h2>
                        <a onclick="showSection('dashboard', this)" class="active">1. Dashboard</a>
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
                        <a onclick="alert('មុខងារប្ដូរពាក្យសម្ងាត់')">8. ប្ដូរពាក្យសម្ងាត់</a>
                        <a onclick="handleLogout()" style="color: #ef4444;">9. ចាកចេញ</a>
                    </div>

                    <div class="main-content">
                        <header>
                            <span id="headerTitle">Dashboard</span>
                            <span id="userRoleBadge" style="font-size: 12px; background: #e2e8f0; padding: 4px 10px; border-radius: 4px;">Admin</span>
                        </header>
                        <div class="content-body">
                            
                            <div id="dashboard" class="section active">
                                <div class="card-container">
                                    <div class="card">អតិថិជនសរុប<h3 id="dBorrowers">0</h3></div>
                                    <div class="card">កម្ចីសកម្ម<h3 id="dActive">0</h3></div>
                                    <div class="card">កម្ចីខូច<h3 id="dBad">0</h3></div>
                                    <div class="card">ប្រាក់ប្រមូលបានសរុប<h3 id="dCollected">$0</h3></div>
                                </div>
                            </div>

                            <div id="borrowers" class="section">
                                <h3>បញ្ជីឈ្មោះអតិថិជន</h3><br>
                                <table>
                                    <thead><tr><th>លេខកូដ</th><th>ឈ្មោះ</th><th>ភេទ</th><th>ទូរស័ព្ទ</th><th>អត្តសញ្ញាណប័ណ្ណ</th><th>អាសយដ្ឋាន</th></tr></thead>
                                    <tbody id="borrowerTable"></tbody>
                                </table>
                            </div>

                            <div id="loans" class="section">
                                <h3>បញ្ជីកម្ចីសកម្ម និងកម្ចីខូច</h3><br>
                                <table>
                                    <thead><tr><th>លេខកូដកម្ចី</th><th>ឈ្មោះអតិថិជន</th><th>ទឹកប្រាក់</th><th>អត្រាការប្រាក់</th><th>មន្ត្រី CO</th><th>ស្ថានភាព</th></tr></thead>
                                    <tbody id="loanTable"></tbody>
                                </table>
                            </div>

                            <div id="collections" class="section"><h3>តារាងប្រមូលប្រាក់</h3></div>
                            <div id="payments" class="section"><h3>ការទូរទាត់ប្រាក់នៅក្រុមហ៊ុន</h3></div>
                            <div id="rep-collection" class="section"><h3>របាយការណ៍ប្រមូលប្រាក់</h3></div>
                            <div id="rep-expense" class="section"><h3>របាយការណ៍ចំណាយ</h3></div>
                            <div id="rep-cashier" class="section"><h3>របាយការណ៍បេឡាទទួលប្រាក់</h3></div>
                            <div id="rep-balance" class="section"><h3>របាយការណ៍សមតុល្យសរុប</h3></div>
                            <div id="settings" class="section"><h3>ការកំណត់ប្រព័ន្ធ</h3></div>

                        </div>
                    </div>
                </div>
            </div>

            <script>
                async function handleLogin() {
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    const errorMsg = document.getElementById('errorMsg');

                    const res = await fetch('/api/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    const data = await res.json();

                    if(data.success) {
                        document.getElementById('loginOverlay').style.display = 'none';
                        document.getElementById('appContainer').style.display = 'block';
                        document.getElementById('userRoleBadge').innerText = 'Role: ' + data.role;
                        loadDashboardData();
                    } else {
                        errorMsg.innerText = data.message;
                    }
                }

                function handleLogout() {
                    document.getElementById('appContainer').style.display = 'none';
                    document.getElementById('loginOverlay').style.display = 'flex';
                    document.getElementById('username').value = '';
                    document.getElementById('password').value = '';
                }

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

                async function loadDashboardData() {
                    const res = await fetch('/api/stats');
                    const data = await res.json();
                    document.getElementById('dBorrowers').innerText = data.borrowersCount;
                    document.getElementById('dActive').innerText = data.activeLoans;
                    document.getElementById('dBad').innerText = data.badLoans;
                    document.getElementById('dCollected').innerText = '$' + data.totalCollected;

                    const bRes = await fetch('/api/borrowers');
                    const borrowers = await bRes.json();
                    let bHtml = '';
                    borrowers.forEach(b => {
                        bHtml += \`<tr><td>\${b.code||''}</td><td>\${b.name||''}</td><td>\${b.gender||''}</td><td>\${b.phone||''}</td><td>\${b.nationalId||''}</td><td>\${b.address||''}</td></tr>\`;
                    });
                    document.getElementById('borrowerTable').innerHTML = bHtml || '<tr><td colspan="6">មិនមានទិន្នន័យ</td></tr>';

                    const lRes = await fetch('/api/loans');
                    const loans = await lRes.json();
                    let lHtml = '';
                    loans.forEach(l => {
                        lHtml += \`<tr><td>\${l.loanCode}</td><td>\${l.borrowerId?.name || 'N/A'}</td><td>$\${l.amount}</td><td>\${l.interestRate}%</td><td>\${l.coOfficer}</td><td>\${l.status}</td></tr>\`;
                    });
                    document.getElementById('loanTable').innerHTML = lHtml || '<tr><td colspan="6">មិនមានទិន្នន័យកម្ចី</td></tr>';
                }
            </script>
        </body>
        </html>
    `);
});

// ==========================================
// ៤. START SERVER
// ==========================================
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
