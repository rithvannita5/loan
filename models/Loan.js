const mongoose = require('mongoose');

const loanSchema = new mongoose.Schema({
    loanCode: String,
    borrowerId: { type: mongoose.Schema.Types.ObjectId, ref: 'Borrower' },
    amount: Number,
    loanType: { type: String, default: 'ការថេរដើមថេរ' },
    paymentFrequency: String,
    interestRate: Number,
    totalPayable: Number,
    remainingBalance: Number,
    coOfficer: String,
    status: { type: String, enum: ['Active', 'Bad Loan', 'Closed'], default: 'Active' },
    createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Loan', loanSchema);
