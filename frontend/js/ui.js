/**
 * BouleAI — UI Utilities
 */

const UI = {
    $(id) {
        return document.getElementById(id);
    },

    show(id) {
        const el = this.$(id);
        if (el) el.hidden = false;
    },

    hide(id) {
        const el = this.$(id);
        if (el) el.hidden = true;
    },

    markdownToHTML(text) {
        if (!text) return '';
        let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\n/g, '<br>');
        return html;
    },

    scrollToBottom(containerId) {
        const el = this.$(containerId);
        if (el) {
            el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
        }
    }
};

export default UI;
