/* ============================================================
   Publications loader + interactive filtering / search / sort
   Reads data/publications.json (kept up to date by the
   automated Google Scholar pipeline) and renders each paper
   with its journal / conference logo.
   ============================================================ */

(function () {
  "use strict";

  const LOGO_BASE = "assets/logos/";
  const TYPE_GROUPS = {
    journal: ["journal"],
    conference: ["conference"],
    preprint: ["preprint", "report", "thesis", "article"],
  };

  const state = { all: [], filter: "all", query: "", sort: "year" };

  const els = {
    list: document.getElementById("pubList"),
    count: document.getElementById("pubCount"),
    search: document.getElementById("pubSearch"),
    filters: document.getElementById("pubFilters"),
    sort: document.getElementById("pubSort"),
    updated: document.getElementById("lastUpdated"),
    marquee: document.getElementById("marqueeTrack"),
    heroStats: document.getElementById("heroStats"),
  };

  function escapeHtml(str) {
    return String(str || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function matchesFilter(pub) {
    if (state.filter === "all") return true;
    const group = TYPE_GROUPS[state.filter] || [state.filter];
    return group.includes(pub.type);
  }

  function matchesQuery(pub) {
    if (!state.query) return true;
    const q = state.query.toLowerCase();
    return (
      pub.title.toLowerCase().includes(q) ||
      (pub.authors || "").toLowerCase().includes(q) ||
      (pub.venue || "").toLowerCase().includes(q)
    );
  }

  function sortPubs(list) {
    const arr = list.slice();
    if (state.sort === "citations") {
      arr.sort((a, b) => (b.citations || 0) - (a.citations || 0));
    } else {
      arr.sort((a, b) => (b.year || 0) - (a.year || 0) || (b.citations || 0) - (a.citations || 0));
    }
    return arr;
  }

  function pubItemHTML(pub, idx) {
    const logo = LOGO_BASE + (pub.logo || "default") + ".svg";
    const cites = pub.citations || 0;
    const link = pub.url || "#";
    return `
      <li class="pub-item" style="animation-delay:${Math.min(idx * 40, 400)}ms">
        <span class="pub-logo">
          <img src="${logo}" alt="${escapeHtml(pub.venue)} logo" loading="lazy"
               onerror="this.onerror=null;this.src='${LOGO_BASE}default.svg'">
        </span>
        <div class="pub-body">
          <a class="pub-title" href="${escapeHtml(link)}" target="_blank" rel="noopener">${escapeHtml(pub.title)}</a>
          <div class="pub-meta">
            <span class="pub-authors">${escapeHtml(pub.authors)}</span>
            <span class="pub-venue">${escapeHtml(pub.venue)} · ${pub.year || ""}</span>
            <span class="pub-type-tag">${escapeHtml(pub.type)}</span>
          </div>
        </div>
        <span class="pub-cites" title="${cites} citations">
          <b>${cites}</b><span>cites</span>
        </span>
      </li>`;
  }

  function render() {
    let list = state.all.filter((p) => matchesFilter(p) && matchesQuery(p));
    list = sortPubs(list);

    if (!list.length) {
      els.list.innerHTML = `<li class="pub-empty">No publications match your search.</li>`;
    } else {
      els.list.innerHTML = list.map(pubItemHTML).join("");
    }
    if (els.count) {
      els.count.textContent = `Showing ${list.length} of ${state.all.length} publications`;
    }
  }

  function buildMarquee(interests) {
    if (!els.marquee || !interests || !interests.length) return;
    const items = interests
      .map((t) => `<span class="marquee__item">${escapeHtml(t)}</span>`)
      .join("");
    // duplicate the track so the infinite scroll loops seamlessly
    els.marquee.innerHTML = items + items;
  }

  function applyMeta(meta) {
    if (!meta) return;
    if (els.updated && meta.last_updated) {
      els.updated.textContent = `Last updated ${meta.last_updated}.`;
    }
    // Sync hero stat targets with live metadata where available.
    const map = {
      "1838": meta.total_citations,
      "19": meta.h_index,
      "29": meta.i10_index,
    };
    if (els.heroStats) {
      els.heroStats.querySelectorAll("[data-count]").forEach((node) => {
        const label = (node.nextElementSibling && node.nextElementSibling.textContent || "").toLowerCase();
        if (label.includes("citation") && meta.total_citations) node.dataset.count = meta.total_citations;
        if (label.includes("h-index") && meta.h_index) node.dataset.count = meta.h_index;
        if (label.includes("i10") && meta.i10_index) node.dataset.count = meta.i10_index;
        if (label.includes("publication")) node.dataset.count = state.all.length;
      });
    }
  }

  function wireControls() {
    if (els.search) {
      els.search.addEventListener("input", (e) => {
        state.query = e.target.value.trim();
        render();
      });
    }
    if (els.filters) {
      els.filters.addEventListener("click", (e) => {
        const btn = e.target.closest(".chip");
        if (!btn) return;
        els.filters.querySelectorAll(".chip").forEach((c) => c.classList.remove("is-active"));
        btn.classList.add("is-active");
        state.filter = btn.dataset.filter;
        render();
      });
    }
    if (els.sort) {
      els.sort.addEventListener("change", (e) => {
        state.sort = e.target.value;
        render();
      });
    }
  }

  async function load() {
    try {
      const res = await fetch("data/publications.json", { cache: "no-cache" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      state.all = Array.isArray(data.publications) ? data.publications : [];
      buildMarquee((data.metadata && data.metadata.interests) || []);
      applyMeta(data.metadata);
      render();
      // Let main.js know data + stats are ready (so counters use live numbers).
      document.dispatchEvent(new CustomEvent("publications:ready", { detail: data }));
    } catch (err) {
      console.error("Failed to load publications:", err);
      els.list.innerHTML = `<li class="pub-empty">Couldn't load publications right now. Please try again later.</li>`;
    }
  }

  wireControls();
  load();
})();
