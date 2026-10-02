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

// Borrower Schema (អតិថិជន និងអ្នកធានា)
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

// Loan Schema (កម្ចីសកម្ម / កម្ចីខូច / ប្រភេទកម្ចី / រយៈពេល)
const loanSchema = new mongoose.Schema({
    loanCode: String,
    borrowerId: { type: mongoose.Schema.Types.ObjectId, ref: 'Borrower' },
    disburseDate: String,
    firstPaymentDate: String,
    duration: Number,
    paymentFrequency: { type: String, enum: ['Daily', 'Weekly', 'Bi-Weekly', 'Monthly'], default: 'Monthly' },
    amount: Number,
    currency: { type: String, default: 'USD' },
    loanType: { type: String, default: 'Flat Rate' }, // ការថេរដើមថេរ, រំលោះថយ, បង់តែការ...
    interestRate: Number,
    totalInterest: Number,
    totalPayable: Number,
    paidAmount: { type: Number, default: 0 },
    remainingBalance: Number,
    coOfficer: String,
    status: { type: String, enum: ['Active', 'Bad Loan', 'Closed', 'Pending'], default: 'Active' },
    createdAt: { type: Date, default: Date.now }
});
const Loan = mongoose.model('Loan', loanSchema);

// Transaction (ការប្រមូលប្រាក់ & ទូរទាត់)
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

app.get('/api/transactions', async (req, res) => res.json(await Transaction.find().populate({ path: 'loanId', populate: { path: 'borrowerId' } })));
app.post('/api/transactions', async (req, res) => {
    try {
        const data = req.body;
        data.totalPaid = Number(data.principalPaid || 0) + Number(data.interestPaid || 0) + Number(data.penaltyPaid || 0);
        const tx = new Transaction(data);
        await tx.save();

        // Update Loan Remaining Balance
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
// ៣. FRONTEND INTERFACE (UI)
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
                .sidebar { width: 260px; background: #1e293b; color: white; display: flex; flex-direction: column; height: 100%; }
                .sidebar h2 { padding: 20px; font-size: 16px; text-align: center; background: #0f172a; border-bottom: 1px solid #334155; }
                .sidebar a { padding: 12px 20px; color: #cbd5e1; text-decoration: none; display: block; cursor: pointer; font-size: 14px; border-left: 4px solid transparent; }
                .sidebar a:hover, .sidebar a.active { background: #334155; color: white; border-left-color: #38bdf8; }
                
                .main-content { flex: 1; display: flex; flex-direction: column; overflow-y: auto; height: 100%; }
                header { background: white; padding: 15px 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 18px; font-weight: bold; color: #334155; display: flex; justify-content: space-between; align-items: center; }
                .content-body { padding: 25px; flex: 1; }
                .section { display: none; }
                .section.active { display: block; }
                
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
                    <a onclick="showSection('borrowers', this)" class="active">1. អតិថិជន និងអ្នកធានា</a>
                    <a onclick="showSection('loans', this)">2. បញ្ជីកម្ចី (សកម្ម និងខូច)</a>
                    <a onclick="showSection('collections', this)">3. តារាងប្រមូលប្រាក់</a>
                    <a onclick="showSection('payments', this)">4. ការទូរទាត់</a>
                    <a onclick="handleLogout()" style="color: #ef4444; margin-top: auto;">ចាកចេញ</a>
                </div>

                <div class="main-content">
                    <header><span id="headerTitle">អតិថិជន និងអ្នកធានា</span></header>
                    <div class="content-body">
                        
                        <!-- 1. អតិថិជន -->
                        <div id="borrowers" class="section active">
                            <h3>បញ្ជីឈ្មោះអតិថិជន និងអ្នករួមរស់/អ្នកធានា</h3>
                            <table>
                               <thead>
                                   <tr>
                                       <th>#</th><th>លេខកូដ</th><th>ឈ្មោះ</th><th>ភេទ</th><th>ទូរស័ព្ទ</th><th>ថ្ងៃខែកំណើត</th><th>អត្តសញ្ញាណ</th><th>អាសយដ្ឋាន</th>
                                       <th>អ្នកធានា</th><th>ភេទ</th><th>អត្តសញ្ញាណ</th><th>ទូរស័ព្ទអ្នកធានា</th><th>ទំនាក់ទំនង</th>
                                   </tr>
                               </thead>
                               <tbody id="borrowerTable"></tbody>
                            </table>
                        </div>

                        <!-- 2. កម្ចី -->
                        <div id="loans" class="section">
                            <h3>បញ្ជីកម្ចី (សកម្ម / កម្ចីខូច)</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>លេខកូដ</th><th>ឈ្មោះ</th><th>ទឹកប្រាក់</th><th>ប្រភេទកម្ចី</th><th>រយៈពេល</th><th>អត្រាការប្រាក់</th><th>ជំពាក់សរុប</th><th>បំណុលខ្វះ</th><th>មន្ត្រី CO</th><th>ស្ថានភាព</th><th>សកម្មភាព</th>
                                    </tr>
                                </thead>
                                <tbody id="loanTable"></tbody>
                            </table>
                        </div>

                        <!-- 3. ប្រមូលប្រាក់ -->
                        <div id="collections" class="section">
                            <h3>តារាងប្រមូលប្រាក់ប្រចាំថ្ងៃ</h3>
                            <table>
                                <thead>
                                    <tr><th>លេខកូដកម្ចី</th><th>ឈ្មោះអតិថិជន</th><th>អាសយដ្ឋាន</th><th>ទូរស័ព្ទ</th><th>បំណុលនៅខ្វះ</th><th>ប្រាក់ត្រូវបង់ (ចុចបង់)</th></tr>
                                </thead>
                                <tbody id="collectionTable"></tbody>
                            </table>
                        </div>

                        <!-- 4. ការទូរទាត់ -->
                        <div id="payments" class="section">
                            <h3>ការទូរទាត់ប្រាក់នៅក្រុមហ៊ុន</h3>
                            <p>គ្រប់គ្រងការបង់ប្រាក់ផ្ទាល់របស់អតិថិជន...</p>
                        </div>

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
                        loadData();
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
                    document.getElementById('headerTitle').innerText = element ? element.innerText : '';
                }

                async function loadData() {
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

                    // Load Loans
                    const lRes = await fetch('/api/loans');
                    const loans = await lRes.json();
                    let lHtml = '', cHtml = '';
                    loans.forEach(l => {
                        lHtml += \`<tr>
                            <td>\${l.loanCode}</td><td>\${l.borrowerId?.name || ''}</td><td>$\${l.amount}</td><td>\${l.loanType}</td><td>\${l.paymentFrequency}</td><td>\${l.interestRate}%</td><td>$\${l.totalPayable}</td><td>$\${l.remainingBalance}</td><td>\${l.coOfficer}</td><td>\${l.status}</td>
                            <td>
                                <button class="btn btn-yellow" onclick="changeStatus('\${l._id}', 'Bad Loan')">កម្ចីខូច</button>
                                <button class="btn btn-red" onclick="changeCO('\${l._id}')">ដូរ CO</button>
                            </td>
                        </tr>\`;

                        cHtml += \`<tr>
                            <td>\${l.loanCode}</td><td>\${l.borrowerId?.name || ''}</td><td>\${l.borrowerId?.address || ''}</td><td>\${l.borrowerId?.phone || ''}</td><td>$\${l.remainingBalance}</td>
                            <td><button class="btn btn-green" onclick="makePayment('\${l._id}', \${l.remainingBalance})">បង់ប្រាក់: $\${l.remainingBalance}</button></td>
                        </tr>\`;
                    });
                    document.getElementById('loanTable').innerHTML = lHtml || '<tr><td colspan="11">មិនមានទិន្នន័យកម្ចី</td></tr>';
                    document.getElementById('collectionTable').innerHTML = cHtml || '<tr><td colspan="6">មិនមានទិន្នន័យប្រមូលប្រាក់</td></tr>';
                }

                async function changeStatus(id, status) {
                    if(confirm('ប្ដូរស្ថានភាពទៅជាកម្ចីខូច?')) {
                        await fetch('/api/loans/'+id+'/status', { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({status}) });
                        loadData();
                    }
                }

                async function changeCO(id) {
                    let newCO = prompt('បញ្ចូលឈ្មោះមន្ត្រីឥណទាន (CO) ថ្មី៖');
                    if(newCO) {
                        await fetch('/api/loans/'+id+'/co', { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({coOfficer: newCO}) });
                        loadData();
                    }
                }

                async function makePayment(loanId, maxDue) {
                    let amount = prompt('បញ្ចូលទឹកប្រាក់ដែលត្រូវបង់:', maxDue);
                    if(amount) {
                        await fetch('/api/transactions', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ receiptNo: 'REC-'+Math.floor(Math.random()*10000), loanId, principalPaid: Number(amount), interestPaid: 0, coOfficer: 'Admin' })
                        });
                        alert('បង់ប្រាក់បានជោគជ័យ!');
                        loadData();
                    }
                }
            </script>
        </body>
        </html>
    `);
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
