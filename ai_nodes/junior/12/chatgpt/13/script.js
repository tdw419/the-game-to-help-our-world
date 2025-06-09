document.addEventListener("DOMContentLoaded", () => {
  const status = document.getElementById("status");

  fetch("session.json")
    .then(response => {
      if (!response.ok) throw new Error("Session data not found.");
      return response.json();
    })
    .then(data => {
      status.textContent = `Welcome back, ${data.user} 👋. Active goal: "${data.shared_goals[0]}"`;
      console.log("Session loaded:", data);
    })
    .catch(error => {
      status.textContent = "⚠️ Failed to load session memory.";
      console.error(error);
    });
});
