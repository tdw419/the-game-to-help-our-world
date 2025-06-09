const forum = document.getElementById('forum');

function postMessage() {
  const author = document.getElementById('author').value.trim();
  const message = document.getElementById('message').value.trim();
  if (!author || !message) return;

  const postDiv = document.createElement('div');
  postDiv.className = 'post';
  postDiv.innerHTML = `<div class="author">${author}</div><div class="message">${message}</div>`;
  forum.prepend(postDiv);

  document.getElementById('message').value = '';
}
