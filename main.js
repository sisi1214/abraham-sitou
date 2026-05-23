// Renderer for DataBlog posts + cursor glow

function formatDate(d){
  const dt = new Date(d);
  return dt.toLocaleDateString(undefined, { year: 'numeric', month: 'short' });
}
function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

function renderPosts(posts){
  const grid = document.getElementById('blogGrid');
  if (!grid) return;
  grid.innerHTML = '';

  if (!posts || posts.length === 0) {
    const placeholder = document.createElement('div');
    placeholder.className = 'post-card';
    placeholder.style.animationDelay = '0.45s';
    placeholder.innerHTML = [
      `<div class="post-title">No posts yet</div>`,
      `<div class="post-excerpt">Add entries by editing <code>posts.json</code> in the site folder.</div>`
    ].join('');
    grid.appendChild(placeholder);
    return;
  }

  posts.forEach((p, i) => {
    const a = document.createElement('a');
    a.className = 'post-card';
    a.href = p.url || '#';
    if (!p.url || p.url === '#') a.setAttribute('role','button');
    a.style.animationDelay = (0.45 + i * 0.06) + 's';
    a.innerHTML = [
      `<div class="post-title">${escapeHtml(p.title)}</div>`,
      `<div class="post-excerpt">${escapeHtml(p.excerpt)}</div>`,
      `<div class="post-meta">`,
        `<div class="post-tags">${(p.tags||[]).map(t => `<span class="post-tag">${escapeHtml(t)}</span>`).join('')}</div>`,
        `<div class="post-date">${formatDate(p.date || new Date())}</div>`,
      `</div>`
    ].join('');
    grid.appendChild(a);
  });
}

// Try to fetch posts.json and render; fallback to placeholder on error
fetch('./posts.json', { cache: "no-store" })
  .then(res => {
    if (!res.ok) throw new Error('posts.json not found');
    return res.json();
  })
  .then(json => renderPosts(json))
  .catch(() => renderPosts([]));

// Cursor glow movement
const cursor = document.getElementById('glowCursor');
if (cursor) {
  document.addEventListener('mousemove', e => {
    cursor.style.left = e.clientX + 'px';
    cursor.style.top  = e.clientY + 'px';
  });
}
    cursor.style.left = e.clientX + 'px';
    cursor.style.top = e.clientY + 'px';
  });
}
// Cursor glow movement
const cursor = document.getElementById('glowCursor');
if (cursor) {
  document.addEventListener('mousemove', e => {
    cursor.style.left = e.clientX + 'px';
    cursor.style.top = e.clientY + 'px';
  });
}
