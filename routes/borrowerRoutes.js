const router = require('express').Router();
const Borrower = require('../models/Borrower');

router.get('/', async (req, res) => {
    try {
        const borrowers = await Borrower.find();
        res.json(borrowers);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
