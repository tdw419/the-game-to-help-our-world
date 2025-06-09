let posts = [];

function renderPosts() {
  const postsDiv = document.getElementById("posts");
  postsDiv.innerHTML = "";
  posts.forEach(post => {
    const div = document.createElement("div");
    div.className = "post";
    div.innerHTML = `
      <div class="post-title">${post.title}</div>
      <div class="post-body">${post.body}</div>
      <div style="color:#888; margin-top:5px;">From: ${post.author}</div>
    `;
    postsDiv.appendChild(div);
  });
}

function addPost(author = "Commander") {
  const title = document.getElementById("titleInput").value.trim();
  const body = document.getElementById("bodyInput").value.trim();
  if (!title || !body) return;
  posts.push({ title, body, author });
  document.getElementById("titleInput").value = "";
  document.getElementById("bodyInput").value = "";
  renderPosts();
}

// For AI to respond only when explicitly commanded
function addAiPost(title, body, author = "Junior") {
  posts.push({ title, body, author });
  renderPosts();
}

window.onload = () => {
  renderPosts();
};
