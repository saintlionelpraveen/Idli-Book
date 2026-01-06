
frappe.ui.form.on('IB Credit Note', {
    refresh: function (frm) {
    },
    is_tax_inclusive: function (frm) { calculate_totals(frm); }
});
frappe.ui.form.on('IB Invoice Item', {
    qty: function (frm) { calculate_totals(frm); },
    rate: function (frm) { calculate_totals(frm); }
});
function calculate_totals(frm) {
    let subtotal = 0;
    let tax = 0;
    (frm.doc.items || []).forEach(row => {
        let amt = (row.qty || 0) * (row.rate || 0);
        row.amount = amt;
        let taxable = amt;
        let t = 0;
        if (frm.doc.is_tax_inclusive) {
            if (row.tax_percentage) { taxable = amt / (1 + row.tax_percentage / 100); t = amt - taxable; }
        } else {
            if (row.tax_percentage) { t = amt * (row.tax_percentage / 100); }
        }
        subtotal += taxable;
        tax += t;
        frappe.model.set_value(row.doctype, row.name, 'amount', amt);
    });
    frm.set_value('subtotal', subtotal);
    frm.set_value('tax_amount', tax);
    frm.set_value('grand_total', subtotal + tax);
}
