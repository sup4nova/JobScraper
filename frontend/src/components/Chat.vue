<script setup>
import { ref, nextTick } from 'vue'

const props = defineProps({
  apiUrl: { type: String, default: '/api/chat' },
})

const emit = defineEmits(['profile-ready'])

const messages = ref([
  { role: 'bot', text: 'Salut ! Je suis **JobBot** 👋\nDis-moi quel poste tu cherches et je scrape les offres pour toi.' }
])
const input    = ref('')
const loading  = ref(false)
const scroller = ref(null)

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', text })
  input.value = ''
  loading.value = true
  await scrollBottom()

  try {
    const res = await fetch(props.apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        history: messages.value.map(m => ({ role: m.role === 'bot' ? 'assistant' : 'user', content: m.text })),
      }),
    })

    if (!res.ok) throw new Error(`Erreur ${res.status}`)
    const data = await res.json()

    messages.value.push({ role: 'bot', text: data.reply })

    if (data.profile) emit('profile-ready', data.profile)
  } catch (e) {
    messages.value.push({ role: 'bot', text: `⚠️ ${e.message}` })
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

async function scrollBottom() {
  await nextTick()
  if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

// Render **bold** and line breaks
function renderText(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}
</script>

<template>
  <div class="chat-wrap">
    <!-- Header -->
    <header class="chat-header">
      <div class="header-dot"></div>
      <span class="header-title">JobBot</span>
      <span class="header-sub">assistant IA · 100% local</span>
    </header>

    <!-- Messages -->
    <div class="messages" ref="scroller">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['bubble-row', msg.role]"
      >
        <div class="bubble" v-html="renderText(msg.text)"></div>
      </div>

      <!-- Typing indicator -->
      <div v-if="loading" class="bubble-row bot">
        <div class="bubble typing">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <!-- Input -->
    <footer class="chat-footer">
      <textarea
        v-model="input"
        @keydown="onKeydown"
        placeholder="Ex : Scrape des offres data scientist remote…"
        rows="1"
        :disabled="loading"
      ></textarea>
      <button @click="send" :disabled="loading || !input.trim()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
    </footer>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=DM+Sans:wght@400;500;600&display=swap');

.chat-wrap {
  width: 100%;
  max-width: 680px;
  height: 82vh;
  min-height: 480px;
  display: flex;
  flex-direction: column;
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(18px);
  border-radius: 24px;
  border: 1px solid rgba(26,22,38,0.08);
  box-shadow: 0 8px 40px rgba(26,22,38,0.10), 0 1.5px 0 rgba(255,255,255,0.9) inset;
  overflow: hidden;
  font-family: 'DM Sans', system-ui, sans-serif;
}

/* ── Header ── */
.chat-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 24px;
  border-bottom: 1px solid rgba(26,22,38,0.07);
  background: rgba(255,255,255,0.55);
  flex-shrink: 0;
}
.header-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: #7A86F5;
  box-shadow: 0 0 0 3px rgba(122,134,245,0.2);
}
.header-title {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 15px;
  color: #1A1626;
}
.header-sub {
  font-size: 12px;
  color: #9490A8;
  margin-left: 2px;
}

/* ── Messages ── */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 20px 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scrollbar-width: thin;
  scrollbar-color: rgba(26,22,38,0.12) transparent;
}

.bubble-row {
  display: flex;
}
.bubble-row.user { justify-content: flex-end; }
.bubble-row.bot  { justify-content: flex-start; }

.bubble {
  max-width: 78%;
  padding: 11px 16px;
  border-radius: 18px;
  font-size: 14.5px;
  line-height: 1.55;
  word-break: break-word;
}
.bot .bubble {
  background: #F1EFF8;
  color: #1A1626;
  border-bottom-left-radius: 5px;
}
.user .bubble {
  background: #1A1626;
  color: #FBF5EB;
  border-bottom-right-radius: 5px;
}

/* typing dots */
.typing {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 14px 18px;
}
.typing span {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #7A86F5;
  animation: bounce 1.1s infinite ease-in-out;
}
.typing span:nth-child(2) { animation-delay: 0.18s; }
.typing span:nth-child(3) { animation-delay: 0.36s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
  40%           { transform: translateY(-6px); opacity: 1; }
}

/* ── Footer ── */
.chat-footer {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid rgba(26,22,38,0.07);
  background: rgba(255,255,255,0.55);
  flex-shrink: 0;
}

textarea {
  flex: 1;
  resize: none;
  border: 1.5px solid rgba(26,22,38,0.12);
  border-radius: 14px;
  padding: 10px 14px;
  font-family: 'DM Sans', system-ui, sans-serif;
  font-size: 14px;
  color: #1A1626;
  background: rgba(255,255,255,0.8);
  outline: none;
  transition: border-color 0.2s;
  max-height: 120px;
  overflow-y: auto;
}
textarea:focus { border-color: #7A86F5; }
textarea:disabled { opacity: 0.5; }
textarea::placeholder { color: #B0ABBC; }

button {
  width: 42px; height: 42px;
  border-radius: 13px;
  border: none;
  background: #1A1626;
  color: #FFD56B;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: opacity 0.15s, transform 0.1s;
}
button:hover:not(:disabled) { opacity: 0.85; transform: scale(1.04); }
button:disabled { opacity: 0.35; cursor: default; }
</style>
