<template>
  <div>
    <div class="toolbar">
      <h2>Posts</h2>
      <router-link to="/posts/new" class="btn btn-primary">+ New Post</router-link>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="loading" style="text-align:center;padding:40px">Loading...</div>

    <table v-else class="posts-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Status</th>
          <th>Category</th>
          <th>Published</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="posts.length === 0">
          <td colspan="6" style="text-align:center;padding:24px;color:#999">No posts yet.</td>
        </tr>
        <tr v-for="post in posts" :key="post.id">
          <td>{{ post.id }}</td>
          <td>{{ post.title }}</td>
          <td>
            <span class="badge" :class="post.status === 'published' ? 'badge-published' : 'badge-draft'">
              {{ post.status }}
            </span>
          </td>
          <td>{{ post.category }}</td>
          <td>{{ formatDate(post.published_at) }}</td>
          <td>
            <router-link :to="`/posts/${post.id}/edit`" class="btn btn-secondary mr-8" style="padding:4px 10px;font-size:12px">
              Edit
            </router-link>
            <button class="btn btn-danger" style="padding:4px 10px;font-size:12px" @click="handleDelete(post)">
              Delete
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listPosts, deletePost } from '../api.js'

const posts = ref([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await listPosts()
    posts.value = data.items || []
  } catch (e) {
    error.value = 'Failed to load posts.'
  } finally {
    loading.value = false
  }
}

async function handleDelete(post) {
  if (!confirm(`Delete "${post.title}"?`)) return
  try {
    await deletePost(post.id)
    posts.value = posts.value.filter(p => p.id !== post.id)
  } catch (e) {
    alert('Failed to delete post.')
  }
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString()
}

onMounted(load)
</script>
