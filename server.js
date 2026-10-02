const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(express.json());
app.use(cors());

// ភ្ជាប់ MongoDB
mongoose.connect(process.env.MONGO_URI)
.then(() => console.log('MongoDB Connected!'))
.catch(err => console.log(err));

// ហៅ Routes មកប្រើប្រាស់
app.use('/api/auth', require('./routes/authRoutes'));
app.use('/api/borrowers', require('./routes/borrowerRoutes'));
app.use('/api/loans', require('./routes/loanRoutes'));

app.listen(3000, () => console.log('Server running on port 3000'));
