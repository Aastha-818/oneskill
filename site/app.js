// Website demo of the router. The ranking mirrors skill/oneskill/scripts/route.py
// - keep the constants and the scoring in step with that file.
(function () {
  var registry = window.ONESKILL_REGISTRY || { skills: [], repo: "" };
  var skills = registry.skills;

  var FIELD_WEIGHTS = { name: 3.0, tags: 2.5, description: 1.0 };
  var ANCHOR_FIELDS = { name: true, tags: true };
  var K1 = 1.4, B = 0.6;
  var PRIOR_MEAN = 3.5, PRIOR_VOTES = 8, QUALITY_FLOOR = 0.5, SUPPORT_RATIO = 0.55;
  var STOPWORDS = {};
  ("a an and are as at be but by can could do for from get give have help how i " +
    "in into is it its just let like make me my need of on or our please should " +
    "so some that the their them then this to up us use want we what when which " +
    "will with would you your new good best create build").split(" ").forEach(function (w) { STOPWORDS[w] = true; });
  var SUFFIXES = ["ations", "ation", "ings", "ing", "ers", "er", "ies", "es", "ed", "s"];

  function stem(word) {
    for (var i = 0; i < SUFFIXES.length; i++) {
      var s = SUFFIXES[i];
      if (word.slice(-s.length) === s && word.length - s.length >= 3) return word.slice(0, -s.length);
    }
    return word;
  }
  function tokens(text) {
    // stemmed tokens plus the exact word when stemming changed it (mirrors route.py)
    var out = [];
    (text.toLowerCase().match(/[a-z0-9+#]+/g) || []).forEach(function (w) {
      if (w.length <= 1 || STOPWORDS[w]) return;
      var s = stem(w);
      out.push(s);
      if (s !== w) out.push(w);
    });
    return out;
  }
  function quality(rating, stars) {
    // mirrors route.py: stars nudge the prior until real votes arrive
    var prior = !stars ? PRIOR_MEAN : 3.0 + Math.min(1.5, 0.3 * Math.log10(1 + stars));
    var votes = (rating && rating.votes) || 0, sum = (rating && rating.sum) || 0;
    return (prior * PRIOR_VOTES + sum) / (PRIOR_VOTES + votes) / 5;
  }
  function starsText(n) {
    if (!n) return "";
    return n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + "k" : String(n);
  }

  var docs = skills.map(function (skill) {
    var tf = {}, anchor = {}, length = 0;
    Object.keys(FIELD_WEIGHTS).forEach(function (field) {
      var value = skill[field] || "";
      if (Array.isArray(value)) value = value.join(" ");
      tokens(value.replace(/-/g, " ")).forEach(function (tok) {
        tf[tok] = (tf[tok] || 0) + FIELD_WEIGHTS[field];
        length += FIELD_WEIGHTS[field];
        if (ANCHOR_FIELDS[field]) anchor[tok] = true;
      });
    });
    return { tf: tf, anchor: anchor, length: length };
  });
  var n = docs.length;
  var avgLen = docs.reduce(function (a, d) { return a + d.length; }, 0) / Math.max(n, 1);
  var df = {};
  docs.forEach(function (d) { Object.keys(d.tf).forEach(function (t) { df[t] = (df[t] || 0) + 1; }); });

  function route(query) {
    var q = tokens(query).filter(function (t, i, all) { return all.indexOf(t) === i; });
    var results = [];
    skills.forEach(function (skill, i) {
      var d = docs[i], relevance = 0, matched = [], anchors = 0;
      q.forEach(function (tok) {
        var f = d.tf[tok];
        if (!f) return;
        var idf = Math.log(1 + (n - df[tok] + 0.5) / (df[tok] + 0.5));
        relevance += idf * f * (K1 + 1) / (f + K1 * (1 - B + B * d.length / avgLen));
        matched.push(tok);
        if (d.anchor[tok]) anchors++;
      });
      if (!matched.length) return;
      var score = relevance * (QUALITY_FLOOR + (1 - QUALITY_FLOOR) * quality(skill.rating, skill.stars));
      if ((skill.kind || "skill") === "skill") score *= 1.1; // SKILL_BONUS in route.py
      var first = tokens(skill.id.replace(/-/g, " "))[0];
      if (first && q.indexOf(first) >= 0) score *= 1.3; // NAME_BONUS in route.py
      results.push({ skill: skill, score: score, matched: matched, anchors: anchors });
    });
    results.sort(function (a, b) { return b.score - a.score || (a.skill.id < b.skill.id ? -1 : 1); });
    if (!results.length || !results[0].anchors) return { match: "none", picks: [] };
    var picks = [results[0]];
    if (results[1] && results[1].score >= SUPPORT_RATIO * results[0].score) picks.push(results[1]);
    return { match: results[0].anchors >= 2 ? "strong" : "weak", picks: picks };
  }
  window.oneskillRoute = route; // exposed so the parity check can call it

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }
  function ratingText(rating) {
    var votes = (rating && rating.votes) || 0;
    if (!votes) return "unrated";
    return (rating.sum / votes).toFixed(1) + " / 5 · " + votes + (votes === 1 ? " vote" : " votes");
  }
  var ACRONYMS = { ui: "UI", api: "API", sql: "SQL", seo: "SEO", prd: "PRD", linkedin: "LinkedIn", ai: "AI", seo: "SEO", pdf: "PDF", docx: "Word (docx)", pptx: "PowerPoint (pptx)", ffmpeg: "FFmpeg", b2b: "B2B", tdd: "TDD" };
  function title(id) {
    var words = id.split("-").map(function (w) { return ACRONYMS[w] || w; });
    words[0] = words[0].charAt(0).toUpperCase() + words[0].slice(1);
    return words.join(" ");
  }

  // hero router
  var input = document.getElementById("task");
  var pulled = document.getElementById("pulled");
  var verdict = document.getElementById("verdict");
  var VERDICTS = {
    strong: "Strong match — Claude follows this skill",
    weak: "Weak match — Claude checks the skill fits before using it",
    none: "No match — Claude does the task without a skill"
  };

  function render(query) {
    pulled.textContent = "";
    if (!query.trim()) {
      verdict.textContent = "";
      pulled.appendChild(el("p", "empty", "Type a task and the catalog pulls the cards it would hand to Claude."));
      return;
    }
    var out = route(query);
    verdict.textContent = VERDICTS[out.match];
    if (!out.picks.length) {
      pulled.appendChild(el("p", "empty", "Nothing on the shelf fits this. Routing only helps when a skill is really about the task, so the router stays out of the way."));
      return;
    }
    out.picks.forEach(function (pick, i) {
      var card = el("article", "cardx in");
      var head = el("header");
      head.appendChild(el("span", "label role " + (i ? "supporting" : "primary"), i ? "Supporting" : "Primary"));
      head.appendChild(el("span", "label", pick.skill.category + (pick.skill.kind === "resource" ? " · repository" : "")));
      card.appendChild(head);
      card.appendChild(el("h3", null, title(pick.skill.id)));
      card.appendChild(el("p", null, pick.skill.description));
      if (pick.skill.source === "github") {
        var src = el("p", "src");
        src.appendChild(el("span", "label", "On GitHub "));
        var a = el("a", null, pick.skill.repo);
        a.href = pick.skill.url; a.target = "_blank"; a.rel = "noopener";
        src.appendChild(a);
        if (pick.skill.stars) src.appendChild(el("span", "label", "  " + starsText(pick.skill.stars) + " stars"));
        card.appendChild(src);
      }
      var dl = el("dl");
      [["Score", pick.score.toFixed(2)], ["Rating", ratingText(pick.skill.rating)], ["Matched", pick.matched.join(", ")]].forEach(function (row) {
        var wrap = el("div");
        wrap.appendChild(el("dt", "label", row[0]));
        wrap.appendChild(el("dd", "num", row[1]));
        dl.appendChild(wrap);
      });
      card.appendChild(dl);
      pulled.appendChild(card);
      setTimeout(function () { card.classList.remove("in"); }, 30 + i * 90);
    });
  }
  input.addEventListener("input", function () { render(input.value); });
  Array.prototype.forEach.call(document.querySelectorAll(".tries button"), function (button) {
    button.addEventListener("click", function () { input.value = button.textContent; render(input.value); });
  });
  input.value = "design a landing page for my app";
  render(input.value);

  // catalog table
  var rows = document.getElementById("rows");
  var filters = document.getElementById("filters");
  var ordered = skills.slice().sort(function (a, b) {
    return quality(b.rating, b.stars) - quality(a.rating, a.stars) || (a.id < b.id ? -1 : 1);
  });
  var categories = ordered.map(function (s) { return s.category; })
    .filter(function (c, i, all) { return all.indexOf(c) === i; }).sort();

  var search = document.getElementById("search");
  var current = "";
  function draw(category) {
    current = category;
    rows.textContent = "";
    var q = search.value.trim().toLowerCase();
    var shown = ordered.filter(function (s) {
      if (category && s.category !== category) return false;
      if (!q) return true;
      return (s.id + " " + s.description + " " + s.tags.join(" ") + " " + (s.repo || "")).toLowerCase().indexOf(q) >= 0;
    });
    document.getElementById("shown").textContent = shown.length === skills.length ? "" : shown.length + " shown";
    shown.slice(0, 400).forEach(function (skill, i) {
      var tr = el("tr");
      tr.appendChild(el("td", "label num", String(i + 1).padStart(2, "0")));
      tr.appendChild(el("td", "name", title(skill.id)));
      tr.appendChild(el("td", "label", skill.category + (skill.kind === "resource" ? " · repo" : "")));
      tr.appendChild(el("td", "desc", skill.description.split(". ")[0].replace(/\.$/, "") + "."));
      var where = el("td", "where");
      if (skill.source === "github") {
        var link = el("a", null, skill.repo);
        link.href = skill.url; link.target = "_blank"; link.rel = "noopener";
        where.appendChild(link);
      } else {
        where.appendChild(el("span", "label", "built in"));
      }
      tr.appendChild(where);
      tr.appendChild(el("td", "rate num", (skill.stars ? starsText(skill.stars) + " stars · " : "") + ratingText(skill.rating)));
      rows.appendChild(tr);
    });
    if (shown.length > 400) {
      var more = el("tr"); var td = el("td", "label", "Showing the first 400 of " + shown.length + " - narrow it down with the search box."); td.colSpan = 6; more.appendChild(td); rows.appendChild(more);
    }
    Array.prototype.forEach.call(filters.children, function (b) {
      b.setAttribute("aria-pressed", String((b.dataset.cat || "") === (category || "")));
    });
  }
  [""].concat(categories).forEach(function (cat) {
    var button = el("button", null, cat || "All");
    button.dataset.cat = cat;
    button.addEventListener("click", function () { draw(cat); });
    filters.appendChild(button);
  });
  search.addEventListener("input", function () { draw(current); });
  draw("");

  document.getElementById("count").textContent = skills.length;
  document.getElementById("fcount").textContent = skills.length;
  var linked = skills.filter(function (s) { return s.source === "github"; }).length;
  document.getElementById("linked").textContent = linked;
  document.getElementById("repos").textContent = skills.reduce(function (set, s) {
    if (s.repo && set.indexOf(s.repo) < 0) set.push(s.repo); return set;
  }, []).length;

  // GitHub links appear only once the repository is configured
  if (registry.repo) {
    Array.prototype.forEach.call(document.querySelectorAll("[data-repo]"), function (a) {
      a.href = "https://github.com/" + registry.repo;
      a.hidden = false;
    });
    document.querySelector("[data-repo-block]").hidden = false;
  }

  var clock = document.getElementById("clock");
  function tick() {
    clock.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + " your time";
  }
  tick();
  setInterval(tick, 30000);
})();
