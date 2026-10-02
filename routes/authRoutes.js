const router = require('express').Router();

router.post('/login', (req, res) => {
    const { username, password } = req.body;
    if (username === 'admin' && password === '123456') {
        res.json({ success: true, message: 'ជោគជ័យ' });
    } else {
        res.status(401).json({ success: false, message: 'ឈ្មោះអ្នកប្រើប្រាស់ ឬពាក្យសម្ងាត់មិនត្រូវ!' });
    }
});

module.exports = router;
