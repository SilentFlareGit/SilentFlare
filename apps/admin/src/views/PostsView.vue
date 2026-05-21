<template>
  <div>
    <div class="toolbar">
      <h2>Posts</h2>
      <router-link to="/posts/new" class="btn btn-primary" data-testid="new-post-link">+ New Post</router-link>
    </div>

    <!-- Search & filter controls -->
    <div class="posts-filters" style="display:flex;gap:12px;margin-bottom:12px;align-items:center;flex-wrap:wrap">
      <input
        v-model="searchQuery"
        data-testid="post-search"
        type="text"
        placeholder="Search by title, slug, or category…"
        style="flex:1;min-width:200px;padding:6px 10px;border:1px solid #ccc;border-radius:4px;font-size:14px"
      />
      <select
        v-model="statusFilter"
        data-testid="status-filter"
        style="padding:6px 10px;border:1px solid #ccc;border-radius:4px;font-size:14px"
      >
        <option value="all">All statuses</option>
        <option value="draft">Draft</option>
        <option value="published">Published</option>
      </select>
      <button
        v-if="searchQuery || statusFilter !== 'all'"
        class="btn btn-secondary"
        data-testid="clear-filters"
        style="padding:6px 12px;font-size:13px"
        @click="clearFilters"
      >
        Clear filters
      </button>
    </div>

    <!-- Count summary -->
    <div v-if="!loading" style="margin-bottom:12px;font-size:13px;color:#666">
      Showing {{ filteredPosts.length }} of {{ posts.length }} posts
      · {{ draftCount }} draft · {{ publishedCount }} published
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="loading" style="text-align:center;padding:40px">Loading...</div>

    <table v-else class="posts-table" data-testid="posts-table">
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
        <tr v-for="post in filteredPosts" :key="post.id" :data-testid="`post-row-${post.slug}`">
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
          <td style="white-space:nowrap">
            <button
              class="btn"
              :class="post.status === 'draft' ? 'btn-primary' : 'btn-secondary'"
              :data-testid="`toggle-status-${post.slug}`"
              style="padding:4px 10px;font-size:12px;margin-right:4px"
              :disabled="post._toggling"
              @click="handleToggleStatus(post)"
            >
              {{ post._toggling ? '...' : (post.status === 'draft' ? 'Publish' : 'Unpublish') }}
            </button>
            <router-link :to="`/posts/${post.id}/edit`" class="btn btn-secondary mr-8" :data-testid="`edit-post-${post.slug}`" style="padding:4px 10px;font-size:12px">
              Edit
            </router-link>
            <button class="btn btn-danger" :data-testid="`delete-post-${post.slug}`" style="padding:4px 10px;font-size:12px" @click="handleDelete(post)">
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
import { listPosts, deletePost, updatePost } from '../api.js'

const posts = ref([])
const loading = ref(true)
const error = ref('')

// --- Filter state ---
const searchQuery = ref('')
const statusFilter = ref('all')

// --- Count helpers ---
const draftCount = computed(() => posts.value.filter(p => p.status === 'draft').length)
const publishedCount = computed(() => posts.value.filter(p => p.status === 'published').length)

// --- Clear filters ---
function clearFilters() {
  searchQuery.value = ''
  statusFilter.value = 'all'
}

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

// --- Quick status toggle ---
async function handleToggleStatus(post) {
  const newStatus = post.status === 'draft' ? 'published' : 'draft'
  post._toggling = true
  error.value = ''
  try {
    const updated = await updatePost(post.id, { status: newStatus })
    // Update the post in our local array
    const idx = posts.value.findIndex(p => p.id === post.id)
    if (idx !== -1) {
      posts.value[idx] = { ...posts.value[idx], ...updated, _toggling: false }
    }
  } catch (e) {
    post._toggling = false
    error.value = `Failed to ${newStatus === 'published' ? 'publish' : 'unpublish'} "${post.title}".`
  }
}

// --- Better delete confirmation ---
async function handleDelete(post) {
  const msg = `Delete "${post.title}"?\nStatus: ${post.status}\nThis cannot be undone.`
  if (!confirm(msg)) return
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
