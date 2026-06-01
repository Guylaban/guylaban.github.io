/* ============================================================
   Interactions: nav, scroll progress, reveal-on-scroll,
   animated stat counters, card spotlight.
   ============================================================ */

(function () {
  "use strict";

  const nav = document.getElementById("nav");
  const navToggle = document.getElementById("navToggle");
  const navLinks = document.querySelector(".nav__links");
  const progress = document.getElementById("scrollProgress");

  /* ---- Sticky nav + scroll progress ---- */
  function onScroll() {
    const y = window.scrollY;
    if (nav) nav.classList.toggle("is-scrolled", y > 24);
    if (progress) {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.width = (h > 0 ? (y / h) * 100 : 0) + "%";
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---- Mobile menu ---- */
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => {
      const open = navLinks.classList.toggle("is-open");
      navToggle.classList.toggle("is-open", open);
      navToggle.setAttribute("aria-expanded", String(open));
    });
    navLinks.querySelectorAll("a").forEach((a) =>
      a.addEventListener("click", () => {
        navLinks.classList.remove("is-open");
        navToggle.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      })
    );
  }

  /* ---- Reveal on scroll ---- */
  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("is-visible"));
  }

  /* ---- Animated counters ---- */
  function animateCount(node) {
    const target = parseFloat(node.dataset.count || "0");
    const suffix = node.dataset.suffix || "";
    const dur = 1500;
    const start = performance.now();
    function tick(now) {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
      const val = Math.round(target * eased);
      node.textContent = val.toLocaleString() + (p === 1 ? suffix : "");
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  let countersStarted = false;
  function startCounters() {
    if (countersStarted) return;
    countersStarted = true;
    document.querySelectorAll(".stat__num[data-count]").forEach(animateCount);
  }

  const statsWrap = document.getElementById("heroStats");
  if (statsWrap && "IntersectionObserver" in window) {
    const so = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          startCounters();
          so.disconnect();
        }
      },
      { threshold: 0.4 }
    );
    so.observe(statsWrap);
  } else {
    startCounters();
  }

  // If live metadata arrives after the counters were primed, re-run with
  // the updated targets (counters only animate once, so guard it).
  document.addEventListener("publications:ready", () => {
    if (!countersStarted) startCounters();
  });

  /* ---- Card spotlight follow ---- */
  document.querySelectorAll(".card").forEach((card) => {
    card.addEventListener("pointermove", (e) => {
      const r = card.getBoundingClientRect();
      card.style.setProperty("--mx", `${e.clientX - r.left}px`);
      card.style.setProperty("--my", `${e.clientY - r.top}px`);
    });
  });

  /* ---- Footer year ---- */
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();
})();
