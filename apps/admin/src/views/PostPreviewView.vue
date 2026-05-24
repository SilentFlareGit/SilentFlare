<template>
  <div class="card" data-testid="post-preview">
    <div class="toolbar" style="margin-bottom: 24px">
      <h2 data-testid="preview-title">{{ post?.title || 'Loading...' }}</h2>
      <div style="display:flex;gap:8px;align-items:center">
        <router-link :to="`/posts`" class="btn btn-secondary">← Posts</router-link>
        <router-link :to="`/posts/${postId}/edit`" class="btn btn-secondary" data-testid="preview-back-link">Edit Post</router-link>
      </div>
    </div>

    <div v-if="loadError" class="error-msg">{{ loadError }}</div>
    <div v-if="loadingPost" style="text-align:center;padding:40px">Loading...</div>

    <div v-else-if="post">
      <div style="margin-bottom: 16px;">
        <span class="badge" :class="post.status === 'published' ? 'badge-published' : 'badge-draft'">
          {{ post.status }}
        </span>
        <span v-if="post.category" style="margin-left: 8px; font-weight: 500; font-size: 13px">{{ post.category }}</span>
        <span v-if="post.tags && post.tags.length" style="margin-left: 8px; color: #666; font-size: 13px">{{ (Array.isArray(post.tags) ? post.tags : post.tags.split(',')).join(', ') }}</span>
      </div>

      <p v-if="post.summary" data-testid="preview-summary" style="font-style: italic; color: #555; margin-bottom: 20px;">
        {{ post.summary }}
      </p>

      <img
        v-if="post.cover_url"
        :src="post.cover_url"
        alt="Cover image"
        style="max-width: 100%; max-height: 400px; border-radius: 8px; margin-bottom: 24px; display: block;"
      />

      <div data-testid="preview-content" class="bytemd-wrapper" style="border: 1px solid #ddd; padding: 16px; border-radius: 4px; background: #fff">
        <Viewer :value="post.content_markdown || ''" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getPost } from '../api.js'
import { Viewer } from '@bytemd/vue-next'
import 'bytemd/dist/index.min.css'

const route = useRoute()
const postId = computed(() => route.params.id)

const post = ref(null)
const loadingPost = ref(false)
const loadError = ref('')

onMounted(async () => {
  loadingPost.value = true
  try {
    post.value = await getPost(postId.value)
  } catch (e) {
    loadError.value = 'Failed to load post.'
  } finally {
    loadingPost.value = false
  }
})
</script>
