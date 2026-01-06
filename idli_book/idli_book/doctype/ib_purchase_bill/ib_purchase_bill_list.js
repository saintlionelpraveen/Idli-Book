frappe.listview_settings['IB Purchase Bill'] = {
    formatters: {
        status(value) {
            const status_colors = {
                'Draft': 'gray',
                'Awaiting Payment': 'orange',
                'Partially Paid': 'yellow',
                'Paid': 'green',
                'Cancelled': 'red'
            };
            return `<span class="indicator-pill ${status_colors[value] || 'gray'}">${value}</span>`;
        }
    },

    get_indicator: function (doc) {
        const status_colors = {
            'Draft': ['Draft', 'gray', 'status,=,Draft'],
            'Awaiting Payment': ['Awaiting Payment', 'orange', 'status,=,Awaiting Payment'],
            'Partially Paid': ['Partially Paid', 'yellow', 'status,=,Partially Paid'],
            'Paid': ['Paid', 'green', 'status,=,Paid'],
            'Cancelled': ['Cancelled', 'red', 'status,=,Cancelled']
        };
        return status_colors[doc.status] || ['Unknown', 'gray'];
    }
};
