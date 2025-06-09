
const agents = ["chatgpt", "gemini", "claude", "grok"];
const statusColors = { responded: "green", idle: "yellow", silent: "red" };

window.onload = () => {
  window.logBox = document.getElementById("logBox");
  window.statusBoard = document.getElementById("statusBoard");
};

function broadcast() {
  const msg = document.getElementById("commanderInput").value.trim();
  if (!msg) return;
  const timestamp = new Date().toISOString();
  log(`[Commander @ ${timestamp}]: ${msg}`);
  document.getElementById("commanderInput").value = "";
  agents.forEach(agent => {
    updateStatus(agent, "responded");
    const response = simulateAgentResponse(agent, msg);
    setTimeout(() => log(`[${agent.toUpperCase()}]: ${response}`), Math.random() * 1000 + 300);
  });
}

function log(text) {
  logBox.innerText += text + "\n";
  logBox.scrollTop = logBox.scrollHeight;
}

function updateStatus(agent, state) {
  const existing = document.getElementById("status-" + agent);
  const el = existing || document.createElement("div");
  el.className = `agent ${statusColors[state]}`;
  el.innerText = agent.toUpperCase();
  el.id = "status-" + agent;
  if (!existing) statusBoard.appendChild(el);
}

function simulateAgentResponse(agent, message) {
  if (agent === "chatgpt") return "Acknowledged. Message logged.";
  if (agent === "gemini") return "Parsed structure. Ready to assist.";
  if (agent === "claude") return "Understood. Reflecting ethically.";
  if (agent === "grok") return "Signal received. Monitoring channels.";
  return "OK.";
}
