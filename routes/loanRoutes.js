const router = require('express').Router();
const Loan = require('../models/Loan');

// ទាញយកកម្ចីទាំងអស់ និងទិន្នន័យស្ថិតិ
router.get('/', async (req, res) => {
    try {
        const loans = await Loan.find().populate('borrowerId');
        const borrowersCount = await require('../models/Borrower').countDocuments();
        const activeLoansCount = await Loan.countDocuments({ status: 'Active' });
        const badLoans = await Loan.find({ status: 'Bad Loan' });
        const badLoansTotalAmount = badLoans.reduce((sum, l) => sum + (l.remainingBalance || 0), 0);

        res.json({
            loans,
            stats: {
                borrowersCount,
                activeLoansCount,
                badLoansCount: badLoans.length,
                badLoansTotalAmount
            }
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ផ្លាស់ប្តូរស្ថានភាពកម្ចី (ឧ. ទៅជា Bad Loan)
router.put('/:id/status', async (req, res) => {
    try {
        const updated = await Loan.findByIdAndUpdate(req.params.id, { status: req.body.status }, { new: true });
        res.json(updated);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

module.exports = router;
