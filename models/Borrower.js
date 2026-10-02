const mongoose = require('mongoose');

const borrowerSchema = new mongoose.Schema({
    code: String,
    name: String,
    gender: String,
    phone: String,
    dob: String,
    nationalId: String,
    address: String,
    guarantor: {
        name: String,
        gender: String,
        nationalId: String,
        dob: String,
        phone: String,
        address: String,
        relation: String
    }
});

module.exports = mongoose.model('Borrower', borrowerSchema);
