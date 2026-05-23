Project: Personal GitHub Page (Abraham Si Tou)

Structure
- index.html        — main page (keeps CSS inline for now)
- main.js           — client script: renders DataBlog and cursor glow
- posts.json        — DataBlog entries (edit this to add/remove posts)
- README.md         — this file

How to add a DataBlog post
1. Edit posts.json and add a new object with fields: title, date (YYYY-MM-DD), tags (array), excerpt, url.
2. The page will load posts.json on page load. If posts.json is missing or invalid, the page uses a built-in fallback.

Notes
- Keep posts.json in the same folder as index.html for the simplest workflow.
- If you want to move styles to a separate file later, create styles.css and update index.html to link it.
