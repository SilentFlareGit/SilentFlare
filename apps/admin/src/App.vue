<template>
  <div>
    <header class="app-header" v-if="loggedIn">
      <h1>SilentFlare Admin</h1>
      <nav class="app-nav">
        <router-link to="/posts" data-testid="nav-posts">Posts</router-link>
        <router-link to="/media" data-testid="nav-media">Media</router-link>
      </nav>
      <button @click="logout">Logout</button>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, clearToken } from './auth.js'

const router = useRouter()

const loggedIn = computed(() => {
  // Re-evaluate on route change so it updates after login/logout
  void router.currentRoute.value
  return isLoggedIn()
})

function logout() {
  clearToken()
  router.push({ name: 'Login' })
}
</script>
