const mongoose = require('mongoose');

const loanSchema = new mongoose.Schema({
    loanCode: { type: String, required: true, unique: true },
    borrowerId: { type: mongoose.Schema.Types.ObjectId, ref: 'Borrower', required: true },
    disburseDate: { type: Date, default: Date.now },
    firstPaymentDate: Date,
    duration: Number,
    paymentFrequency: { type: String, enum: ['Daily', 'Weekly', 'Bi-Weekly', 'Monthly'] },
    amount: { type: Number, required: true },
    currency: { type: String, default: 'USD' },
    loanType: String,
    interestRate: Number,
    totalInterest: Number,
    totalPayable: Number,
    paidAmount: { type: Number, default: 0 },
    remainingBalance: Number,
    coOfficer: String,
    status: { type: String, enum: ['Active', 'Bad Loan', 'Closed', 'Pending'], default: 'Active' },
    schedule: [{
        installmentNumber: Number,
        dueDate: Date,
        principalDue: Number,
        interestDue: Number,
        totalDue: Number,
        status: { type: String, default: 'Unpaid' }
    }],
    createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Loan', loanSchema);
