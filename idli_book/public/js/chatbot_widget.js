frappe.provide('frappe.ui');

frappe.ui.ChatbotWidget = class ChatbotWidget {
    constructor() {
        this.setup();
    }

    setup() {
        this.make_components();
        this.bind_events();
        this.add_styles();
    }

    make_components() {
        // 1. Create Floating Action Button (FAB)
        this.$fab = $(`
            <div class="aibot-fab" title="Idli Book Assistant">
                <div class="aibot-fab-icon">
                     <!-- Assistant Icon -->
                     <svg style="width: 28px; height: 28px; fill: white;" viewBox="0 0 24 24">
                        <path d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A2.5,2.5 0 0,0 5,15.5A2.5,2.5 0 0,0 7.5,18A2.5,2.5 0 0,0 10,15.5A2.5,2.5 0 0,0 7.5,13M16.5,13A2.5,2.5 0 0,0 14,15.5A2.5,2.5 0 0,0 16.5,18A2.5,2.5 0 0,0 19,15.5A2.5,2.5 0 0,0 16.5,13Z" />
                    </svg>
                </div>
            </div>
        `).appendTo('body');

        // 2. Create Chat Container (Hidden by default)
        this.$container = $(`
            <div class="aibot-widget-container" style="display: none;">
                <div class="aibot-header">
                    <div class="aibot-header-title">
                        <svg style="width: 20px; height: 20px; fill: white; margin-right: 8px;" viewBox="0 0 24 24">
                            <path d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A2.5,2.5 0 0,0 5,15.5A2.5,2.5 0 0,0 7.5,18A2.5,2.5 0 0,0 10,15.5A2.5,2.5 0 0,0 7.5,13M16.5,13A2.5,2.5 0 0,0 14,15.5A2.5,2.5 0 0,0 16.5,18A2.5,2.5 0 0,0 19,15.5A2.5,2.5 0 0,0 16.5,13Z" />
                        </svg>
                        <span class="aibot-title-text">Idli Book Assistant</span>
                    </div>
                    <button class="aibot-close-btn">&times;</button>
                </div>
                <div class="aibot-content">
                    <div class="aibot-chat-interface">
                        <div class="aibot-messages"></div>
                        <div class="aibot-input-area">
                            <input type="text" class="aibot-input" placeholder="Ask anything..." />
                            <button class="aibot-send-btn">
                                <svg style="width: 20px; height: 20px; fill: white;" viewBox="0 0 24 24">
                                    <path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).appendTo('body');

        // References for easy access
        this.$messages = this.$container.find('.aibot-messages');
        this.$input = this.$container.find('.aibot-input');
        this.$send_btn = this.$container.find('.aibot-send-btn');
    }

    bind_events() {
        // Toggle Widget
        this.$fab.on('click', () => this.toggle_widget());

        // Close Widget
        this.$container.find('.aibot-close-btn').on('click', () => this.close_widget());

        // Send Message
        this.$send_btn.on('click', () => this.send_message());
        this.$input.on('keypress', (e) => {
            if (e.which === 13) this.send_message();
        });
    }

    toggle_widget() {
        if (this.$container.is(':visible')) {
            this.close_widget();
        } else {
            this.open_widget();
        }
    }

    open_widget() {
        this.$container.fadeIn(200);
        this.$input.focus();

        // Welcome message if first time
        if (this.$messages.children().length === 0) {
            this.add_message('assistant', 'Hello! I\'m your Idli Book Assistant. Ask me about invoices, customers, payments, or business summaries.');
        }
    }

    close_widget() {
        this.$container.fadeOut(200);
    }

    add_message(role, text) {
        const bubble = $(`<div class="aibot-msg ${role}"><div class="bubble">${frappe.utils.escape_html(text)}</div></div>`);
        this.$messages.append(bubble);
        this.$messages.scrollTop(this.$messages[0].scrollHeight);
    }

    async send_message() {
        const msg = this.$input.val().trim();
        if (!msg) return;

        // User Message
        this.add_message('user', msg);
        this.$input.val('');

        // Disable send while waiting
        this.$send_btn.prop('disabled', true);

        // Typing indicator
        const $typing = $(`<div class="aibot-msg assistant typing"><span>.</span><span>.</span><span>.</span></div>`).appendTo(this.$messages);
        this.$messages.scrollTop(this.$messages[0].scrollHeight);

        try {
            const response = await frappe.call({
                method: 'idli_book.api.chatbot.chat',
                args: { message: msg }
            });

            $typing.remove();

            const reply = response.message.response || "I didn't understand that.";
            this.add_message('assistant', reply);

        } catch (e) {
            $typing.remove();
            this.add_message('assistant', 'Error connecting to server. Please try again.');
            console.error(e);
        } finally {
            this.$send_btn.prop('disabled', false);
            this.$input.focus();
        }
    }

    add_styles() {
        if ($('#aibot-styles').length) return;
        $('head').append(`
            <style id="aibot-styles">
                /* FAB */
                .aibot-fab {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    width: 60px;
                    height: 60px;
                    background: linear-gradient(135deg, #2c3e50, #4ca1af);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                    z-index: 10001;
                    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                }
                .aibot-fab:hover { transform: scale(1.05); }
                
                /* Widget Container */
                .aibot-widget-container {
                    position: fixed;
                    bottom: 90px;
                    right: 20px;
                    width: 380px;
                    height: 500px;
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    z-index: 10002;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    font-family: 'Inter', sans-serif;
                }

                .aibot-header {
                    padding: 16px;
                    background: linear-gradient(135deg, #2c3e50, #4ca1af);
                    color: white;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .aibot-header-title { display: flex; align-items: center; font-weight: 600; font-size: 16px; }
                .aibot-close-btn { background:none; border:none; color:white; font-size:24px; cursor:pointer; padding:0; line-height:1; }
                
                .aibot-content { flex: 1; overflow: hidden; display: flex; flex-direction: column; }

                /* Chat Styles */
                .aibot-chat-interface { display:flex; flex-direction:column; height:100%; }
                .aibot-messages { flex:1; padding:15px; overflow-y:auto; background:#f4f6f9; display:flex; flex-direction:column; gap:10px; }
                .aibot-msg { display:flex; margin-bottom:5px; }
                .aibot-msg.user { flex-direction:row-reverse; }
                .aibot-msg .bubble { max-width:80%; padding:10px 14px; border-radius:12px; font-size:14px; line-height:1.4; }
                .aibot-msg.user .bubble { background:linear-gradient(135deg, #2c3e50, #4ca1af); color:white; border-bottom-right-radius:2px; }
                .aibot-msg.assistant .bubble { background:white; color:#333; border-bottom-left-radius:2px; box-shadow:0 2px 5px rgba(0,0,0,0.05); }
                
                .aibot-input-area { padding:15px; border-top:1px solid #eee; display:flex; gap:10px; }
                .aibot-input { flex:1; border:1px solid #ddd; padding:10px 15px; border-radius:20px; outline:none; transition:border 0.2s; }
                .aibot-input:focus { border-color:#2c3e50; }
                .aibot-send-btn { width:40px; height:40px; background:linear-gradient(135deg, #2c3e50, #4ca1af); border:none; border-radius:50%; display:flex; align-items:center; justify-content:center; cursor:pointer; flex-shrink:0; }
                .aibot-send-btn:hover { transform:scale(1.05); }
                .aibot-send-btn:disabled { opacity:0.6; cursor:not-allowed; }

                /* Typing Animation */
                .aibot-msg.typing span { animation: typing 1.4s infinite; display:inline-block; margin:0 1px; }
                .aibot-msg.typing span:nth-child(2) { animation-delay: 0.2s; }
                .aibot-msg.typing span:nth-child(3) { animation-delay: 0.4s; }
                
                @keyframes typing {
                    0%, 60%, 100% { transform: translateY(0); }
                    30% { transform: translateY(-5px); }
                }
            </style>
        `);
    }
};

$(document).on('app_ready', function () {
    frappe.chatbot_widget = new frappe.ui.ChatbotWidget();
});
