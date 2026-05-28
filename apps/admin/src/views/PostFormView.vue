<template>
  <div>
    <div class="toolbar">
      <h2>
        {{ isEdit ? 'Edit Post' : 'New Post' }}
        <span class="badge" :class="form.status === 'published' ? 'badge-published' : 'badge-draft'">
          {{ form.status }}
        </span>
      </h2>
      <div style="display:flex;gap:8px;align-items:center">
        <a
          v-if="publicPostUrl"
          :href="publicPostUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="btn btn-secondary"
          style="font-size:13px;padding:6px 12px"
        >View Public Post</a>
        <router-link
          v-if="isEdit"
          :to="`/posts/${postId}/preview`"
          class="btn btn-secondary"
          data-testid="preview-current-post"
          style="font-size:13px;padding:6px 12px"
        >Preview</router-link>
        <router-link to="/posts" class="btn btn-secondary">< Back</router-link>
      </div>
    </div>
    <p v-if="isEdit && form.status === 'draft'" class="draft-hint">
      Draft posts are not visible on the public blog.
    </p>

    <div v-if="loadError" class="error-msg">{{ loadError }}</div>
    <div v-if="loadingPost" style="text-align:center;padding:40px">Loading...</div>

    <form v-else class="card" data-testid="post-form" @submit.prevent="handleSubmit">
      <div v-if="success" class="success-msg">{{ success }}</div>
      <div v-if="error" class="error-msg">{{ error }}</div>

      <div class="form-group">
        <label for="title">Title</label>
        <input id="title" v-model="form.title" data-testid="post-title" type="text" required />
      </div>

      <div class="form-group">
        <label for="slug">Slug <small>(leave blank to auto-generate)</small></label>
        <input id="slug" v-model="form.slug" data-testid="post-slug" type="text" @input="onSlugInput" />
      </div>

      <div class="form-group">
        <label for="summary">Summary</label>
        <input id="summary" v-model="form.summary" data-testid="post-summary" type="text" />
      </div>

      <div class="form-group">
        <label>Content (Markdown)</label>
        <div class="bytemd-wrapper" data-testid="post-content-editor">
          <Editor
            :value="form.content_markdown"
            mode="split"
            @change="handleEditorChange"
          />
        </div>
      </div>

      <div class="form-group">
        <label for="cover_url">Cover URL</label>
        <div style="display:flex;gap:8px;align-items:center">
          <input id="cover_url" v-model="form.cover_url" data-testid="post-cover-url" type="text" style="flex:1" />
          <input
            ref="coverFileInput"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            data-testid="cover-file-input"
            style="display:none"
            @change="handleCoverUpload"
          />
          <button
            type="button"
            class="btn btn-secondary"
            style="white-space:nowrap;font-size:13px;padding:6px 12px"
            :disabled="uploading"
            data-testid="cover-upload-btn"
            @click="coverFileInput?.click()"
          >
            {{ uploading ? 'Uploading...' : 'Upload Image' }}
          </button>
        </div>
        <p v-if="uploadError" class="error-msg" style="margin-top:4px;font-size:13px" data-testid="cover-upload-error">{{ uploadError }}</p>
        <img
          v-if="form.cover_url"
          :src="form.cover_url"
          alt="Cover preview"
          data-testid="cover-preview"
          style="margin-top:8px;max-width:320px;max-height:180px;border-radius:4px;border:1px solid #333"
        />
      </div>

      <div class="form-group">
        <label for="status">Status</label>
        <select id="status" v-model="form.status" data-testid="post-status">
          <option value="draft">Draft</option>
          <option value="published">Published</option>
        </select>
      </div>

      <div class="form-group">
        <label for="category">Category</label>
        <input id="category" v-model="form.category" data-testid="post-category" type="text" />
      </div>

      <div class="form-group">
        <label for="tags">Tags <small>(comma-separated)</small></label>
        <input id="tags" v-model="tagsInput" data-testid="post-tags" type="text" placeholder="tag1, tag2, tag3" />
      </div>

      <div class="form-group">
        <label for="published_at">Published At <small>(optional, e.g. 2026-05-20T12:00:00Z)</small></label>
        <input id="published_at" v-model="form.published_at" data-testid="post-published-at" type="text" />
      </div>

      <fieldset class="seo-section">
        <legend>SEO</legend>
        <div class="form-group">
          <label for="seo_title">SEO Title</label>
          <input id="seo_title" v-model="form.seo_title" data-testid="post-seo-title" type="text" />
        </div>
        <div class="form-group">
          <label for="meta_description">Meta Description</label>
          <textarea id="meta_description" v-model="form.meta_description" data-testid="post-meta-description" rows="3"></textarea>
        </div>
      </fieldset>

      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <button type="submit" class="btn btn-primary" :disabled="saving" data-testid="post-submit">
          {{ saving ? 'Saving...' : (isEdit ? 'Update Post' : 'Create Post') }}
        </button>
        <button
          type="button"
          class="btn btn-secondary"
          :disabled="saving"
          data-testid="post-submit-keep-editing"
          @click="handleSubmit({ keepEditing: true })"
        >
          {{ saving ? 'Saving...' : (isEdit ? 'Update and keep editing' : 'Create and keep editing') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Editor } from '@bytemd/vue-next'
import 'bytemd/dist/index.min.css'
import { getPost, createPost, updatePost, uploadCover } from '../api.js'

const blogBaseUrl = import.meta.env.VITE_PUBLIC_BLOG_BASE_URL || 'http://localhost:4321'

const props = defineProps({
  id: String,
})

const router = useRouter()
const route = useRoute()

// Determine edit vs new from the route
const postId = computed(() => props.id || route.params.id)
const isEdit = computed(() => !!postId.value)

const publicPostUrl = computed(() => {
  if (isEdit.value && form.value.status === 'published' && form.value.slug) {
    return `${blogBaseUrl}/posts/${form.value.slug}`
  }
  return ''
})

const form = ref({
  title: '',
  slug: '',
  summary: '',
  content_markdown: '',
  cover_url: '',
  status: 'draft',
  category: '',
  published_at: '',
  seo_title: '',
  meta_description: '',
})

const tagsInput = ref('')
const error = ref('')
const success = ref('')
const loadError = ref('')
const saving = ref(false)
const loadingPost = ref(false)

// Cover upload
const coverFileInput = ref(null)
const uploading = ref(false)
const uploadError = ref('')

// --- Auto slug generation (new post only) ---
const slugManuallyEdited = ref(false)

// Simple slug helper: lowercase, replace non-alphanumeric with hyphens, trim hyphens
function generateSlug(text) {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

// When the user types in the slug field, mark it as manually edited
function onSlugInput() {
  slugManuallyEdited.value = true
}

// Watch title changes - auto-fill slug only for new posts and only if user hasn't edited slug
watch(
  () => form.value.title,
  (newTitle) => {
    if (isEdit.value) return
    if (slugManuallyEdited.value) return
    form.value.slug = generateSlug(newTitle)
  }
)

// -- Cover image upload --
async function handleCoverUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return

  uploading.value = true
  uploadError.value = ''

  try {
    const data = await uploadCover(file)
    form.value.cover_url = data.cover_url
  } catch (e) {
    uploadError.value = e.message || 'Upload failed'
  } finally {
    uploading.value = false
    // Reset so the same file can be re-selected
    if (coverFileInput.value) coverFileInput.value.value = ''
  }
}

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
      seo_title: post.seo_title || '',
      meta_description: post.meta_description || '',
    }
    tagsInput.value = (post.tags || []).join(', ')
  } catch (e) {
    loadError.value = 'Failed to load post.'
  } finally {
    loadingPost.value = false
  }
})

async function handleSubmit({ keepEditing = false } = {}) {
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
    let created
    if (isEdit.value) {
      await updatePost(postId.value, payload)
    } else {
      created = await createPost(payload)
    }
    success.value = isEdit.value ? 'Post updated successfully!' : 'Post created successfully!'

    if (keepEditing) {
      if (!isEdit.value && created?.id) {
        // New post: navigate to its edit route
        router.push(`/posts/${created.id}/edit`)
      }
      // Existing post: stay on the current route (no navigation)
    } else {
      // Original behavior: navigate back to Posts list
      setTimeout(() => router.push({ name: 'Posts' }), 1500)
    }
  } catch (e) {
    error.value = `Failed to ${isEdit.value ? 'update' : 'create'} post. ${e.message}`
  } finally {
    saving.value = false
  }
}
</script>
