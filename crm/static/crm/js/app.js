const menu = document.getElementById("mobileMenu");
const overlay = document.getElementById("mobileOverlay");
const openButton = document.getElementById("openMobileMenu");
const closeButton = document.getElementById("closeMobileMenu");

function setMenuOpen(isOpen) {
  if (!menu || !overlay || !openButton) return;
  menu.classList.toggle("is-open", isOpen);
  overlay.classList.toggle("is-open", isOpen);
  menu.setAttribute("aria-hidden", String(!isOpen));
  openButton.setAttribute("aria-expanded", String(isOpen));
}

openButton?.addEventListener("click", () => setMenuOpen(true));
closeButton?.addEventListener("click", () => setMenuOpen(false));
overlay?.addEventListener("click", () => setMenuOpen(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") setMenuOpen(false);
});
