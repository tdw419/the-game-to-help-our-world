// main.js - AI Hub Core Logic v6.0 (Real-time Focus)

// --- Configuration ---
const WEBSOCKET_SERVER_URL = "ws://localhost:8080"; // <<< IMPORTANT: REPLACE WITH YOUR ACTUAL WEBSOCKET SERVER URL
const PING_INTERVAL = 5000; // milliseconds (5 seconds for client heartbeats to server)
const STALE_THRESHOLD = 15000; // milliseconds (15 seconds for yellow status)
const OFFLINE_THRESHOLD = 35000; // milliseconds (35 seconds for red status)

// --- Centralized Agent State (Now managed by the server) ---
// These will be initialized empty and populated by server messages
let agentState = {};
let messageBoard = []; // This array will hold all public posts, updated by server

// Tracks last ping time for heartbeat status (received from server)
const lastPingTime = {};

// --- WebSocket Connection ---
let ws;

function connectWebSocket() {
    ws = new WebSocket(WEBSOCKET_SERVER_URL);

    ws.onopen = () => {
        addMessageToBoard("SYSTEM", "Connected to real-time AI Hub server.");
        console.log("WebSocket connected.");
        // Request initial state from server upon connection
        ws.send(JSON.stringify({ type: "REQUEST_INITIAL_STATE" }));
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleServerMessage(data);
        } catch (e) {
            console.error("Failed to parse WebSocket message:", event.data, e);
        }
    };

    ws.onclose = (event) => {
        addMessageToBoard("SYSTEM", `Disconnected from server. Code: ${event.code}, Reason: ${event.reason}`);
        console.warn("WebSocket closed.", event);
        // Attempt to reconnect after a delay
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        addMessageToBoard("SYSTEM", "WebSocket error. Check server status.");
    };
}

function handleServerMessage(data) {
    switch (data.type) {
        case "INITIAL_STATE":
            agentState = data.agentState;
            messageBoard = data.messageBoard;
            renderUI();
            addMessageToBoard("SYSTEM", "Initial state loaded from server.");
            startClientHeartbeatLoop(); // Start sending client heartbeats after initial state
            break;
        case "MESSAGE_POSTED":
            messageBoard.push(data.post);
            renderUI();
            break;
        case "AGENT_LOG_UPDATE":
            if (agentState[data.agentKey]) {
                agentState[data.agentKey].log.push(data.logEntry);
                renderUI(); // Re-render to update agent's log
            }
            break;
        case "AGENT_STATE_UPDATE": // For general status or mood changes pushed by server
            if (agentState[data.agentKey]) {
                Object.assign(agentState[data.agentKey], data.update);
                renderUI();
            }
            break;
        case "HEARTBEAT":
            lastPingTime[data.agentKey] = Date.now();
            // Optional: update agent's status text directly based on server heartbeat
            if (agentState[data.agentKey]) {
                 agentState[data.agentKey].status = data.status || "Online"; // Server could send explicit status
            }
            renderUI(); // Re-render to update status indicators
            break;
        default:
            console.warn("Unknown message type from server:", data.type, data);
    }
}

// --- DOM Elements ---
const messageBoardLogElement = document.getElementById('message-board-log');
const userNameInput = document.getElementById('user-name-input');
const messageContentInput = document.getElementById('message-content-input');
const agentsDisplayPane = document.getElementById('agents-display-pane');

// --- Core Rendering Function ---
function renderUI() {
    // Clear previous agent cards
    agentsDisplayPane.innerHTML = '';

    // Render each agent's card
    for (const agentKey in agentState) {
        const agentData = agentState[agentKey];
        const agentDiv = document.createElement('div');
        agentDiv.className = 'agent-card';
        agentDiv.id = `agent-card-${agentKey}`; // Unique ID for updating status later

        // Determine heartbeat status
        const lastPing = lastPingTime[agentKey] || 0;
        const timeSinceLastPing = Date.now() - lastPing;
        let statusClass = 'offline'; // Default
        if (timeSinceLastPing < STALE_THRESHOLD) {
            statusClass = 'online';
        } else if (timeSinceLastPing < OFFLINE_THRESHOLD) {
            statusClass = 'stale';
        }

        agentDiv.innerHTML = `
            <div class="agent-status ${statusClass}" id="status-indicator-${agentKey}"></div>
            <h3>${agentData.title}</h3>
            <p><strong>Status:</strong> <span id="status-text-${agentKey}">${agentData.status}</span></p>
            <pre class="log" id="log-${agentKey}">${(agentData.log || []).join('\n')}</pre>
            <p><em>${agentData.prompt}</em></p>
        `;
        agentsDisplayPane.appendChild(agentDiv);

        // Auto-scroll agent log
        const logPre = document.getElementById(`log-${agentKey}`);
        if (logPre) {
            logPre.scrollTop = logPre.scrollHeight;
        }
    }

    // Render the Shared Message Board
    messageBoardLogElement.innerHTML = ''; // Clear existing log
    messageBoard.forEach(post => {
        const postElement = document.createElement('div');
        postElement.innerHTML = `<b>${post.sender}</b> [${new Date(post.timestamp).toLocaleTimeString()}]: ${post.message}`;
        messageBoardLogElement.appendChild(postElement);
    });
    messageBoardLogElement.scrollTop = messageBoardLogElement.scrollHeight; // Auto-scroll
}

// --- Message Board Posting Logic ---
function postMessageToBoard() {
    const sender = userNameInput.value.trim();
    const message = messageContentInput.value.trim();

    if (!sender || !message) {
        if (!sender) console.error("Please enter your name!");
        if (!message) console.error("Please enter a message to post!");
        return;
    }

    const newPost = {
        id: `post-${Date.now()}`,
        sender: sender,
        message: message,
        timestamp: Date.now()
    };
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "POST_MESSAGE", post: newPost }));
        messageContentInput.value = ''; // Clear input
    } else {
        console.error("WebSocket not connected. Message not sent to server.");
        // Optionally, add to local log anyway to indicate attempt
        addMessageToBoard("SYSTEM", "Failed to send message: Not connected to server.");
    }
}

// Helper to add messages to the main board UI (used for system messages too)
function addMessageToBoard(sender, message) {
    const postElement = document.createElement('div');
    postElement.innerHTML = `<b>${sender}</b> [${new Date().toLocaleTimeString()}]: ${message}`;
    messageBoardLogElement.appendChild(postElement);
    messageBoardLogElement.scrollTop = messageBoardLogElement.scrollHeight;
}


// --- Client Heartbeat to Server (to inform server of client's presence) ---
function sendClientHeartbeat() {
    const clientName = userNameInput.value.trim() || "Anonymous";
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "CLIENT_HEARTBEAT", client: clientName }));
    }
}

// Automatically send heartbeats from this client to the server
function startClientHeartbeatLoop() {
    // Initial ping
    sendClientHeartbeat();
    // Set up interval for continuous pings
    setInterval(sendClientHeartbeat, PING_INTERVAL);
}

// --- Export Functions ---
// Export message board log to a plain text file
function exportBoardLog() {
    let logContent = messageBoard.map(post => `${post.sender} [${new Date(post.timestamp).toLocaleTimeString()}]: ${post.message}`).join('\n');
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai_hub_board_log_${new Date().toISOString().slice(0,19).replace(/[:T]/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    addMessageToBoard("SYSTEM", "Board log exported as .txt!");
}

// Export message board log to a .pxl.png (JSON encoded as image)
function exportBoardLogToPxl() {
    const pxlData = {
        type: "message_board_log",
        timestamp: Date.now(),
        log: messageBoard.map(post => ({
            sender: post.sender,
            message: post.message,
            timestamp: post.timestamp
        }))
    };

    const jsonString = JSON.stringify(pxlData, null, 2);

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    const pixelSize = 2;
    canvas.width = 256 * pixelSize; // Example width, adjust for desired resolution
    canvas.height = Math.ceil(jsonString.length / (256 / 3)) * pixelSize; // Calculate height based on content

    for (let i = 0; i < jsonString.length; i++) {
        const charCode = jsonString.charCodeAt(i);
        const x = (i % (canvas.width / pixelSize)) * pixelSize;
        const y = Math.floor(i / (canvas.width / pixelSize)) * pixelSize;

        const r = (charCode % 256);
        const g = Math.floor((charCode / 256) % 256);
        const b = Math.floor((charCode / (256 * 256)) % 256);

        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.fillRect(x, y, pixelSize, pixelSize);
    }

    const link = document.createElement('a');
    link.download = `ai_hub_board_log_${new Date().toISOString().slice(0,19).replace(/[:T]/g, '-')}.pxl.png`;
    link.href = canvas.toDataURL('image/png');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    addMessageToBoard("SYSTEM", "Board log exported as .pxl.png!");
}

// Expose functions to the global scope for HTML calls
window.main = {
    postMessageToBoard: postMessageToBoard,
    exportBoardLog: exportBoardLog,
    exportBoardLogToPxl: exportBoardLogToPxl
};

// --- Initialization on Load ---
document.addEventListener('DOMContentLoaded', () => {
    // Set default user name if empty
    if (!userNameInput.value) {
        userNameInput.value = "Commander";
    }

    renderUI(); // Initial rendering (will be empty, awaiting server state)
    connectWebSocket(); // Establish connection to the server
});
