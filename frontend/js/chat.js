/**
 * BouleAI — Chat Controller
 */
import API from './api.js';
import Auth from './auth.js';
import UI from './ui.js';

let currentChatId = null;

const Chat = {
    async init() {
        Auth.checkAuth();
        this.bindEvents();
        await this.loadChatList(true); // Initial load

        // Show user email
        const token = localStorage.getItem('access_token');
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                UI.$('user-email').textContent = payload.sub || '';
            } catch (e) { }
        }
    },

    bindEvents() {
        UI.$('logout-btn').onclick = () => Auth.logout();
        UI.$('new-chat-btn').onclick = () => this.createNewChat();
        UI.$('start-btn').onclick = () => this.createNewChat();

        const input = UI.$('prompt-input');
        input.oninput = () => {
            input.style.height = 'auto';
            input.style.height = (input.scrollHeight) + 'px';
            UI.$('send-btn').disabled = !input.value.trim();
        };

        input.onkeydown = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        };

        UI.$('send-btn').onclick = () => this.sendMessage();
    },

    async loadChatList(isInitial = false) {
        try {
            const chats = await API.fetch('/chats');
            const list = UI.$('chat-list');
            list.innerHTML = '';

            if (chats.length === 0 && isInitial) {
                UI.show('onboarding-overlay');
                return;
            }

            UI.hide('onboarding-overlay');

            chats.forEach(chat => {
                const item = document.createElement('div');
                item.className = `chat-item ${chat.id === currentChatId ? 'active' : ''}`;
                item.textContent = chat.title || 'Untitled Chat';
                item.onclick = () => this.switchChat(chat.id);
                list.appendChild(item);
            });

            if (isInitial && chats.length > 0) {
                this.switchChat(chats[0].id);
            }
        } catch (err) {
            this.showError(`Failed to load chats: ${err.message}`);
        }
    },

    async createNewChat() {
        try {
            const chat = await API.fetch('/chats', { method: 'POST' });
            currentChatId = chat.id;
            UI.hide('onboarding-overlay');
            await this.loadChatList();
            this.switchChat(chat.id);
        } catch (err) {
            this.showError(`Failed to create chat: ${err.message}`);
        }
    },

    async switchChat(chatId) {
        if (currentChatId !== chatId) {
            currentChatId = chatId;
            // Update active state in UI without full re-render of list if possible
            document.querySelectorAll('.chat-item').forEach(i => {
                i.classList.toggle('active', i.textContent === chatId || i.getAttribute('data-id') === chatId);
            });
            // Simplified: just reload list for now but update active class
            await this.loadChatList();
        }

        UI.$('chat-messages').innerHTML = '';
        try {
            const history = await API.fetch(`/chats/${chatId}`);
            if (history.messages && history.messages.length > 0) {
                UI.hide('onboarding-overlay');
                history.messages.forEach(msg => {
                    this.renderMessage(msg.role, msg.content, msg.deliberation_trace);
                });
                UI.scrollToBottom('chat-messages');
            } else {
                UI.show('onboarding-overlay');
            }
        } catch (err) {
            this.showError(`Failed to load chat history: ${err.message}`);
        }
    },

    async sendMessage() {
        const input = UI.$('prompt-input');
        const prompt = input.value.trim();
        if (!prompt || !currentChatId) return;

        input.value = '';
        input.style.height = 'auto';
        UI.$('send-btn').disabled = true;

        // Render user message Optimistically
        this.renderMessage('user', prompt);
        UI.scrollToBottom('chat-messages');

        try {
            const trace = await API.fetch(`/chats/${currentChatId}/message`, {
                method: 'POST',
                body: JSON.stringify({ prompt })
            });

            this.renderMessage('assistant', trace.verdict, trace);
            UI.scrollToBottom('chat-messages');
            this.loadChatList(); // Update title if needed
        } catch (err) {
            this.renderMessage('assistant', `Failed to get response: ${err.message}`);
            this.showError(`Council deliberation failed: ${err.message}`);
        } finally {
            UI.$('send-btn').disabled = false;
        }
    },

    renderMessage(role, content, trace = null) {
        const container = UI.$('chat-messages');
        const bubble = document.createElement('div');
        bubble.className = `message-bubble ${role}`;

        const avatar = role === 'user' ? 'U' : 'C';
        const avatarClass = role === 'user' ? 'user' : 'council';

        let html = `
            <div class="avatar ${avatarClass}">${avatar}</div>
            <div class="message-content">
                <div class="text">${UI.markdownToHTML(content)}</div>
        `;

        if (trace && trace.stage1_opinions) {
            html += `
                <div class="deliberation-dropdown">
                    <div class="dropdown-header" onclick="this.nextElementSibling.classList.toggle('active')">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                        View Council Deliberation Process
                    </div>
                    <div class="dropdown-body">
                        ${this.renderDeliberationDetails(trace)}
                    </div>
                </div>
            `;
        }

        html += `</div>`;
        bubble.innerHTML = html;
        container.appendChild(bubble);
    },

    renderDeliberationDetails(trace) {
        return `
            <div style="font-size: 0.85rem; color: var(--text-dim);">
                <div style="margin-bottom: 1.5rem;">
                    <h4 style="color: var(--accent); margin-bottom: 0.75rem; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em;">Stage 1: Independent Opinions</h4>
                    <div style="display: flex; gap: 0.75rem; overflow-x: auto; padding-bottom: 0.5rem; scrollbar-width: thin;">
                        ${trace.stage1_opinions.map(op => `
                            <div style="padding: 1rem; background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 10px; min-width: 220px; flex-shrink: 0;">
                                <strong style="color: var(--text); display: block; margin-bottom: 0.4rem;">${op.short_name}</strong>
                                <div style="font-size: 0.8rem; line-height: 1.5; color: var(--text-dim); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                                    ${op.response}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div style="margin-bottom: 1rem;">
                    <h4 style="color: var(--accent); margin-bottom: 0.75rem; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em;">Stage 2: Peer Cross-Review</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 0.75rem;">
                        ${trace.stage2_reviews.map(rev => rev.detailed_scores.map(score => `
                            <div style="padding: 0.85rem; background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 10px;">
                                <div style="font-size: 0.75rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between;">
                                    <span style="color: var(--primary); font-weight: 600;">Peer Review #${score.response_id}</span>
                                    <span style="color: var(--success);">Avg: ${((score.accuracy + score.insight + score.logic) / 3).toFixed(1)}</span>
                                </div>
                                <div style="font-style: italic; font-size: 0.8rem; line-height: 1.4;">
                                    "${score.critique.length > 80 ? score.critique.substring(0, 80) + '...' : score.critique}"
                                </div>
                            </div>
                        `).join('')).join('')}
                    </div>
                </div>
                
                <div style="margin-top: 1.25rem; padding-top: 1rem; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem;">
                    <span>Protocol: Boule-3-Stage-V2</span>
                    <span style="color: var(--text-dim);">Timing: ${trace.meta.timing.total_seconds}s</span>
                </div>
            </div>
        `;
    },

    showError(msg) {
        const toast = UI.$('error-toast');
        const message = UI.$('error-message');
        if (toast && message) {
            message.textContent = msg;
            toast.style.display = 'block';
            setTimeout(() => {
                toast.style.display = 'none';
            }, 5000);
        }
    }
};

Chat.init();
export default Chat;
