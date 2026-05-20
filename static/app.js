const state = {
  config: null,
  sessionId: null,
  participantId: "student-001",
  personality: "conscientiousness",
  task: "dedupe",
  turnId: 1,
};

const els = {
  participantId: document.querySelector("#participantId"),
  personalitySelect: document.querySelector("#personalitySelect"),
  taskSelect: document.querySelector("#taskSelect"),
  startButton: document.querySelector("#startButton"),
  personalityInfo: document.querySelector("#personalityInfo"),
  taskInfo: document.querySelector("#taskInfo"),
  chatTitle: document.querySelector("#chatTitle"),
  chatSubtitle: document.querySelector("#chatSubtitle"),
  messages: document.querySelector("#messages"),
  messageForm: document.querySelector("#messageForm"),
  studentMessage: document.querySelector("#studentMessage"),
  logButton: document.querySelector("#logButton"),
  logDialog: document.querySelector("#logDialog"),
  closeLogButton: document.querySelector("#closeLogButton"),
  logContent: document.querySelector("#logContent"),
};

async function init() {
  const response = await fetch("/api/config");
  state.config = await response.json();
  renderSelectors();
  renderSelectedInfo();
  bindEvents();
}

function renderSelectors() {
  els.personalitySelect.innerHTML = state.config.personalities
    .map((item) => `<option value="${item.key}">${item.name}</option>`)
    .join("");
  els.taskSelect.innerHTML = state.config.tasks
    .map((item) => `<option value="${item.key}">${item.title}（${item.difficulty}）</option>`)
    .join("");
  els.personalitySelect.value = state.personality;
  els.taskSelect.value = state.task;
}

function renderSelectedInfo() {
  const personality = getPersonality();
  const task = getTask();
  els.personalityInfo.innerHTML = `
    <strong>${personality.name}</strong>
    <p>${personality.description}</p>
  `;
  els.taskInfo.innerHTML = `
    <strong>${task.title}</strong>
    <p>${task.prompt}</p>
    <div class="constraints">
      <strong>数据范围</strong>
      <ul>
        ${task.constraints.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
      </ul>
    </div>
    <pre>${escapeHtml(task.example)}</pre>
    <div class="knowledge-points">
      ${task.knowledge_points.map((point) => `<span>${point}</span>`).join("")}
    </div>
  `;
  els.chatTitle.textContent = `${personality.short_name}智能体：${task.title}`;
  els.chatSubtitle.textContent = "你的目标是像老师一样教会 AI，而不是只贴答案。";
}

function bindEvents() {
  els.personalitySelect.addEventListener("change", () => {
    state.personality = els.personalitySelect.value;
    renderSelectedInfo();
  });

  els.taskSelect.addEventListener("change", () => {
    state.task = els.taskSelect.value;
    renderSelectedInfo();
  });

  els.startButton.addEventListener("click", startSession);
  els.messageForm.addEventListener("submit", sendMessage);
  els.logButton.addEventListener("click", showLogs);
  els.closeLogButton.addEventListener("click", () => els.logDialog.close());
}

async function startSession() {
  state.participantId = els.participantId.value.trim() || "anonymous";
  state.personality = els.personalitySelect.value;
  state.task = els.taskSelect.value;
  const response = await fetch("/api/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      participant_id: state.participantId,
      personality: state.personality,
      task: state.task,
    }),
  });
  const data = await response.json();
  state.sessionId = data.session_id;
  state.turnId = 1;
  els.messages.innerHTML = "";
  addMessage("agent", data.agent_message);
}

async function sendMessage(event) {
  event.preventDefault();
  const message = els.studentMessage.value.trim();
  if (!message) return;
  if (!state.sessionId) {
    await startSession();
  }
  addMessage("student", message);
  els.studentMessage.value = "";

  const response = await fetch("/api/message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: state.sessionId,
      participant_id: state.participantId,
      personality: state.personality,
      task: state.task,
      turn_id: state.turnId,
      message,
    }),
  });
  const data = await response.json();
  if (!response.ok) {
    addMessage("agent", `大模型调用失败：${data.error || "未知错误"}`);
    return;
  }
  state.turnId = data.turn_id;
  addMessage("agent", data.agent_message);
}

async function showLogs() {
  const response = await fetch("/api/logs");
  const data = await response.json();
  els.logContent.textContent = JSON.stringify(data.items, null, 2);
  els.logDialog.showModal();
}

function addMessage(role, content) {
  const node = document.createElement("div");
  node.className = `message ${role}`;
  node.innerHTML = `
    <div class="message-meta">${role === "agent" ? "AI 学生" : "学生老师"}</div>
    <div>${escapeHtml(content)}</div>
  `;
  els.messages.appendChild(node);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function getPersonality() {
  return state.config.personalities.find((item) => item.key === state.personality);
}

function getTask() {
  return state.config.tasks.find((item) => item.key === state.task);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

init().catch((error) => {
  els.messages.innerHTML = `<div class="message agent">启动失败：${escapeHtml(error.message)}</div>`;
});
