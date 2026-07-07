/* Mascot SVG — a friendly blob that reacts to swipes
   States: idle | like | pass | super | match | thinking | scraping
*/

window.MascotComponent = {
  props: {
    state: { type: String, default: "idle" },
    size: { type: Number, default: 120 },
  },
  computed: {
    blobColor() {
      switch (this.state) {
        case "like": return "#FFC2B8";
        case "pass": return "#EFE7D5";
        case "super": return "#FFD56B";
        case "match": return "#FFD56B";
        case "scraping": return "#DCE6FF";
        default: return "#FFD56B";
      }
    },
    bounceClass() {
      return `mascot-state-${this.state}`;
    },
  },
  template: `
    <svg :class="bounceClass" :width="size" :height="size" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <filter id="m-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="4" stdDeviation="0" flood-color="#1A1626" flood-opacity="1"/>
        </filter>
      </defs>

      <!-- antenna / hat varies by state -->
      <g class="m-antenna">
        <line x1="100" y1="42" x2="100" y2="22" stroke="#1A1626" stroke-width="3" stroke-linecap="round"/>
        <circle :cx="100" :cy="18" r="6" :fill="state === 'super' ? '#FF6E5A' : (state === 'like' ? '#FF6E5A' : (state === 'pass' ? '#7A86F5' : '#7A86F5'))" stroke="#1A1626" stroke-width="2.5"/>
      </g>

      <!-- body blob -->
      <path
        class="m-body"
        d="M40,110 C40,70 65,45 100,45 C135,45 160,70 160,110 C160,140 145,165 100,165 C55,165 40,140 40,110 Z"
        :fill="blobColor"
        stroke="#1A1626"
        stroke-width="3"
      />

      <!-- left arm -->
      <g class="m-arm-left" :class="state">
        <line x1="50" y1="115" x2="32" y2="138" stroke="#1A1626" stroke-width="3" stroke-linecap="round"/>
        <circle cx="30" cy="140" r="6" fill="#1A1626"/>
      </g>
      <!-- right arm -->
      <g class="m-arm-right" :class="state">
        <line x1="150" y1="115" x2="168" y2="138" stroke="#1A1626" stroke-width="3" stroke-linecap="round"/>
        <circle cx="170" cy="140" r="6" fill="#1A1626"/>
      </g>

      <!-- face -->
      <!-- idle/thinking eyes (dots) -->
      <g v-if="state === 'idle' || state === 'thinking' || state === 'scraping'" class="m-face">
        <circle cx="82" cy="98" r="6" fill="#1A1626"/>
        <circle cx="118" cy="98" r="6" fill="#1A1626"/>
        <!-- highlight -->
        <circle cx="84" cy="96" r="1.6" fill="#FFFFFF"/>
        <circle cx="120" cy="96" r="1.6" fill="#FFFFFF"/>
        <!-- mouth -->
        <path v-if="state === 'idle'" d="M88,128 Q100,138 112,128" stroke="#1A1626" stroke-width="3" stroke-linecap="round" fill="none"/>
        <path v-else-if="state === 'thinking'" d="M88,130 Q100,127 112,130" stroke="#1A1626" stroke-width="3" stroke-linecap="round" fill="none"/>
        <!-- scraping: small "o" mouth with bouncing dots -->
        <g v-else>
          <circle cx="92" cy="130" r="2.5" fill="#1A1626"/>
          <circle cx="100" cy="130" r="2.5" fill="#1A1626" class="m-dot-2"/>
          <circle cx="108" cy="130" r="2.5" fill="#1A1626" class="m-dot-3"/>
        </g>
      </g>

      <!-- LIKE: heart eyes + open smile -->
      <g v-else-if="state === 'like'" class="m-face">
        <path d="M76,94 C76,89 80,86 84,89 C88,86 92,89 92,94 C92,99 84,106 84,106 C84,106 76,99 76,94 Z" fill="#E84B36" stroke="#1A1626" stroke-width="2"/>
        <path d="M108,94 C108,89 112,86 116,89 C120,86 124,89 124,94 C124,99 116,106 116,106 C116,106 108,99 108,94 Z" fill="#E84B36" stroke="#1A1626" stroke-width="2"/>
        <path d="M84,125 Q100,142 116,125" stroke="#1A1626" stroke-width="3" stroke-linecap="round" fill="#1A1626" fill-opacity="0.15"/>
        <!-- blush -->
        <circle cx="68" cy="118" r="6" fill="#FF6E5A" opacity="0.5"/>
        <circle cx="132" cy="118" r="6" fill="#FF6E5A" opacity="0.5"/>
      </g>

      <!-- PASS: x eyes + tongue -->
      <g v-else-if="state === 'pass'" class="m-face">
        <g stroke="#1A1626" stroke-width="3" stroke-linecap="round">
          <line x1="76" y1="92" x2="88" y2="104"/>
          <line x1="88" y1="92" x2="76" y2="104"/>
          <line x1="112" y1="92" x2="124" y2="104"/>
          <line x1="124" y1="92" x2="112" y2="104"/>
        </g>
        <!-- meh mouth -->
        <path d="M86,132 Q100,124 114,132" stroke="#1A1626" stroke-width="3" stroke-linecap="round" fill="none"/>
        <path d="M104,130 L108,138 Q104,141 100,138 Z" fill="#FF6E5A" stroke="#1A1626" stroke-width="2"/>
      </g>

      <!-- SUPER: star eyes + fire mouth -->
      <g v-else-if="state === 'super'" class="m-face">
        <g class="m-star-eyes">
          <path d="M82,90 L85,98 L93,98 L86.5,103 L89,111 L82,106 L75,111 L77.5,103 L71,98 L79,98 Z" fill="#FF6E5A" stroke="#1A1626" stroke-width="1.5"/>
          <path d="M118,90 L121,98 L129,98 L122.5,103 L125,111 L118,106 L111,111 L113.5,103 L107,98 L115,98 Z" fill="#FF6E5A" stroke="#1A1626" stroke-width="1.5"/>
        </g>
        <!-- O mouth with fire -->
        <ellipse cx="100" cy="132" rx="7" ry="9" fill="#1A1626"/>
        <path class="m-fire" d="M93,140 Q90,148 95,154 Q97,148 100,152 Q103,148 105,154 Q110,148 107,140 Z" fill="#FF6E5A" stroke="#1A1626" stroke-width="2"/>
      </g>

      <!-- MATCH: bigger heart eyes + cheering arms -->
      <g v-else-if="state === 'match'" class="m-face">
        <path d="M74,92 C74,85 80,82 85,86 C90,82 96,85 96,92 C96,99 85,108 85,108 C85,108 74,99 74,92 Z" fill="#E84B36" stroke="#1A1626" stroke-width="2"/>
        <path d="M104,92 C104,85 110,82 115,86 C120,82 126,85 126,92 C126,99 115,108 115,108 C115,108 104,99 104,92 Z" fill="#E84B36" stroke="#1A1626" stroke-width="2"/>
        <path d="M82,128 Q100,148 118,128" stroke="#1A1626" stroke-width="3.5" stroke-linecap="round" fill="#1A1626" fill-opacity="0.2"/>
      </g>
    </svg>
  `,
};

/* Mascot animations via class names */
const mascotCss = `
  .mascot-state-idle .m-body { animation: m-breathe 3s ease-in-out infinite; transform-origin: center; }
  .mascot-state-like .m-body { animation: m-bounce 0.5s ease-out; transform-origin: center bottom; }
  .mascot-state-pass .m-body { animation: m-shake 0.5s ease-out; transform-origin: center bottom; }
  .mascot-state-super .m-body { animation: m-spin-up 0.6s cubic-bezier(.4,1.6,.6,1); transform-origin: center; }
  .mascot-state-match .m-body { animation: m-celebrate 0.8s ease-in-out infinite; transform-origin: center bottom; }
  .mascot-state-scraping .m-body { animation: m-breathe 0.9s ease-in-out infinite; transform-origin: center; }
  .mascot-state-thinking .m-body { animation: m-tilt 2s ease-in-out infinite; transform-origin: center bottom; }

  /* arms wave on like/match */
  .mascot-state-like .m-arm-left,
  .mascot-state-match .m-arm-left { animation: m-wave-l 0.6s ease-in-out infinite; transform-origin: 50px 115px; }
  .mascot-state-like .m-arm-right,
  .mascot-state-match .m-arm-right { animation: m-wave-r 0.6s ease-in-out infinite; transform-origin: 150px 115px; }

  /* arms drop on pass */
  .mascot-state-pass .m-arm-left,
  .mascot-state-pass .m-arm-right { animation: m-droop 0.4s ease-out forwards; transform-origin: center 115px; }

  /* star eyes pulse on super */
  .mascot-state-super .m-star-eyes { animation: m-pulse 0.5s ease-in-out infinite alternate; transform-origin: 100px 100px; }
  .mascot-state-super .m-fire { animation: m-flame 0.25s ease-in-out infinite alternate; transform-origin: 100px 150px; }

  .m-dot-2 { animation: m-dot 1s ease-in-out 0.15s infinite; }
  .m-dot-3 { animation: m-dot 1s ease-in-out 0.3s infinite; }

  @keyframes m-breathe {
    0%, 100% { transform: scale(1, 1); }
    50% { transform: scale(1.03, 0.97); }
  }
  @keyframes m-bounce {
    0% { transform: scale(1,1); }
    40% { transform: scale(1.15, 0.85) translateY(-8px); }
    70% { transform: scale(0.95, 1.05); }
    100% { transform: scale(1,1); }
  }
  @keyframes m-shake {
    0%, 100% { transform: translateX(0) rotate(0); }
    25% { transform: translateX(-6px) rotate(-3deg); }
    75% { transform: translateX(6px) rotate(3deg); }
  }
  @keyframes m-spin-up {
    0% { transform: translateY(0) rotate(0) scale(1); }
    50% { transform: translateY(-14px) rotate(8deg) scale(1.1); }
    100% { transform: translateY(0) rotate(0) scale(1); }
  }
  @keyframes m-celebrate {
    0%, 100% { transform: translateY(0) rotate(-2deg); }
    50% { transform: translateY(-6px) rotate(2deg); }
  }
  @keyframes m-tilt {
    0%, 100% { transform: rotate(-3deg); }
    50% { transform: rotate(3deg); }
  }
  @keyframes m-wave-l {
    0%, 100% { transform: rotate(0); }
    50% { transform: rotate(-30deg); }
  }
  @keyframes m-wave-r {
    0%, 100% { transform: rotate(0); }
    50% { transform: rotate(30deg); }
  }
  @keyframes m-droop {
    from { transform: translateY(0); }
    to { transform: translateY(10px); }
  }
  @keyframes m-pulse {
    from { transform: scale(1); }
    to { transform: scale(1.15); }
  }
  @keyframes m-flame {
    from { transform: scaleY(1); }
    to { transform: scaleY(1.2) translateY(2px); }
  }
  @keyframes m-dot {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-3px); }
  }
`;

// inject mascot styles
const _style = document.createElement("style");
_style.textContent = mascotCss;
document.head.appendChild(_style);
