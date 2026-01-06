
frappe.ui.form.on('IB Journal Entry', {
    refresh: function (frm) {
    }
});

frappe.ui.form.on('IB Journal Entry Account', {
    debit: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.debit > 0) {
            frappe.model.set_value(cdt, cdn, 'credit', 0);
        }
        calculate_totals(frm);
    },
    credit: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.credit > 0) {
            frappe.model.set_value(cdt, cdn, 'debit', 0);
        }
        calculate_totals(frm);
    }
});

function calculate_totals(frm) {
    let total_debit = 0;
    let total_credit = 0;

    (frm.doc.entries || []).forEach(row => {
        total_debit += (row.debit || 0);
        total_credit += (row.credit || 0);
    });

    frm.set_value('total_debit', total_debit);
    frm.set_value('total_credit', total_credit);
}
