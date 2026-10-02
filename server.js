const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const Borrower = require('./models/Borrower');
const Loan = require('./models/Loan');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(cors());

// តភ្ជាប់ MongoDB Atlas
mongoose.connect(process.env.MONGO_URI)
.then(() => console.log('MongoDB Connected Successfully!'))
.catch((err) => console.log('DB Connection Error:', err));

// Route មើលសាកល្បងថា Server ដំណើរការ
app.get('/', (req, res) => {
    res.send('Loan Management API is running...');
});

// API បញ្ចូលអ្នកខ្ចីថ្មី
app.post('/api/borrowers', async (req, res) => {
    try {
        const newBorrower = new Borrower(req.body);
        const saved = await newBorrower.save();
        res.status(201).json(saved);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

// API មើលបញ្ជីអ្នកខ្ចី
app.get('/api/borrowers', async (req, res) => {
    try {
        const borrowers = await Borrower.find();
        res.json(borrowers);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
