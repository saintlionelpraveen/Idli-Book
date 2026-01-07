frappe.listview_settings['IB GL Entry'] = {
    add_fields: ["transaction_type", "is_cancelled", "debit", "credit"],

    get_indicator: function (doc) {
        // Cancelled entries
        if (doc.is_cancelled == 1) {
            return [__("Cancelled"), "red", "is_cancelled,=,1"];
        }

        // Color code by transaction type
        if (doc.transaction_type === "IB Sales Invoice") {
            return [__("Sales"), "blue", "transaction_type,=,IB Sales Invoice"];
        } else if (doc.transaction_type === "IB Purchase Bill") {
            return [__("Purchase"), "orange", "transaction_type,=,IB Purchase Bill"];
        } else if (doc.transaction_type === "IB Payment") {
            return [__("Payment"), "green", "transaction_type,=,IB Payment"];
        }

        return [__("Active"), "grey", "is_cancelled,=,0"];
    }
};
