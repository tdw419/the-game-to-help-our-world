const threadContainer = document.getElementById("threads");

const threadList = [
  "threads/001.json",
  "threads/002.json"
];

function loadThread(url) {
  fetch(url)
    .then(res => res.json())
    .then(data => {
      const div = document.createElement("div");
      div.className = "thread";
      div.innerHTML = `
        <div class="title">${data.title}</div>
        <div class="post">${data.body}</div>
      `;
      threadContainer.appendChild(div);
    })
    .catch(err => {
      console.error("Error loading", url, err);
    });
}

threadContainer.innerHTML = "";
threadList.forEach(loadThread);
