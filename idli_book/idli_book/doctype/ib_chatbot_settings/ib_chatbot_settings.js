// Copyright (c) 2026, Praveen and contributors
// For license information, please see license.txt

frappe.ui.form.on('IB Chatbot Settings', {
    refresh: function (frm) {
        frm.set_intro(__('Configure AI Chatbot settings for Idli Book'));

        if (!frm.doc.api_key) {
            frm.set_intro(__('Please enter your OpenAI API key to enable chatbot'), 'yellow');
        }
    }
});
