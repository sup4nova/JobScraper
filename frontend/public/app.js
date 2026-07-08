/* JobSwipe — Vue 3 main app
   POST /api/scrape   → scrape jobs (Indeed, LinkedIn, Wellfound, RemoteOK)
   POST /api/likes    → save liked jobs
*/

const { createApp, ref, reactive, computed, watch, nextTick, onMounted } = Vue;

// ─────────────── Persistence (localStorage) ───────────────

const LS = {
  swipes:  "jobswipe_swipes",
  profile: "jobswipe_profile",
  jobs:    "jobswipe_jobs",
};

function lsSave(key, val) {
  try {
    localStorage.setItem(key, JSON.stringify(val));
  } catch (e) {
    console.warn("[JobSwipe] localStorage unavailable:", e.name);
  }
}
function lsLoad(key, fallback) {
  try {
    const r = localStorage.getItem(key);
    return r ? JSON.parse(r) : fallback;
  } catch (e) {
    console.warn("[JobSwipe] localStorage unreadable:", e.name);
    return fallback;
  }
}

// ─────────────── API base ───────────────
// Docker/nginx proxies /api/ to the backend container (same origin), so a
// relative path works there. Opening index.html directly (file://) has no
// server to proxy through, so fall back to the local FastAPI dev server.
const API_BASE = location.protocol === "file:" ? "http://localhost:8000" : "";

// ─────────────── App ───────────────

const App = {
  setup() {

    // ── State ──────────────────────────────────────────────
    const scene        = ref("hero"); // hero | onboarding | scraping | swipe | stats
    const mascotState  = ref("idle");
    const showMatchModal = ref(false);
    const matchedJob   = ref(null);
    const confettiPieces = ref([]);

    const tweaks = reactive(/*EDITMODE-BEGIN*/{
      "theme":       "coral",
      "mascot_size": 76,
      "show_score":  true,
    }/*EDITMODE-END*/);
    const showTweaks = ref(false);

    const profile = reactive({
      poste:       "",
      ville:       "",
      rayon:       30,
      remote:      ["hybrid"],
      contrats:    ["Permanent"],
      salaryMin:   45,
      salaryMax:   75,
      experience:  "3-5",
      langues:     ["French"],
      companySize: ["scale-up"],
      name:        "",
      email:       "",
      competences: "",
    });

    const onbStep    = ref(0);
    const totalSteps = 8;
    const scroller   = ref(null);

    // ── Chat state ─────────────────────────────────────────
    const chatOpen     = ref(false);
    const chatInput    = ref("");
    const chatLoading  = ref(false);
    const chatScroller = ref(null);
    const chatMessages = ref([
      { role: "bot", text: "Hey! I'm **JobBot** 👋\nOnce your jobs are scraped, I can generate a cover letter, analyze how well your profile matches an offer, or translate the letter." },
    ]);

    const scrapeProgress = ref(0);
    const scrapeStatus   = ref("");
    const scrapeSources  = reactive([
      { id: "indeed",    label: "Indeed",    state: "pending", count: 0 },
      { id: "linkedin",  label: "LinkedIn",  state: "pending", count: 0 },
      { id: "wellfound", label: "Wellfound", state: "pending", count: 0 },
      { id: "remoteok",  label: "RemoteOK",  state: "pending", count: 0 },
    ]);

    const jobs    = ref([]);
    const cardIdx = ref(0);
    const swipes  = ref([]);

    // ── Computed ───────────────────────────────────────────
    const progressPct   = computed(() => Math.round(((onbStep.value + 1) / totalSteps) * 100));
    const visibleCards  = computed(() => jobs.value.slice(cardIdx.value, cardIdx.value + 3));
    const liked         = computed(() => swipes.value.filter(s => s.action === "like" || s.action === "super"));
    const passed        = computed(() => swipes.value.filter(s => s.action === "pass"));
    const superLiked    = computed(() => swipes.value.filter(s => s.action === "super"));
    const matchPct      = computed(() => {
      if (swipes.value.length === 0) return 0;
      return Math.round((liked.value.length / swipes.value.length) * 100);
    });

    const sourceBreakdown = computed(() => {
      const counts = { indeed: 0, linkedin: 0, wellfound: 0, remoteok: 0 };
      liked.value.forEach(s => { counts[s.job.source] = (counts[s.job.source] || 0) + 1; });
      const total = liked.value.length || 1;
      return Object.entries(counts).map(([id, c]) => ({
        id,
        label: window.SOURCE_LABELS[id],
        count: c,
        pct:   Math.round((c / total) * 100),
        color: id === "indeed" ? "#8FD4A9" : id === "linkedin" ? "#7A86F5" : id === "wellfound" ? "#F2B82E" : id === "remoteok" ? "#52B57A" : "#8FD4A9",
      }));
    });

    const topMatches = computed(() =>
      [...liked.value]
        .sort((a, b) => (b.job.yourScore || 0) - (a.job.yourScore || 0))
        .slice(0, 5)
    );

    // ── Onboarding ─────────────────────────────────────────
    function startOnboarding() {
      mascotState.value = "thinking";
      scene.value       = "onboarding";
      onbStep.value     = 0;
    }

    function setOnbStep(i) {
      onbStep.value = Math.max(0, Math.min(totalSteps - 1, i));
      nextTick(() => {
        const el = scroller.value?.children[onbStep.value];
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }

    function nextOnb() {
      if (onbStep.value < totalSteps - 1) setOnbStep(onbStep.value + 1);
      else startScraping();
    }
    function prevOnb() {
      if (onbStep.value > 0) setOnbStep(onbStep.value - 1);
    }

    function toggleArr(arr, val, single = false) {
      const i = arr.indexOf(val);
      if (i >= 0) {
        if (!single) arr.splice(i, 1);
      } else {
        if (single) arr.splice(0, arr.length);
        arr.push(val);
      }
    }

    // ── Sync profile → backend ──────────────────────────────
    async function syncProfileToBackend() {
      const profil = {
        name:          profile.name,
        title:         profile.poste,
        email:         profile.email,
        phone:         "",
        location:      profile.ville,
        github:        "",
        summary:       `Looking for a ${profile.poste || "?"} position (${(profile.remote || []).join(", ") || "?"}) — contracts: ${(profile.contrats || []).join(", ")}.`,
        skills:        profile.competences,
        experience:    profile.experience,
        education_text: "",
      };
      try {
        await fetch(`${API_BASE}/api/profile`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify(profil),
        });
      } catch (e) {
        console.error("Profile sync error:", e);
      }
    }

    // ── Scraping ───────────────────────────────────────────
    async function startScraping() {
      await syncProfileToBackend();
      scene.value         = "scraping";
      mascotState.value   = "scraping";
      scrapeProgress.value = 10;
      scrapeStatus.value  = "Launching scrape...";

      try {
        const res = await fetch(`${API_BASE}/api/scrape`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify({
            poste:  profile.poste,
            ville:  profile.ville,
            limite: 20,
          }),
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data      = await res.json();
        const freshJobs = data.jobs ?? [];
        console.log(`>>> ${freshJobs.length} jobs received`, freshJobs[0]);

        // Merge with local history (dedup by URL)
        const stored     = lsLoad(LS.jobs, []);
        const storedUrls = new Set(stored.map(j => j.url));
        const merged     = [...stored];
        for (const j of freshJobs) {
          if (!storedUrls.has(j.url)) merged.push(j);
        }
        lsSave(LS.jobs, merged);

        // Only show jobs not yet swiped
        const swipedUrls = new Set(swipes.value.map(s => s.job.url));
        jobs.value       = merged.filter(j => !swipedUrls.has(j.url));
        scrapeStatus.value = `${jobs.value.length} jobs to discover!`;

      } catch (e) {
        console.error(e);
        scrapeStatus.value = "Backend connection error.";
        return;
      }

      scrapeProgress.value = 100;
      cardIdx.value        = 0;
      mascotState.value    = "idle";
      scene.value          = "swipe";
    }

    // ── Swipe ──────────────────────────────────────────────
    const dragState = reactive({
      active: false,
      x: 0, y: 0,
      startX: 0, startY: 0,
      stamp: null,
    });

    const SWIPE_THRESHOLD = 90;
    const SUPER_THRESHOLD = -110;

    function onPointerDown(e, idx) {
      if (idx !== cardIdx.value) return;
      dragState.active = true;
      const p = e.touches ? e.touches[0] : e;
      dragState.startX = p.clientX;
      dragState.startY = p.clientY;
      dragState.x      = 0;
      dragState.y      = 0;
      dragState.stamp  = null;
    }

    function onPointerMove(e) {
      if (!dragState.active) return;
      const p = e.touches ? e.touches[0] : e;
      dragState.x = p.clientX - dragState.startX;
      dragState.y = p.clientY - dragState.startY;

      const ax = Math.abs(dragState.x);
      const ay = Math.abs(dragState.y);
      if (dragState.y < -50 && ay > ax)  { dragState.stamp = "up";    mascotState.value = "super"; }
      else if (dragState.x > 30)          { dragState.stamp = "right"; mascotState.value = "like"; }
      else if (dragState.x < -30)         { dragState.stamp = "left";  mascotState.value = "pass"; }
      else                                { dragState.stamp = null;    mascotState.value = "thinking"; }
    }

    function onPointerUp() {
      if (!dragState.active) return;
      const { x, y } = dragState;
      dragState.active = false;

      if      (y < SUPER_THRESHOLD)  commitSwipe("super");
      else if (x > SWIPE_THRESHOLD)  commitSwipe("like");
      else if (x < -SWIPE_THRESHOLD) commitSwipe("pass");
      else {
        dragState.x = 0; dragState.y = 0; dragState.stamp = null;
        mascotState.value = "idle";
      }
    }

    async function commitSwipe(action) {
      const job = jobs.value[cardIdx.value];
      if (!job) return;

      if (action === "like")  { dragState.x =  600; dragState.y =    0; }
      if (action === "pass")  { dragState.x = -600; dragState.y =    0; }
      if (action === "super") { dragState.x =    0; dragState.y = -800; }

      mascotState.value = action === "pass" ? "pass" : action === "super" ? "super" : "like";
      swipes.value.push({ job, action });

      if (action === "like" || action === "super") {
        try {
          await fetch(`${API_BASE}/api/likes`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ jobs: [job] }),
          });
        } catch (e) {
          console.error("Error saving like:", e);
        }
      }

      setTimeout(() => {
        cardIdx.value++;
        dragState.x = 0; dragState.y = 0; dragState.stamp = null;

        if (action === "super") {
          showMatch(job);
        } else if (action === "like" && Math.random() < 0.25) {
          showMatch(job);
        } else {
          setTimeout(() => { mascotState.value = "idle"; }, 600);
        }
      }, 320);
    }

    function actionButton(action) { commitSwipe(action); }

    function showMatch(job) {
      matchedJob.value     = job;
      showMatchModal.value = true;
      mascotState.value    = "match";
      const colors = ["#FF6E5A", "#FFD56B", "#7A86F5", "#8FD4A9", "#FFC2B8"];
      confettiPieces.value = Array.from({ length: 40 }, (_, i) => ({
        left:   Math.random() * 100 + "%",
        color:  colors[i % colors.length],
        delay:  (Math.random() * 0.4) + "s",
        rotate: (Math.random() * 360) + "deg",
      }));
      setTimeout(() => { confettiPieces.value = []; }, 1800);
    }

    function closeMatch() {
      showMatchModal.value = false;
      mascotState.value    = "idle";
    }

    // ── Navigation ─────────────────────────────────────────
    function goStats() {
      mascotState.value = "thinking";
      scene.value       = "stats";
    }
    function backToSwipe() {
      scene.value       = jobs.value.length === 0 ? "hero" : "swipe";
      mascotState.value = "idle";
    }
    function restartScrape() { startScraping(); }
    function editProfile() {
      scene.value       = "onboarding";
      onbStep.value     = 0;
      mascotState.value = "thinking";
    }
    function clearHistory() {
      swipes.value = [];
      localStorage.removeItem(LS.swipes);
      const allJobs = lsLoad(LS.jobs, []);
      if (allJobs.length > 0) {
        jobs.value    = allJobs;
        cardIdx.value = 0;
        scene.value   = "swipe";
      }
    }

    // ── Card helpers ───────────────────────────────────────
    function cardTransform(idx) {
      const offset = idx - cardIdx.value;
      if (offset === 0 && (dragState.active || Math.abs(dragState.x) > 100 || Math.abs(dragState.y) > 100)) {
        return `translate(${dragState.x}px, ${dragState.y}px) rotate(${dragState.x * 0.06}deg)`;
      }
      return `translate(0, ${offset * 12}px) scale(${1 - offset * 0.04})`;
    }
    function cardZ(idx) { return 100 - (idx - cardIdx.value); }
    function stampOpacity(stampName) {
      if (!dragState.active && Math.abs(dragState.x) < 100 && Math.abs(dragState.y) < 100) return 0;
      if (stampName === "right" && dragState.x > 0) return Math.min(1,  dragState.x / 100);
      if (stampName === "left"  && dragState.x < 0) return Math.min(1, -dragState.x / 100);
      if (stampName === "up"    && dragState.y < 0) return Math.min(1, -dragState.y / 100);
      return 0;
    }

    // ── Tweaks ─────────────────────────────────────────────
    const themeStyles = {
      coral:  { primary: "#FF6E5A", primaryDeep: "#E84B36" },
      peri:   { primary: "#7A86F5", primaryDeep: "#4858DC" },
      mint:   { primary: "#52B57A", primaryDeep: "#2E8B58" },
      butter: { primary: "#F2B82E", primaryDeep: "#C8941A" },
    };

    function applyTheme(t) {
      const s = themeStyles[t];
      if (!s) return;
      document.documentElement.style.setProperty("--coral",      s.primary);
      document.documentElement.style.setProperty("--coral-deep", s.primaryDeep);
    }
    function persistTweaks() {
      try {
        window.parent.postMessage({
          type:  "__edit_mode_set_keys",
          edits: JSON.parse(JSON.stringify(tweaks)),
        }, "*");
      } catch (_) {}
    }
    function closeTweaks() {
      showTweaks.value = false;
      try { window.parent.postMessage({ type: "__edit_mode_dismissed" }, "*"); } catch (_) {}
    }

    // ── Watchers ───────────────────────────────────────────
    watch(swipes,  val => lsSave(LS.swipes,  val),         { deep: true });
    watch(profile, val => lsSave(LS.profile, { ...val }),  { deep: true });
    watch(() => tweaks.theme,      t => { applyTheme(t); persistTweaks(); });
    watch(() => tweaks.show_score, persistTweaks);
    watch(() => tweaks.mascot_size, persistTweaks);

    // ── Mounted ────────────────────────────────────────────
    onMounted(() => {
      // Mouse / touch events
      window.addEventListener("mousemove", onPointerMove);
      window.addEventListener("mouseup",   onPointerUp);
      window.addEventListener("touchmove", onPointerMove, { passive: false });
      window.addEventListener("touchend",  onPointerUp);

      // Theme + edit mode
      applyTheme(tweaks.theme);
      window.addEventListener("message", e => {
        if (e.data?.type === "__activate_edit_mode")   showTweaks.value = true;
        if (e.data?.type === "__deactivate_edit_mode") showTweaks.value = false;
      });
      try { window.parent.postMessage({ type: "__edit_mode_available" }, "*"); } catch (_) {}

      // Restore persisted state
      const savedSwipes  = lsLoad(LS.swipes,  []);
      const savedProfile = lsLoad(LS.profile,  null);
      const savedJobs    = lsLoad(LS.jobs,     []);

      if (savedSwipes.length > 0)  swipes.value = savedSwipes;
      if (savedProfile)            Object.assign(profile, savedProfile);

      if (savedJobs.length > 0) {
        const swipedUrls = new Set(swipes.value.map(s => s.job.url));
        const unseen     = savedJobs.filter(j => !swipedUrls.has(j.url));
        if (unseen.length > 0) {
          jobs.value    = unseen;
          cardIdx.value = 0;
          scene.value   = "swipe";
        }
      }
    });

    // ── Return ─────────────────────────────────────────────
    return {
      scene, mascotState, profile, onbStep, totalSteps, progressPct, scroller,
      scrapeProgress, scrapeStatus, scrapeSources,
      jobs, cardIdx, swipes, visibleCards, liked, passed, superLiked, matchPct,
      sourceBreakdown, topMatches,
      dragState, cardTransform, cardZ, stampOpacity,
      onPointerDown, onPointerUp, actionButton, toggleArr,
      startOnboarding, nextOnb, prevOnb, setOnbStep,
      goStats, backToSwipe, restartScrape, editProfile, clearHistory,
      showMatchModal, matchedJob, closeMatch, confettiPieces,
      tweaks, showTweaks, closeTweaks,
      chatOpen, chatInput, chatLoading, chatScroller, chatMessages,
      sourceLabels: window.SOURCE_LABELS,
    };
  },

  // ── Methods ────────────────────────────────────────────
  methods: {
    async sendChat() {
      const text = this.chatInput.trim();
      if (!text || this.chatLoading) return;
      this.chatMessages.push({ role: "user", text });
      this.chatInput   = "";
      this.chatLoading = true;
      await this.$nextTick();
      if (this.chatScroller) this.chatScroller.scrollTop = this.chatScroller.scrollHeight;
      try {
        const res = await fetch(`${API_BASE}/api/chat`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify({ message: text }),
        });
        if (!res.ok) throw new Error(`Error ${res.status}`);
        const data = await res.json();
        this.chatMessages.push({ role: "bot", text: data.reply });
      } catch (e) {
        this.chatMessages.push({ role: "bot", text: `⚠️ ${e.message}` });
      } finally {
        this.chatLoading = false;
        await this.$nextTick();
        if (this.chatScroller) this.chatScroller.scrollTop = this.chatScroller.scrollHeight;
      }
    },

    renderChatText(text) {
      return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\*\*([^*]+)\*\*/g, (_, p1) => `<strong>${p1}</strong>`)
        .replace(/\n/g, "<br>");
    },

    companyInitials(name) {
      if (!name) return "?";
      const parts = name.split(/\s+/);
      return parts.length === 1
        ? parts[0].slice(0, 2).toUpperCase()
        : (parts[0][0] + parts[1][0]).toUpperCase();
    },
    companyColor(name) {
      return window.COMPANY_COLORS[name] || "#1A1626";
    },
    formatDescription(desc) {
      if (!desc) return "";
      const lines = desc.split("\n").filter(l => l.trim());
      let out = "", inList = false;
      for (const l of lines) {
        if (l.trim().startsWith("•")) {
          if (!inList) { out += "<ul>"; inList = true; }
          out += `<li>${l.replace(/^•\s*/, "")}</li>`;
        } else {
          if (inList) { out += "</ul>"; inList = false; }
          out += `<p>${l}</p>`;
        }
      }
      if (inList) out += "</ul>";
      return out;
    },
    scoreClass(score) {
      if (score >= 80) return "";
      if (score >= 65) return "medium";
      return "low";
    },
  },
};

createApp(App).mount("#app");