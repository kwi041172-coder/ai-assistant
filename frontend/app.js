(() => {
  const configuredUrl = window.APP_CONFIG?.API_BASE_URL;
  const API_BASE_URL = configuredUrl && configuredUrl !== "__API_BASE_URL__"
    ? configuredUrl.replace(/\/+$/, "")
    : window.location.protocol === "file:"
      ? "http://127.0.0.1:8000"
      : window.location.origin;
  const elements = {
    summary: document.querySelector("#summary-content"),
    dataList: document.querySelector("#data-list"),
    recordCount: document.querySelector("#record-count"),
    dataForm: document.querySelector("#data-form"),
    dataDate: document.querySelector("#data-date"),
    dataValue: document.querySelector("#data-value"),
    dataMemo: document.querySelector("#data-memo"),
    chatForm: document.querySelector("#chat-form"),
    chatInput: document.querySelector("#chat-input"),
    chatMessages: document.querySelector("#chat-messages"),
    sendButton: document.querySelector("#send-button"),
    conversationList: document.querySelector("#conversation-list"),
    toast: document.querySelector("#toast"),
  };
  let activeConversationId = null;
  let messages = [];
  let toastTimeout;

  function showToast(message) {
    elements.toast.textContent = message;
    elements.toast.classList.add("visible");
    window.clearTimeout(toastTimeout);
    toastTimeout = window.setTimeout(() => elements.toast.classList.remove("visible"), 3600);
  }

  async function request(path, options = {}) {
    let response;
    try {
      response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers: {
          ...(options.body ? { "Content-Type": "application/json" } : {}),
          ...options.headers,
        },
      });
    } catch {
      throw new Error("백엔드에 연결할 수 없습니다. 서버 주소와 실행 상태를 확인해 주세요.");
    }
    if (!response.ok) {
      let detail = `요청 실패 (${response.status})`;
      try {
        const body = await response.json();
        if (typeof body.detail === "string") detail = body.detail;
        else if (Array.isArray(body.detail)) detail = body.detail.map((item) => item.msg).join(", ");
      } catch {
        // Keep the explicit HTTP status when the response is not JSON.
      }
      throw new Error(detail);
    }
    return response.status === 204 ? null : response.json();
  }

  function formatNumber(value) {
    if (value === null || value === undefined) return "-";
    return new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(value);
  }

  function makeElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  async function loadSummary() {
    try {
      const summary = await request("/api/data/summary");
      elements.summary.replaceChildren();
      elements.summary.append(makeElement("p", "summary-period", summary.period || "데이터를 추가해 시작하세요"));
      const metricGrid = makeElement("div", "metric-grid");
      [
        ["레코드", `${summary.count}건`],
        ["합계", formatNumber(summary.metrics.total)],
        ["평균", formatNumber(summary.metrics.average)],
        ["최고 / 최저", `${formatNumber(summary.metrics.max)} / ${formatNumber(summary.metrics.min)}`],
      ].forEach(([label, value]) => {
        const metric = makeElement("div", "metric");
        metric.append(makeElement("span", "", label), makeElement("strong", "", value));
        metricGrid.append(metric);
      });
      elements.summary.append(metricGrid, makeElement("div", "trend-chip", summary.trend));
    } catch (error) {
      elements.summary.textContent = `요약을 불러오지 못했습니다: ${error.message}`;
    }
  }

  async function loadData() {
    try {
      const records = await request("/api/data");
      elements.recordCount.textContent = `${records.length}건`;
      elements.dataList.replaceChildren();
      if (!records.length) {
        elements.dataList.append(makeElement("p", "empty-note", "아직 데이터가 없습니다."));
        return;
      }
      records.forEach((record) => {
        const row = makeElement("div", "data-row");
        const main = makeElement("div", "data-row-main");
        main.append(
          makeElement("strong", "", `${record.date} · ${formatNumber(record.value)}`),
          makeElement("small", "", record.memo || "메모 없음"),
        );
        const actions = makeElement("div", "row-actions");
        const edit = makeElement("button", "", "수정");
        edit.type = "button";
        edit.addEventListener("click", () => editRecord(record));
        const remove = makeElement("button", "", "삭제");
        remove.type = "button";
        remove.addEventListener("click", () => deleteRecord(record.id));
        actions.append(edit, remove);
        row.append(main, actions);
        elements.dataList.append(row);
      });
    } catch (error) {
      elements.dataList.replaceChildren(makeElement("p", "empty-note", `데이터를 불러오지 못했습니다: ${error.message}`));
    }
  }

  async function refreshDataViews() {
    await Promise.all([loadData(), loadSummary()]);
  }

  async function editRecord(record) {
    const date = window.prompt("날짜 (YYYY-MM-DD)", record.date);
    if (date === null) return;
    const valueText = window.prompt("값", String(record.value));
    if (valueText === null) return;
    const value = Number(valueText);
    if (!date || !Number.isFinite(value)) {
      showToast("날짜와 유효한 숫자 값을 입력해 주세요.");
      return;
    }
    const memo = window.prompt("메모", record.memo || "");
    if (memo === null) return;
    try {
      await request(`/api/data/${encodeURIComponent(record.id)}`, {
        method: "PUT",
        body: JSON.stringify({ date, value, memo }),
      });
      showToast("데이터를 수정했습니다.");
      await refreshDataViews();
    } catch (error) {
      showToast(`수정 실패: ${error.message}`);
    }
  }

  async function deleteRecord(id) {
    if (!window.confirm("이 데이터를 삭제할까요?")) return;
    try {
      await request(`/api/data/${encodeURIComponent(id)}`, { method: "DELETE" });
      showToast("데이터를 삭제했습니다.");
      await refreshDataViews();
    } catch (error) {
      showToast(`삭제 실패: ${error.message}`);
    }
  }

  function appendMessage(role, content) {
    const emptyWelcome = elements.chatMessages.querySelector(".welcome-card");
    if (emptyWelcome) emptyWelcome.remove();
    const message = makeElement("div", `message ${role}`, content);
    elements.chatMessages.append(message);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }

  function displayMessages(messages) {
    elements.chatMessages.replaceChildren();
    messages.forEach((message) => appendMessage(message.role, message.content));
  }

  async function loadConversations() {
    try {
      const conversations = await request("/api/conversations");
      elements.conversationList.replaceChildren();
      if (!conversations.length) {
        elements.conversationList.append(makeElement("p", "empty-note", "저장된 대화가 없습니다."));
        return;
      }
      conversations.forEach((conversation) => {
        const item = makeElement("div", "conversation-item");
        const load = makeElement("button", "load-chat", conversation.title || "새 대화");
        load.type = "button";
        load.addEventListener("click", () => openConversation(conversation.id));
        const remove = makeElement("button", "delete-chat", "삭제");
        remove.type = "button";
        remove.setAttribute("aria-label", `대화 삭제: ${conversation.title}`);
        remove.addEventListener("click", () => deleteConversation(conversation.id));
        item.append(load, remove);
        elements.conversationList.append(item);
      });
    } catch (error) {
      elements.conversationList.replaceChildren(makeElement("p", "empty-note", `기록을 불러오지 못했습니다: ${error.message}`));
    }
  }

  async function openConversation(id) {
    try {
      const conversation = await request(`/api/conversations/${encodeURIComponent(id)}`);
      activeConversationId = conversation.id;
      messages = conversation.messages || [];
      displayMessages(messages);
    } catch (error) {
      showToast(`대화를 불러오지 못했습니다: ${error.message}`);
    }
  }

  async function deleteConversation(id) {
    if (!window.confirm("이 대화를 삭제할까요?")) return;
    try {
      await request(`/api/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });
      if (activeConversationId === id) startNewChat();
      showToast("대화를 삭제했습니다.");
      await loadConversations();
    } catch (error) {
      showToast(`삭제 실패: ${error.message}`);
    }
  }

  function startNewChat() {
    activeConversationId = null;
    messages = [];
    elements.chatMessages.replaceChildren();
    const welcome = makeElement("div", "welcome-card");
    welcome.append(
      makeElement("span", "welcome-star", "✦"),
      makeElement("h2", "", "데이터에 대해 물어보세요"),
      makeElement("p", "", "예: “전체 데이터의 최근 추세를 알려줘”"),
    );
    elements.chatMessages.append(welcome);
  }

  async function saveCurrentConversation() {
    if (!messages.length) return;
    const firstUserMessage = messages.find((message) => message.role === "user")?.content || "새 대화";
    const payload = {
      title: firstUserMessage.slice(0, 200),
      messages: messages.slice(-200),
    };
    const path = activeConversationId
      ? `/api/conversations/${encodeURIComponent(activeConversationId)}`
      : "/api/conversations";
    const saved = await request(path, {
      method: activeConversationId ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    activeConversationId = saved.id;
    await loadConversations();
  }

  elements.dataForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      date: elements.dataDate.value,
      value: Number(elements.dataValue.value),
      memo: elements.dataMemo.value.trim(),
    };
    try {
      await request("/api/data", { method: "POST", body: JSON.stringify(payload) });
      elements.dataForm.reset();
      showToast("데이터를 추가했습니다.");
      await refreshDataViews();
      await loadConversations();
    } catch (error) {
      showToast(`추가 실패: ${error.message}`);
    }
  });

  elements.chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = elements.chatInput.value.trim();
    if (!message || elements.sendButton.disabled) return;
    messages.push({ role: "user", content: message });
    appendMessage("user", message);
    elements.chatInput.value = "";
    const loading = makeElement("div", "loading-message", "답변을 준비하고 있어요...");
    elements.chatMessages.append(loading);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    elements.sendButton.disabled = true;
    try {
      const result = await request("/api/chat", {
        method: "POST",
        body: JSON.stringify({ message, messages: messages.slice(-40) }),
      });
      loading.remove();
      messages.push({ role: "assistant", content: result.response });
      appendMessage("assistant", result.response);
      if (result.warning) showToast(result.warning);
      await saveCurrentConversation().catch((error) => {
        showToast(`답변은 받았지만 대화를 저장하지 못했습니다: ${error.message}`);
      });
      await loadSummary();
    } catch (error) {
      loading.remove();
      showToast(`요청을 완료하지 못했습니다: ${error.message}`);
    } finally {
      elements.sendButton.disabled = false;
    }
  });

  document.querySelector("#refresh-summary").addEventListener("click", refreshDataViews);
  document.querySelector("#new-chat").addEventListener("click", startNewChat);
  elements.dataDate.value = new Date().toISOString().slice(0, 10);
  void Promise.all([refreshDataViews(), loadConversations()]);
})();
