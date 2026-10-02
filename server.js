const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(cors());

// ==========================================
// ១. MONGODB CONNECTION
// ==========================================
mongoose.connect(process.env.MONGO_URI)
.then(() => console.log('MongoDB Connected Successfully!'))
.catch((err) => console.log('DB Connection Error:', err));

// ==========================================
// ២. SCHEMAS & MODELS
// ==========================================
// ឯកសារអ្នកខ្ចី និងអ្នកធានា
const borrowerSchema = new mongoose.Schema({
    code: { type: String, required: true, unique: true },
    name: { type: String, required: true },
    gender: String,
    phone: String,
    dob: Date,
    nationalId: String,
    address: String,
    guarantor: {
        name: String,
        gender: String,
        nationalId: String,
        dob: Date,
        phone: String,
        address: String,
        relation: String
    },
    createdAt: { type: Date, default: Date.now }
});
const Borrower = mongoose.model('Borrower', borrowerSchema);

// ឯកសារកម្ចី និងកាលវិភាគបង់ប្រាក់
const loanSchema = new mongoose.Schema({
    loanCode: { type: String, required: true, unique: true },
    borrowerId: { type: mongoose.Schema.Types.ObjectId, ref: 'Borrower', required: true },
    disburseDate: { type: Date, default: Date.now },
    duration: Number, // រយៈពេល (ចំនួនงวด)
    paymentFrequency: { type: String, enum: ['Daily', 'Weekly', 'Bi-Weekly', 'Monthly'], default: 'Monthly' },
    amount: { type: Number, required: true },
    currency: { type: String, default: 'USD' },
    loanType: { type: String, default: 'Flat Rate' }, // ការថេរដើមថេរ, រំលោះថយ...
    interestRate: Number,
    totalInterest: Number,
    totalPayable: Number,
    paidAmount: { type: Number, default: 0 },
    remainingBalance: Number,
    coOfficer: String,
    status: { type: String, enum: ['Active', 'Bad Loan', 'Closed'], default: 'Active' },
    schedule: [{
        installmentNumber: Number,
        dueDate: Date,
        principalDue: Number,
        interestDue: Number,
        totalDue: Number,
        status: { type: String, default: 'Unpaid' } // Unpaid, Paid
    }],
    createdAt: { type: Date, default: Date.now }
});
const Loan = mongoose.model('Loan', loanSchema);

// ឯកសារទូទាត់ប្រាក់ (Transactions)
const transactionSchema = new mongoose.Schema({
    receiptNo: { type: String, required: true },
    loanId: { type: mongoose.Schema.Types.ObjectId, ref: 'Loan', required: true },
    coOfficer: String,
    principalPaid: Number,
    interestPaid: Number,
    penaltyPaid: { type: Number, default: 0 },
    totalPaid: Number,
    paymentDate: { type: Date, default: Date.now },
    receivedByCashier: { type: Boolean, default: false }, // បេឡាករ Clear ទឹកប្រាក់
    clearedAt: Date
});
const Transaction = mongoose.model('Transaction', transactionSchema);

// ឯកសារចំណាយប្រចាំថ្ងៃ
const expenseSchema = new mongoose.Schema({
    title: String,
    amount: Number,
    category: String,
    date: { type: Date, default: Date.now },
    recordedBy: String
});
const Expense = mongoose.model('Expense', expenseSchema);


// ==========================================
// ៣. API ROUTES
// ==========================================

// ក. គ្រប់គ្រងអ្នកខ្ចី
app.post('/api/borrowers', async (req, res) => {
    try {
        const borrower = new Borrower(req.body);
        await borrower.save();
        res.status(201).json(borrower);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

app.get('/api/borrowers', async (req, res) => {
    try {
        const list = await Borrower.find();
        res.json(list);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ខ. គ្រប់គ្រងកម្ចី និងបង្កើតតារាងបង់ប្រាក់ស្វ័យប្រវត្តិ
app.post('/api/loans', async (req, res) => {
    try {
        const { loanCode, borrowerId, amount, interestRate, duration, paymentFrequency, disburseDate, coOfficer, loanType } = req.body;
        
        let totalInterest = (amount * (interestRate / 100) * (duration / 12));
        let totalPayable = amount + totalInterest;
        let remainingBalance = totalPayable;

        let schedule = [];
        let installmentAmount = totalPayable / duration;
        let principalPerInstallment = amount / duration;
        let interestPerInstallment = totalInterest / duration;
        let baseDate = new Date(disburseDate || Date.now());

        for (let i = 1; i <= duration; i++) {
            if (paymentFrequency === 'Daily') baseDate.setDate(baseDate.getDate() + 1);
            else if (paymentFrequency === 'Weekly') baseDate.setDate(baseDate.getDate() + 7);
            else if (paymentFrequency === 'Bi-Weekly') baseDate.setDate(baseDate.getDate() + 14);
            else if (paymentFrequency === 'Monthly') baseDate.setMonth(baseDate.getMonth() + 1);

            schedule.push({
                installmentNumber: i,
                dueDate: new Date(baseDate),
                principalDue: principalPerInstallment,
                interestDue: interestPerInstallment,
                totalDue: installmentAmount,
                status: 'Unpaid'
            });
        }

        const loan = new Loan({
            loanCode, borrowerId, amount, interestRate, duration, paymentFrequency,
            disburseDate, totalInterest, totalPayable, remainingBalance, coOfficer, loanType, schedule
        });
        await loan.save();
        res.status(201).json(loan);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

app.get('/api/loans', async (req, res) => {
    try {
        const loans = await Loan.find().populate('borrowerId');
        res.json(loans);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ផ្លាស់ប្តូរស្ថានភាពកម្ចីទៅជា កម្ចីខូច (Bad Loan)
app.put('/api/loans/:id/status', async (req, res) => {
    try {
        const { status } = req.body; // 'Active' or 'Bad Loan' or 'Closed'
        const loan = await Loan.findByIdAndUpdate(req.params.id, { status }, { new: true });
        res.json(loan);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

// គ. ការទូទាត់ប្រាក់ និងប្រមូលប្រាក់ (Repayments)
app.post('/api/repayments', async (req, res) => {
    try {
        const { receiptNo, loanId, coOfficer, principalPaid, interestPaid, penaltyPaid } = req.body;
        const totalPaid = Number(principalPaid) + Number(interestPaid) + Number(penaltyPaid);

        const tx = new Transaction({
            receiptNo, loanId, coOfficer, principalPaid, interestPaid, penaltyPaid, totalPaid
        });
        await tx.save();

        const loan = await Loan.findById(loanId);
        loan.paidAmount += totalPaid;
        loan.remainingBalance -= (Number(principalPaid) + Number(interestPaid));
        if (loan.remainingBalance <= 0) loan.status = 'Closed';
        await loan.save();

        res.status(201).json({ message: 'Success', tx });
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

// ឃ. បេឡាករ Clear ប្រាក់
app.put('/api/cashier/clear/:id', async (req, res) => {
    try {
        const tx = await Transaction.findByIdAndUpdate(req.params.id, {
            receivedByCashier: true,
            clearedAt: new Date()
        }, { new: true });
        res.json(tx);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

// ង. ចំណាយប្រចាំថ្ងៃ និងរបាយការណ៍
app.post('/api/expenses', async (req, res) => {
    try {
        const exp = new Expense(req.body);
        await exp.save();
        res.status(201).json(exp);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

app.get('/api/reports/summary', async (req, res) => {
    try {
        const totalLoans = await Loan.aggregate([{ $group: { _id: null, total: { $sum: '$amount' } } }]);
        const totalCollected = await Transaction.aggregate([{ $group: { _id: null, total: { $sum: '$totalPaid' } } }]);
        const totalExpenses = await Expense.aggregate([{ $group: { _id: null, total: { $sum: '$amount' } } }]);
        res.json({
            totalDisbursed: totalLoans[0]?.total || 0,
            totalCollected: totalCollected[0]?.total || 0,
            totalExpenses: totalExpenses[0]?.total || 0
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});


// ==========================================
// ៤. FRONTEND DASHBOARD (UI ងាយស្រួលប្រើប្រាស់)
// ==========================================
app.get('/', (req, res) => {
    res.send(`
        <!DOCTYPE html>
        <html lang="km">
        <head>
            <meta charset="UTF-8">
            <title>ប្រព័ន្ធគ្រប់គ្រងកម្ចី (Loan Management System)</title>
            <style>
                body { font-family: 'Khmer OS Battambang', sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
                h1 { color: #2c3e50; text-align: center; }
                .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: center; font-size: 14px; }
                th { background-color: #2ecc71; color: white; }
                .btn-green { background-color: #27ae60; color: white; border: none; padding: 6px 12px; cursor: pointer; border-radius: 4px; font-weight: bold; }
                .btn-green:hover { background-color: #219653; }
            </style>
        </head>
        <body>
            <h1>ប្រព័ន្ធគ្រប់គ្រងកម្ចី (Loan Management System)</h1>
            
            <div class="card">
                <h3>តារាងប្រមូលប្រាក់ប្រចាំថ្ងៃ និងទូទាត់</h3>
                <table>
                    <thead>
                        <tr>
                            <th>លេខកូដកម្ចី</th>
                            <th>ប្រាក់ត្រូវបង់សរុប</th>
                            <th>ប្រាក់ដើម</th>
                            <th>ការប្រាក់</th>
                            <th>ស្ថានភាព</th>
                            <th>សកម្មភាព (បង់ប្រាក់)</th>
                        </tr>
                    </thead>
                    <tbody id="loanTable">
                        <tr><td colspan="6">កំពុងទាញទិន្នន័យ...</td></tr>
                    </tbody>
                </table>
            </div>

            <script>
                async function loadLoans() {
                    const res = await fetch('/api/loans');
                    const loans = await res.json();
                    const tbody = document.getElementById('loanTable');
                    tbody.innerHTML = '';
                    if(loans.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="6">មិនមានទិន្នន័យកម្ចីទេ</td></tr>';
                        return;
                    }
                    loans.forEach(l => {
                        let nextDue = l.schedule.find(s => s.status === 'Unpaid') || l.schedule[0];
                        let dueAmount = nextDue ? nextDue.totalDue.toFixed(2) : 0;
                        tbody.innerHTML += \`
                            <tr>
                                <td>\${l.loanCode}</td>
                                <td>$\${dueAmount}</td>
                                <td>$\${nextDue ? nextDue.principalDue.toFixed(2) : 0}</td>
                                <td>$\${nextDue ? nextDue.interestDue.toFixed(2) : 0}</td>
                                <td>\${l.status}</td>
                                <td><button class="btn-green" onclick="makePayment('\${l._id}', \${nextDue ? nextDue.principalDue : 0}, \${nextDue ? nextDue.interestDue : 0})">បង់ប្រាក់</button></td>
                            </tr>
                        \`;
                    });
                }

                async function makePayment(loanId, principal, interest) {
                    let receiptNo = "REC-" + Math.floor(Math.random()*10000);
                    let res = await fetch('/api/repayments', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ receiptNo, loanId, principalPaid: principal, interestPaid: interest, penaltyPaid: 0, coOfficer: "Admin" })
                    });
                    if(res.ok) {
                        alert('បង់ប្រាក់ជោគជ័យ!');
                        loadLoans();
                    } else {
                        alert('មានបញ្ហាពេលបង់ប្រាក់');
                    }
                }

                loadLoans();
            </script>
        </body>
        </html>
    `);
});

// ==========================================
// ៥. START SERVER
// ==========================================
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
