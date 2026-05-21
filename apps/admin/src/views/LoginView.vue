<template>
  <div class="login-wrapper">
    <div class="card login-box">
      <h2>Admin Login</h2>
      <div v-if="error" class="error-msg">{{ error }}</div>
      <form data-testid="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">Username</label>
          <input id="username" v-model="username" data-testid="login-username" type="text" required autocomplete="username" />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input id="password" v-model="password" data-testid="login-password" type="password" required autocomplete="current-password" />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="loading" data-testid="login-submit" style="width:100%">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../api.js'
import { setToken } from '../auth.js'

const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const data = await login(username.value, password.value)
    setToken(data.access_token)
    router.push({ name: 'Posts' })
  } catch (e) {
    error.value = 'Login failed. Check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>
