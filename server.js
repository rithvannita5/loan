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

// Borrower Schema (ពត៌មានអ្នកខ្ចី និងអ្នកធានា)
const borrowerSchema = new mongoose.Schema({
    code: String,
    name: String,
    gender: String,
    phone: String,
    dob: String,
    nationalId: String,
    address: String,
    guarantor: {
        name: String,
        gender: String,
        nationalId: String,
        dob: String,
        phone: String,
        address: String,
        relation: String
    }
});
const Borrower = mongoose.model('Borrower', borrowerSchema);

// Loan Schema (កម្ចីសកម្ម / កម្ចីខូច)
const loanSchema = new mongoose.Schema({
    loanCode: String,
    borrowerId: { type: mongoose.Schema.Types.ObjectId, ref: 'Borrower' },
    disburseDate: String,
    duration: Number,
    paymentFrequency: { type: String, enum: ['Daily', 'Weekly', 'Bi-Weekly', 'Monthly'], default: 'Monthly' },
    amount: Number,
    currency: { type: String, default: 'USD' },
    loanType: { type: String, default: 'ការថេរដើមថេរ' }, // ការថេរដើមថេរ, បង់រំលោះថេរ, រំលោះថយ, បង់តែការ
    interestRate: Number,
    totalInterest: Number,
    totalPayable: Number,
    paidAmount: { type: Number, default: 0 },
    remainingBalance: Number,
    coOfficer: String,
    status: { type: String, enum: ['Active', 'Bad Loan', 'Closed'], default: 'Active' },
    createdAt: { type: Date, default: Date.now }
});
const Loan = mongoose.model('Loan', loanSchema);

// Transaction (ប្រមូលប្រាក់ & ទូរទាត់)
const transactionSchema = new mongoose.Schema({
    receiptNo: String,
    loanId: { type: mongoose.Schema.Types.ObjectId, ref: 'Loan' },
    coOfficer: String,
    principalPaid: Number,
    interestPaid: Number,
    penaltyPaid: { type: Number, default: 0 },
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
app.post('/api/login', (req, res) => {
    const { username, password } = req.body;
    if(username === 'admin' && password === '123456') {
        res.json({ success: true, role: 'Admin' });
    } else {
        res.status(401).json({ success: false, message: 'ឈ្មោះអ្នកប្រើប្រាស់ ឬពាក្យសម្ងាត់មិនត្រូវ!' });
    }
});

// Stats API for Dashboard (គណនាកម្ចីខូច និងទឹកប្រាក់ខូច)
app.get('/api/stats', async (req, res) => {
    try {
        const borrowersCount = await Borrower.countDocuments();
        const activeLoansCount = await Loan.countDocuments({ status: 'Active' });
        
        // កម្ចីខូច និងទឹកប្រាក់ខូចសរុប
        const badLoans = await Loan.find({ status: 'Bad Loan' });
        const badLoansCount = badLoans.length;
        const badLoansTotalAmount = badLoans.reduce((sum, l) => sum + (l.remainingBalance || 0), 0);

        const totalCollected = await Transaction.aggregate([{ $group: { _id: null, total: { $sum: '$totalPaid' } } }]);

        res.json({
            borrowersCount,
            activeLoansCount,
            badLoansCount,
            badLoansTotalAmount,
            totalCollected: totalCollected[0]?.total || 0
        });
    } catch(err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/borrowers', async (req, res) => res.json(await Borrower.find()));
app.post('/api/borrowers', async (req, res) => res.status(201).json(await new Borrower(req.body).save()));
app.delete('/api/borrowers/:id', async (req, res) => res.json(await Borrower.findByIdAndDelete(req.params.id)));

app.get('/api/loans', async (req, res) => res.json(await Loan.find().populate('borrowerId')));
app.post('/api/loans', async (req, res) => {
    try {
        const data = req.body;
        data.totalInterest = (data.amount * (data.interestRate / 100));
        data.totalPayable = Number(data.amount) + Number(data.totalInterest);
        data.remainingBalance = data.totalPayable;
        const loan = new Loan(data);
        await loan.save();
        res.status(201).json(loan);
    } catch(err) { res.status(400).json({ error: err.message }); }
});

app.put('/api/loans/:id/status', async (req, res) => {
    res.json(await Loan.findByIdAndUpdate(req.params.id, { status: req.body.status }, { new: true }));
});
app.put('/api/loans/:id/co', async (req, res) => {
    res.json(await Loan.findByIdAndUpdate(req.params.id, { coOfficer: req.body.coOfficer }, { new: true }));
});
app.delete('/api/loans/:id', async (req, res) => res.json(await Loan.findByIdAndDelete(req.params.id)));

app.get('/api/transactions', async (req, res) => res.json(await Transaction.find().populate({ path: 'loanId', populate: { path: 'borrowerId' } })));
app.post('/api/transactions', async (req, res) => {
    try {
        const data = req.body;
        data.totalPaid = Number(data.principalPaid || 0) + Number(data.interestPaid || 0) + Number(data.penaltyPaid || 0);
        const tx = new Transaction(data);
        await tx.save();

        const loan = await Loan.findById(data.loanId);
        if(loan) {
            loan.paidAmount += data.totalPaid;
            loan.remainingBalance -= (Number(data.principalPaid || 0) + Number(data.interestPaid || 0));
            if(loan.remainingBalance <= 0) loan.status = 'Closed';
            await loan.save();
        }
        res.status(201).json(tx);
    } catch(err) { res.status(400).json({ error: err.message }); }
});


// ==========================================
// ៣. FRONTEND (9-MENU SIDEBAR & FULL UI)
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
                
                #loginOverlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #1e293b; display: flex; justify-content: center; align-items: center; z-index: 999; }
                .login-card { background: white; padding: 30px; border-radius: 8px; width: 350px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
                .login-card h2 { text-align: center; margin-bottom: 20px; color: #1e293b; }
                .login-card input { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #cbd5e1; border-radius: 4px; }
                .login-card button { width: 100%; padding: 10px; background: #0284c7; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }

                #appContainer { display: none; width: 100%; height: 100%; display: flex; }
                .sidebar { width: 260px; background: #1e293b; color: white; display: flex; flex-direction: column; height: 100%; overflow-y: auto; }
                .sidebar h2 { padding: 20px; font-size: 16px; text-align: center; background: #0f172a; border-bottom: 1px solid #334155; }
                .sidebar a { padding: 12px 20px; color: #cbd5e1; text-decoration: none; display: block; cursor: pointer; font-size: 13px; border-left: 4px solid transparent; }
                .sidebar a:hover, .sidebar a.active { background: #334155; color: white; border-left-color: #38bdf8; }
                .submenu { padding-left: 15px; background: #0f172a; display: none; }
                .submenu.show { display: block; }
                
                .main-content { flex: 1; display: flex; flex-direction: column; overflow-y: auto; height: 100%; }
                header { background: white; padding: 15px 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 18px; font-weight: bold; color: #334155; display: flex; justify-content: space-between; align-items: center; }
                .content-body { padding: 25px; flex: 1; }
                .section { display: none; }
                .section.active { display: block; }
                
                .card-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px; }
                .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }
                .card h3 { font-size: 20px; color: #0284c7; margin-top: 5px; }

                table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-top: 10px; }
                th, td { padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: center; font-size: 12px; }
                th { background: #f8fafc; color: #475569; }
                
                .btn { padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 11px; color: white; margin: 2px; }
                .btn-green { background: #10b981; } .btn-blue { background: #0284c7; } .btn-red { background: #ef4444; } .btn-yellow { background: #f59e0b; }
            </style>
        </head>
        <body>

            <div id="loginOverlay">
                <div class="login-card">
                    <h2>ចូលប្រព័ន្ធ MFI</h2>
                    <div id="errorMsg" style="color:red; font-size:12px; margin-bottom:10px; text-align:center;"></div>
                    <input type="text" id="username" placeholder="ឈ្មោះអ្នកប្រើប្រាស់ (admin)">
                    <input type="password" id="password" placeholder="ពាក្យសម្ងាត់ (123456)">
                    <button onclick="handleLogin()">ចូលប្រព័ន្ធ</button>
                </div>
            </div>

            <div id="appContainer" style="display:none;">
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
                    <header><span id="headerTitle">Dashboard</span></header>
                    <div class="content-body">
                        
                        <!-- 1. DASHBOARD -->
                        <div id="dashboard" class="section active">
                            <div class="card-container">
                                <div class="card">អតិថិជនសរុប<h3 id="dBorrowers">0</h3></div>
                                <div class="card">កម្ចីសកម្ម<h3 id="dActive">0</h3></div>
                                <div class="card">កម្ចីខូចសរុប (ចំនួន)<h3 id="dBadCount">0</h3></div>
                                <div class="card">ទឹកប្រាក់កម្ចីខូចសរុប<h3 id="dBadAmount">$0</h3></div>
                            </div>
                        </div>

                        <!-- 2. អតិថិជន -->
                        <div id="borrowers" class="section">
                            <h3>ពត៌មានអ្នកខ្ចី និងអ្នករួមរស់/អ្នកធានា</h3>
                            <table>
                               <thead>
                                   <tr>
                                       <th>#</th><th>លេខកូដ</th><th>ឈ្មោះ</th><th>ភេទ</th><th>ទូរស័ព្ទ</th><th>ថ្ងៃខែកំណើត</th><th>អត្តសញ្ញាណ</th><th>អាសយដ្ឋាន</th>
                                       <th>អ្នកធានា</th><th>ភេទ</th><th>អត្តសញ្ញាណ</th><th>ទូរស័ព្ទ</th><th>ទំនាក់ទំនង</th>
                                   </tr>
                               </thead>
                               <tbody id="borrowerTable"></tbody>
                            </table>
                        </div>

                        <!-- 3. កម្ចី (សកម្ម និង កម្ចីខូច) -->
                        <div id="loans" class="section">
                            <h3>ក. កម្ចីសកម្ម</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>លេខកូដ</th><th>ឈ្មោះអតិថិជន</th><th>ទឹកប្រាក់</th><th>ប្រភេទកម្ចី</th><th>រយៈពេល</th><th>អត្រាការប្រាក់</th><th>ជំពាក់សរុប</th><th>បំណុលខ្វះ</th><th>មន្ត្រី CO</th><th>សកម្មភាព</th>
                                    </tr>
                                </thead>
                                <tbody id="activeLoanTable"></tbody>
                            </table>
                            
                            <br>
                            <h3 style="color: #ef4444;">ខ. កម្ចីខូច (ដកចេញពីកម្ចីសកម្ម)</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>លេខកូដ</th><th>ឈ្មោះអតិថិជន</th><th>ទឹកប្រាក់ដើម</th><th>បំណុលខ្វះសរុប</th><th>មន្ត្រី CO</th><th>ស្ថានភាព</th><th>សកម្មភាព</th>
                                    </tr>
                                </thead>
                                <tbody id="badLoanTable"></tbody>
                            </table>
                        </div>

                        <!-- 4. ប្រមូលប្រាក់ -->
                        <div id="collections" class="section">
                            <h3>តារាងប្រមូលប្រាក់ប្រចាំថ្ងៃ</h3>
                            <table>
                                <thead>
                                    <tr><th>លេខកូដកម្ចី</th><th>ឈ្មោះអតិថិជន</th><th>អាសយដ្ឋាន</th><th>ទូរស័ព្ទ</th><th>បំណុលខ្វះ</th><th>ទឹកប្រាក់ត្រូវបង់ (ប៊ូតុងបៃតង)</th></tr>
                                </thead>
                                <tbody id="collectionTable"></tbody>
                            </table>
                        </div>

                        <!-- 5. ទូរទាត់ -->
                        <div id="payments" class="section">
                            <h3>ការទូរទាត់ប្រាក់នៅក្រុមហ៊ុន</h3>
                            <p>កន្លែងទទួលប្រាក់អតិថិជនដែលមកបង់ផ្ទាល់នៅការិយាល័យ...</p>
                        </div>

                        <!-- 6. របាយការណ៍ -->
                        <div id="rep-collection" class="section"><h3>របាយការណ៍ប្រមូលប្រាក់</h3></div>
                        <div id="rep-expense" class="section"><h3>របាយការណ៍ចំណាយ</h3></div>
                        <div id="rep-cashier" class="section"><h3>របាយការណ៍បេឡាទទួលប្រាក់</h3></div>
                        <div id="rep-balance" class="section"><h3>របាយការណ៍សមតុល្យសរុប</h3></div>

                        <!-- 7. ការកំណត់ -->
                        <div id="settings" class="section"><h3>ការកំណត់ប្រព័ន្ធ</h3></div>

                    </div>
                </div>
            </div>

            <script>
                async function handleLogin() {
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    const res = await fetch('/api/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    const data = await res.json();
                    if(data.success) {
                        document.getElementById('loginOverlay').style.display = 'none';
                        document.getElementById('appContainer').style.display = 'flex';
                        loadAllData();
                    } else {
                        document.getElementById('errorMsg').innerText = data.message;
                    }
                }

                function handleLogout() { location.reload(); }

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

                async function loadAllData() {
                    // Load Stats Dashboard
                    const sRes = await fetch('/api/stats');
                    const stats = await sRes.json();
                    document.getElementById('dBorrowers').innerText = stats.borrowersCount;
                    document.getElementById('dActive').innerText = stats.activeLoansCount;
                    document.getElementById('dBadCount').innerText = stats.badLoansCount;
                    document.getElementById('dBadAmount').innerText = '$' + stats.badLoansTotalAmount.toFixed(2);

                    // Load Borrowers
                    const bRes = await fetch('/api/borrowers');
                    const borrowers = await bRes.json();
                    let bHtml = '';
                    borrowers.forEach((b, i) => {
                        bHtml += \`<tr>
                            <td>\${i+1}</td><td>\${b.code||''}</td><td>\${b.name||''}</td><td>\${b.gender||''}</td><td>\${b.phone||''}</td><td>\${b.dob||''}</td><td>\${b.nationalId||''}</td><td>\${b.address||''}</td>
                            <td>\${b.guarantor?.name||''}</td><td>\${b.guarantor?.gender||''}</td><td>\${b.guarantor?.nationalId||''}</td><td>\${b.guarantor?.phone||''}</td><td>\${b.guarantor?.relation||''}</td>
                        </tr>\`;
                    });
                    document.getElementById('borrowerTable').innerHTML = bHtml || '<tr><td colspan="13">មិនមានទិន្នន័យអតិថិជន</td></tr>';

                    // Load Loans (Active & Bad Loans separated)
                    const lRes = await fetch('/api/loans');
                    const loans = await lRes.json();
                    let activeHtml = '', badHtml = '', cHtml = '';
                    
                    loans.forEach(l => {
                        if (l.status === 'Active') {
                            activeHtml += \`<tr>
                                <td>\${l.loanCode}</td><td>\${l.borrowerId?.name || ''}</td><td>$\${l.amount}</td><td>\${l.loanType}</td><td>\${l.paymentFrequency}</td><td>\${l.interestRate}%</td><td>$\${l.totalPayable}</td><td>$\${l.remainingBalance}</td><td>\${l.coOfficer}</td>
                                <td>
                                    <button class="btn btn-yellow" onclick="changeStatus('\${l._id}', 'Bad Loan')">ប្ដូរទៅកម្ចីខូច</button>
                                    <button class="btn btn-blue" onclick="changeCO('\${l._id}')">ដូរ CO</button>
                                </td>
                            </tr>\`;

                            cHtml += \`<tr>
                                <td>\${l.loanCode}</td><td>\${l.borrowerId?.name || ''}</td><td>\${l.borrowerId?.address || ''}</td><td>\${l.borrowerId?.phone || ''}</td><td>$\${l.remainingBalance}</td>
                                <td><button class="btn btn-green" onclick="makePayment('\${l._id}', \$.trim(\${l.remainingBalance}))">បង់ប្រាក់: $\${l.remainingBalance}</button></td>
                            </tr>\`;
                        } else if (l.status === 'Bad Loan') {
                            badHtml += \`<tr>
                                <td>\${l.loanCode}</td><td>\${l.borrowerId?.name || ''}</td><td>$\${l.amount}</td><td style="color:red; font-weight:bold;">$\${l.remainingBalance}</td><td>\${l.coOfficer}</td><td>\${l.status}</td>
                                <td><button class="btn btn-red" onclick="deleteLoan('\${l._id}')">លុប</button></td>
                            </tr>\`;
                        }
                    });

                    document.getElementById('activeLoanTable').innerHTML = activeHtml || '<tr><td colspan="10">មិនមានកម្ចីសកម្ម</td></tr>';
                    document.getElementById('badLoanTable').innerHTML = badHtml || '<tr><td colspan="7">មិនមានកម្ចីខូចទេ</td></tr>';
                    document.getElementById('collectionTable').innerHTML = cHtml || '<tr><td colspan="6">មិនមានទិន្នន័យប្រមូលប្រាក់</td></tr>';
                }

                async function changeStatus(id, status) {
                    if(confirm('តើអ្នកពិតជាចង់ផ្ទេរកម្ចីនេះទៅជា កម្ចីខូច និងដកចេញពីបញ្ជីកម្ចីសកម្មមែនទេ?')) {
                        await fetch('/api/loans/'+id+'/status', { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({status}) });
                        loadAllData();
                    }
                }

                async function changeCO(id) {
                    let newCO = prompt('បញ្ចូលឈ្មោះមន្ត្រីឥណទាន (CO) ថ្មី៖');
                    if(newCO) {
                        await fetch('/api/loans/'+id+'/co', { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({coOfficer: newCO}) });
                        loadAllData();
                    }
                }

                async function deleteLoan(id) {
                    if(confirm('លុបទិន្នន័យកម្ចីខូចនេះចេញពីប្រព័ន្ធមែនទេ?')) {
                        await fetch('/api/loans/'+id, { method: 'DELETE' });
                        loadAllData();
                    }
                }

                async function makePayment(loanId, maxDue) {
                    let amount = prompt('បញ្ចូលទឹកប្រាក់ដែលអតិថិជនបានបង់:', maxDue);
                    if(amount) {
                        await fetch('/api/transactions', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ receiptNo: 'REC-'+Math.floor(Math.random()*10000), loanId, principalPaid: Number(amount), interestPaid: 0, coOfficer: 'Admin' })
                        });
                        alert('បង់ប្រាក់បានជោគជ័យ!');
                        loadAllData();
                    }
                }
            </script>
        </body>
        </html>
    `);
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
