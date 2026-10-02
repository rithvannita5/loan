const mongoose = require('mongoose');

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

module.exports = mongoose.model('Borrower', borrowerSchema);
