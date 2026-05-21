<template>
  <div>
    <div class="toolbar">
      <h2>Posts</h2>
      <router-link to="/posts/new" class="btn btn-primary">+ New Post</router-link>
    </div>

    <!-- Search & filter controls -->
    <div class="posts-filters" style="display:flex;gap:12px;margin-bottom:16px;align-items:center;flex-wrap:wrap">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search by title, slug, or category…"
        style="flex:1;min-width:200px;padding:6px 10px;border:1px solid #ccc;border-radius:4px;font-size:14px"
      />
      <select
        v-model="statusFilter"
        style="padding:6px 10px;border:1px solid #ccc;border-radius:4px;font-size:14px"
      >
        <option value="all">All statuses</option>
        <option value="draft">Draft</option>
        <option value="published">Published</option>
      </select>
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
          <th>Updated</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="filteredPosts.length === 0">
          <td colspan="7" style="text-align:center;padding:24px;color:#999">No posts found.</td>
        </tr>
        <tr v-for="post in filteredPosts" :key="post.id">
          <td>{{ post.id }}</td>
          <td>{{ post.title }}</td>
          <td>
            <span class="badge" :class="post.status === 'published' ? 'badge-published' : 'badge-draft'">
              {{ post.status }}
            </span>
          </td>
          <td>{{ post.category }}</td>
          <td>{{ formatDate(post.published_at) }}</td>
          <td>{{ formatDate(post.updated_at) }}</td>
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
import { ref, computed, onMounted } from 'vue'
import { listPosts, deletePost } from '../api.js'

const posts = ref([])
const loading = ref(true)
const error = ref('')

// --- Filter state ---
const searchQuery = ref('')
const statusFilter = ref('all')

// --- Computed: filtered + sorted posts ---
const filteredPosts = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  const status = statusFilter.value

  return posts.value
    .filter((post) => {
      // Status filter
      if (status !== 'all' && post.status !== status) return false

      // Search filter (title, slug, category)
      if (query) {
        const title = (post.title || '').toLowerCase()
        const slug = (post.slug || '').toLowerCase()
        const category = (post.category || '').toLowerCase()
        if (!title.includes(query) && !slug.includes(query) && !category.includes(query)) {
          return false
        }
      }

      return true
    })
    // Sort newest first (highest id first)
    .sort((a, b) => b.id - a.id)
})

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
