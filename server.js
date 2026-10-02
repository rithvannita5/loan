const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(cors());

// បើកកន្លែងឲ្យអាន Frontend (HTML) ពីថត public
app.use(express.static(path.join(__dirname, 'public')));

// ភ្ជាប់ MongoDB Database
mongoose.connect(process.env.MONGO_URI || 'mongodb://localhost:27017/loan_db')
.then(() => console.log('MongoDB Connected Successfully!'))
.catch(err => console.log('DB Connection Error:', err));

// ហៅ Routes មកប្រើប្រាស់តាមផ្នែកនីមួយៗ
app.use('/api/auth', require('./routes/authRoutes'));
app.use('/api/borrowers', require('./routes/borrowerRoutes'));
app.use('/api/loans', require('./routes/loanRoutes'));

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
