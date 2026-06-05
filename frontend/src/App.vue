<script setup>
import Chat from './components/Chat.vue'

function onProfileReady(profile) {
  console.log('Profile ready:', profile)
}
</script>

<template>
  <div class="shell">
    <Chat api-url="http://localhost:8000/api/chat" @profile-ready="onProfileReady" />
  </div>
</template>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, #app {
  min-height: 100vh;
  font-family: 'DM Sans', system-ui, sans-serif;
}

body {
  background: #FBF5EB;
  background-image:
    radial-gradient(circle at 12% 18%, rgba(255, 213, 107, 0.45), transparent 35%),
    radial-gradient(circle at 88% 82%, rgba(122, 134, 245, 0.30), transparent 40%),
    radial-gradient(circle at 50% 50%, rgba(255, 194, 184, 0.20), transparent 60%);
}

.shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
</style>
