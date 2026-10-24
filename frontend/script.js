const API_BASE_URL = (window.API_BASE_URL || 'http://127.0.0.1:8000/api').replace(/\/+$/, '');

const state = {
    messages: [],
    conversations: [],
    currentConversationId: null,
    dataList: [],
    isLoading: false
};

const elements = {
    app: document.querySelector('.container'),
    tabButtons: document.querySelectorAll('.tab-btn'),
    chatTab: document.getElementById('chat-tab'),
    historyTab: document.getElementById('history-tab'),
    chatMessages: document.getElementById('chat-messages'),
    chatForm: document.getElementById('chat-form'),
    chatInput: document.getElementById('chat-input'),
    sendButton: document.querySelector('.btn-send'),
    dataForm: document.getElementById('data-form'),
    dataDate: document.getElementById('data-date'),
    dataValue: document.getElementById('data-value'),
    dataMemo: document.getElementById('data-memo'),
    dataList: document.getElementById('data-list'),
    summaryBox: document.getElementById('summary-box'),
    saveConversationButton: document.getElementById('save-conversation-btn'),
    newConversationButton: document.getElementById('new-conversation-btn'),
    conversationList: document.getElementById('conversation-list'),
    conversationDetail: document.getElementById('conversation-detail'),
    detailMessages: document.getElementById('detail-messages'),
    backToListButton: document.getElementById('back-to-list-btn')
};

document.addEventListener('DOMContentLoaded', initialize);

function initialize() {
    elements.tabButtons.forEach(button => button.addEventListener('click', () => switchTab(button.dataset.tab)));
    elements.chatForm.addEventListener('submit', handleChatSubmit);
    elements.dataForm.addEventListener('submit', handleDataSubmit);
    elements.saveConversationButton.addEventListener('click', () => saveConversation(true));
    elements.newConversationButton.addEventListener('click', startNewConversation);
    elements.backToListButton.addEventListener('click', showConversationList);
    elements.dataDate.value = new Date().toISOString().slice(0, 10);

    elements.dataList.addEventListener('click', event => {
        const button = event.target.closest('[data-delete-data]');
        if (button) deleteData(button.dataset.deleteData);
    });
    elements.conversationList.addEventListener('click', event => {
        const button = event.target.closest('[data-conversation-action]');
        if (!button) return;
        if (button.dataset.conversationAction === 'open') {
            loadConversationDetail(button.dataset.conversationId);
        } else {
            deleteConversation(button.dataset.conversationId);
        }
    });

    loadAppData();
}

async function loadAppData() {
    const results = await Promise.allSettled([loadData(), loadConversations()]);
    results.filter(result => result.status === 'rejected')
        .forEach(result => console.error('초기 데이터 로드 실패:', result.reason));
}

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers: {
            ...(options.body ? { 'Content-Type': 'application/json' } : {}),
            ...options.headers
        }
    });

    if (!response.ok) {
        let message = `API 오류 (${response.status})`;
        try {
            const payload = await response.json();
            message = payload.detail || payload.message || message;
        } catch {
            // Keep the HTTP status message when the response is not JSON.
        }
        throw new Error(message);
    }

    if (response.status === 204) return null;
    return response.json();
}

function switchTab(tabName) {
    elements.tabButtons.forEach(button => button.classList.toggle('active', button.dataset.tab === tabName));
    elements.chatTab.classList.toggle('active', tabName === 'chat');
    elements.historyTab.classList.toggle('active', tabName === 'history');
}

async function handleChatSubmit(event) {
    event.preventDefault();
    const content = elements.chatInput.value.trim();
    if (!content || state.isLoading) return;

    state.messages.push({ role: 'user', content });
    appendMessage(elements.chatMessages, 'user', content);
    elements.chatInput.value = '';
    setChatLoading(true);

    try {
        const result = await apiRequest('/chat', {
            method: 'POST',
            body: JSON.stringify({
                message: content,
                messages: state.messages.slice(-100)
            })
        });
        state.messages.push({ role: 'assistant', content: result.response });
        appendMessage(elements.chatMessages, 'assistant', result.response);
        renderSummary(result.summary);
        if (result.warning) {
            appendMessage(elements.chatMessages, 'system', result.warning);
        } else {
            await saveConversation(false);
        }
    } catch (error) {
        console.error('AI 응답 요청 실패:', error);
        appendMessage(elements.chatMessages, 'system', `응답을 받지 못했습니다: ${error.message}`);
    } finally {
        setChatLoading(false);
    }
}

function setChatLoading(loading) {
    state.isLoading = loading;
    elements.sendButton.disabled = loading;
    elements.chatInput.disabled = loading;
    elements.sendButton.textContent = loading ? '응답 중…' : '전송';
    if (loading) {
        const indicator = document.createElement('div');
        indicator.className = 'message assistant loading';
        indicator.id = 'loading-message';
        indicator.setAttribute('aria-label', '응답 생성 중');
        indicator.innerHTML = '<span></span><span></span><span></span>';
        elements.chatMessages.appendChild(indicator);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    } else {
        document.getElementById('loading-message')?.remove();
    }
}

function appendMessage(container, role, content) {
    const message = document.createElement('div');
    message.className = `message ${role}`;
    const paragraph = document.createElement('p');
    paragraph.textContent = content;
    message.appendChild(paragraph);
    container.appendChild(message);
    container.scrollTop = container.scrollHeight;
}

async function handleDataSubmit(event) {
    event.preventDefault();
    const record = {
        date: elements.dataDate.value,
        value: Number(elements.dataValue.value),
        memo: elements.dataMemo.value.trim()
    };
    if (!record.date || !Number.isFinite(record.value)) {
        alert('날짜와 유효한 숫자 값을 입력해 주세요.');
        return;
    }

    try {
        await apiRequest('/data', { method: 'POST', body: JSON.stringify(record) });
        elements.dataForm.reset();
        elements.dataDate.value = new Date().toISOString().slice(0, 10);
        await loadData();
        alert('데이터가 저장되었습니다.');
    } catch (error) {
        console.error('데이터 저장 실패:', error);
        alert(`데이터 저장에 실패했습니다: ${error.message}`);
    }
}

async function loadData() {
    try {
        state.dataList = await apiRequest('/data');
        renderData();
        renderSummary(await apiRequest('/data/summary'));
    } catch (error) {
        elements.dataList.textContent = `데이터를 불러오지 못했습니다: ${error.message}`;
        elements.summaryBox.textContent = `요약을 불러오지 못했습니다: ${error.message}`;
        throw error;
    }
}

function renderData() {
    elements.dataList.replaceChildren();
    if (!state.dataList.length) {
        elements.dataList.textContent = '저장된 데이터가 없습니다.';
        return;
    }

    state.dataList.forEach(item => {
        const row = document.createElement('article');
        row.className = 'data-item';
        const info = document.createElement('div');
        info.className = 'data-item-info';
        const date = document.createElement('div');
        date.className = 'data-item-date';
        date.textContent = item.date;
        const value = document.createElement('div');
        value.className = 'data-item-value';
        value.textContent = `값: ${item.value}`;
        info.append(date, value);
        if (item.memo) {
            const memo = document.createElement('div');
            memo.className = 'data-item-memo';
            memo.textContent = item.memo;
            info.appendChild(memo);
        }
        const remove = document.createElement('button');
        remove.className = 'btn-delete';
        remove.type = 'button';
        remove.dataset.deleteData = item.id;
        remove.textContent = '삭제';
        row.append(info, remove);
        elements.dataList.appendChild(row);
    });
}

function renderSummary(summary) {
    if (!summary) return;
    const { metrics = {} } = summary;
    const lines = [
        `기간: ${summary.period || '데이터 없음'}`,
        `레코드: ${summary.count ?? 0}개`,
        `합계: ${metrics.total ?? 0}`,
        `평균: ${metrics.average ?? 0}`,
        `최대 / 최소: ${metrics.max ?? 0} / ${metrics.min ?? 0}`,
        `추세: ${summary.trend || '분석 불가'}`
    ];
    elements.summaryBox.replaceChildren(...lines.map(text => {
        const line = document.createElement('p');
        line.textContent = text;
        return line;
    }));
}

async function deleteData(id) {
    if (!confirm('이 데이터를 삭제하시겠습니까?')) return;
    try {
        await apiRequest(`/data/${encodeURIComponent(id)}`, { method: 'DELETE' });
        await loadData();
    } catch (error) {
        console.error('데이터 삭제 실패:', error);
        alert(`데이터 삭제에 실패했습니다: ${error.message}`);
    }
}

async function saveConversation(showMessage) {
    if (!state.messages.length) {
        if (showMessage) alert('저장할 대화가 없습니다.');
        return;
    }

    const firstUserMessage = state.messages.find(message => message.role === 'user')?.content || '새 대화';
    const payload = {
        title: firstUserMessage.slice(0, 100),
        messages: state.messages
    };
    try {
        const saved = await apiRequest(
            state.currentConversationId
                ? `/conversations/${encodeURIComponent(state.currentConversationId)}`
                : '/conversations',
            {
                method: state.currentConversationId ? 'PUT' : 'POST',
                body: JSON.stringify(payload)
            }
        );
        state.currentConversationId = saved.id;
        await loadConversations();
        if (showMessage) alert('대화가 저장되었습니다.');
    } catch (error) {
        console.error('대화 저장 실패:', error);
        if (showMessage) alert(`대화 저장에 실패했습니다: ${error.message}`);
    }
}

async function loadConversations() {
    try {
        state.conversations = await apiRequest('/conversations');
        renderConversations();
    } catch (error) {
        elements.conversationList.textContent = `대화 기록을 불러오지 못했습니다: ${error.message}`;
        throw error;
    }
}

function renderConversations() {
    elements.conversationList.replaceChildren();
    if (!state.conversations.length) {
        elements.conversationList.textContent = '저장된 대화가 없습니다.';
        return;
    }

    state.conversations.forEach(conversation => {
        const row = document.createElement('article');
        row.className = 'conversation-item';
        const open = document.createElement('button');
        open.className = 'conversation-title';
        open.type = 'button';
        open.dataset.conversationAction = 'open';
        open.dataset.conversationId = conversation.id;
        open.textContent = conversation.title;
        const date = document.createElement('div');
        date.className = 'conversation-date';
        date.textContent = formatDate(conversation.updated_at || conversation.created_at);
        const remove = document.createElement('button');
        remove.className = 'btn-delete';
        remove.type = 'button';
        remove.dataset.conversationAction = 'delete';
        remove.dataset.conversationId = conversation.id;
        remove.textContent = '삭제';
        row.append(open, date, remove);
        elements.conversationList.appendChild(row);
    });
}

async function loadConversationDetail(id) {
    try {
        const conversation = await apiRequest(`/conversations/${encodeURIComponent(id)}`);
        elements.detailMessages.replaceChildren();
        conversation.messages.forEach(message => appendMessage(elements.detailMessages, message.role, message.content));
        elements.conversationList.hidden = true;
        elements.conversationDetail.hidden = false;
    } catch (error) {
        console.error('대화 상세 조회 실패:', error);
        alert(`대화를 불러오지 못했습니다: ${error.message}`);
    }
}

function showConversationList() {
    elements.conversationDetail.hidden = true;
    elements.conversationList.hidden = false;
}

function startNewConversation() {
    state.messages = [];
    state.currentConversationId = null;
    elements.chatMessages.replaceChildren();
    appendMessage(elements.chatMessages, 'system', '새 대화를 시작합니다. 무엇을 도와드릴까요?');
    elements.chatInput.value = '';
    showConversationList();
    switchTab('chat');
    elements.chatInput.focus();
}

async function deleteConversation(id) {
    if (!confirm('이 대화를 삭제하시겠습니까?')) return;
    try {
        await apiRequest(`/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' });
        if (state.currentConversationId === id) state.currentConversationId = null;
        await loadConversations();
    } catch (error) {
        console.error('대화 삭제 실패:', error);
        alert(`대화 삭제에 실패했습니다: ${error.message}`);
    }
}

function formatDate(value) {
    if (!value) return '';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ko-KR');
}

elements.chatInput.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        elements.chatForm.requestSubmit();
    }
});
