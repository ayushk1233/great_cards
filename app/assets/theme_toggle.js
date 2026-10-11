// One-click light/dark toggle (top right). It drives Streamlit's own theme switcher in the main
// menu, so the choice is stored by Streamlit, applies without a reload, and the chat is kept.
// Relies on the menu's data-testids (stMainMenuButton, stMainMenuItem-theme-Light/Dark), which is
// fine while streamlit is pinned in requirements.txt. Written without a less-than sign so the
// page sanitiser never mistakes part of it for a tag.
(function () {
  // Streamlit may re-create the button on a rerun and run this script again, so everything is
  // installed once per page (window flag) and the button is looked up fresh each time.
  if (window.__gaThemeToggle) return;
  window.__gaThemeToggle = true;
  const button = () => document.getElementById("ga-theme-toggle");
  let busy = false;

  const isDark = () => {
    const app = document.querySelector(".stApp");
    if (!app) return false;
    const rgb = getComputedStyle(app).backgroundColor.match(/\d+/g).map(Number);
    return 0.5 > (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255;
  };
  const sync = () => {
    const btn = button();
    if (!btn) return;
    const dark = isDark();
    btn.dataset.mode = dark ? "dark" : "light";
    btn.title = dark ? "Switch to light theme" : "Switch to dark theme";
    btn.setAttribute("aria-label", btn.title);
  };
  const menuOpen = () => !!document.querySelector('[data-testid="stMainMenuList"]');
  const waitFor = (sel, ms) => new Promise((resolve) => {
    const t0 = Date.now();
    (function poll() {
      const el = document.querySelector(sel);
      if (el || Date.now() - t0 > ms) return resolve(el);
      requestAnimationFrame(poll);
    })();
  });

  // one delegated listener for the page, whichever button element is current
  document.addEventListener("click", async (ev) => {
    if (!ev.target.closest || !ev.target.closest("#ga-theme-toggle") || busy) return;
    const menu = document.querySelector('[data-testid="stMainMenuButton"]');
    if (!menu) return;
    busy = true;
    const target = isDark() ? "Light" : "Dark";
    document.body.classList.add("ga-theme-switching");  // keeps the menu invisible while we use it
    if (!menuOpen()) menu.click();
    const item = await waitFor('[data-testid="stMainMenuItem-theme-' + target + '"]', 1500);
    if (item) item.click();
    await new Promise((r) => setTimeout(r, 200));
    if (menuOpen()) menu.click();  // the menu button toggles it closed
    await new Promise((r) => setTimeout(r, 150));
    menu.blur();  // no leftover focus ring on the menu button
    document.body.classList.remove("ga-theme-switching");
    busy = false;
    sync();
  });

  sync();
  setInterval(sync, 1000);  // follow changes made from the menu or by the system setting
})();
