<template>
  <div>
    <div class="toolbar">
      <h2>{{ isEdit ? 'Edit Post' : 'New Post' }}</h2>
      <router-link to="/posts" class="btn btn-secondary">← Back</router-link>
    </div>

    <div v-if="loadError" class="error-msg">{{ loadError }}</div>
    <div v-if="loadingPost" style="text-align:center;padding:40px">Loading...</div>

    <form v-else class="card" @submit.prevent="handleSubmit">
      <div v-if="success" class="success-msg">{{ success }}</div>
      <div v-if="error" class="error-msg">{{ error }}</div>

      <div class="form-group">
        <label for="title">Title</label>
        <input id="title" v-model="form.title" type="text" required />
      </div>

      <div class="form-group">
        <label for="slug">Slug <small>(leave blank to auto-generate)</small></label>
        <input id="slug" v-model="form.slug" type="text" />
      </div>

      <div class="form-group">
        <label for="summary">Summary</label>
        <input id="summary" v-model="form.summary" type="text" />
      </div>

      <div class="form-group">
        <label>Content (Markdown)</label>
        <div class="bytemd-wrapper">
          <Editor
            :value="form.content_markdown"
            @change="handleEditorChange"
          />
        </div>
      </div>

      <div class="form-group">
        <label for="cover_url">Cover URL</label>
        <input id="cover_url" v-model="form.cover_url" type="text" />
      </div>

      <div class="form-group">
        <label for="status">Status</label>
        <select id="status" v-model="form.status">
          <option value="draft">Draft</option>
          <option value="published">Published</option>
        </select>
      </div>

      <div class="form-group">
        <label for="category">Category</label>
        <input id="category" v-model="form.category" type="text" />
      </div>

      <div class="form-group">
        <label for="tags">Tags <small>(comma-separated)</small></label>
        <input id="tags" v-model="tagsInput" type="text" placeholder="tag1, tag2, tag3" />
      </div>

      <div class="form-group">
        <label for="published_at">Published At <small>(optional, e.g. 2026-05-20T12:00:00Z)</small></label>
        <input id="published_at" v-model="form.published_at" type="text" />
      </div>

      <button type="submit" class="btn btn-primary" :disabled="saving">
        {{ saving ? 'Saving...' : (isEdit ? 'Update Post' : 'Create Post') }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Editor } from '@bytemd/vue-next'
import 'bytemd/dist/index.min.css'
import { getPost, createPost, updatePost } from '../api.js'

const props = defineProps({
  id: String,
})

const router = useRouter()
const route = useRoute()

// Determine edit vs new from the route
const postId = computed(() => props.id || route.params.id)
const isEdit = computed(() => !!postId.value)

const form = ref({
  title: '',
  slug: '',
  summary: '',
  content_markdown: '',
  cover_url: '',
  status: 'draft',
  category: '',
  published_at: '',
})

const tagsInput = ref('')
const error = ref('')
const success = ref('')
const loadError = ref('')
const saving = ref(false)
const loadingPost = ref(false)

// ByteMD emits @change with the new markdown string
function handleEditorChange(val) {
  form.value.content_markdown = val
}

// Load existing post for editing
onMounted(async () => {
  if (!isEdit.value) return
  loadingPost.value = true
  try {
    const post = await getPost(postId.value)
    form.value = {
      title: post.title || '',
      slug: post.slug || '',
      summary: post.summary || '',
      content_markdown: post.content_markdown || '',
      cover_url: post.cover_url || '',
      status: post.status || 'draft',
      category: post.category || '',
      published_at: post.published_at || '',
    }
    tagsInput.value = (post.tags || []).join(', ')
  } catch (e) {
    loadError.value = 'Failed to load post.'
  } finally {
    loadingPost.value = false
  }
})

async function handleSubmit() {
  error.value = ''
  success.value = ''
  saving.value = true

  // Build payload
  const payload = { ...form.value }
  payload.tags = tagsInput.value
    .split(',')
    .map(t => t.trim())
    .filter(Boolean)

  // Remove empty optional fields
  if (!payload.slug) delete payload.slug
  if (!payload.published_at) delete payload.published_at

  try {
    if (isEdit.value) {
      await updatePost(postId.value, payload)
    } else {
      await createPost(payload)
    }
    // Show success briefly, then navigate back
    success.value = isEdit.value ? 'Post updated successfully!' : 'Post created successfully!'
    setTimeout(() => router.push({ name: 'Posts' }), 1500)
  } catch (e) {
    error.value = `Failed to ${isEdit.value ? 'update' : 'create'} post. ${e.message}`
  } finally {
    saving.value = false
  }
}
</script>
