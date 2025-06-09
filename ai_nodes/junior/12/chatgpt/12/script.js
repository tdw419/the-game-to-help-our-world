document.addEventListener("DOMContentLoaded", () => {
  const status = document.getElementById("status");
  status.textContent = "AI Hub is live. Ready for your command.";

  // Example command parser
  window.sendCommand = (command) => {
    status.textContent = `Executing: ${command}`;
    // Extend here for task routing
    if (command === "load_ai") {
      status.textContent = "🔁 Loading AI agent...";
      // Simulate future agent integration
    }
  };

  // Simulated startup
  console.log("AI Hub initialized.");
});
