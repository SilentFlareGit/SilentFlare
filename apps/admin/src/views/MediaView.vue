<template>
  <div>
    <div class="toolbar">
      <h2>Media - Cover Images</h2>
      <button class="btn btn-secondary" data-testid="media-refresh" @click="load">Refresh</button>
    </div>

    <div v-if="error" class="error-msg" data-testid="media-error">{{ error }}</div>

    <div v-if="loading" style="text-align:center;padding:40px" data-testid="media-loading">Loading...</div>

    <div v-else-if="files.length === 0" style="text-align:center;padding:40px;color:#999" data-testid="media-empty">
      No cover files found.
    </div>

    <table v-else class="media-table" data-testid="media-table">
      <thead>
        <tr>
          <th>Thumbnail</th>
          <th>Filename</th>
          <th>Size</th>
          <th>Modified</th>
          <th>Status</th>
          <th>Used By</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="file in files" :key="file.filename" :data-testid="`media-row-${file.filename}`">
          <td>
            <img
              :src="file.cover_url"
              :alt="file.filename"
              class="media-thumb"
            />
          </td>
          <td class="media-filename">{{ file.filename }}</td>
          <td>{{ formatSize(file.size_bytes) }}</td>
          <td>{{ formatDate(file.modified_at) }}</td>
          <td>
            <span v-if="file.used" class="badge badge-published">Used</span>
            <span v-else class="badge badge-draft">Unused</span>
          </td>
          <td>
            <span v-if="file.used_by_post_ids && file.used_by_post_ids.length">
              {{ file.used_by_post_ids.join(', ') }}
            </span>
            <span v-else style="color:#999">-</span>
          </td>
          <td>
            <button
              v-if="!file.used"
              class="btn btn-danger"
              style="padding:4px 10px;font-size:12px"
              :data-testid="`delete-media-${file.filename}`"
              :disabled="file._deleting"
              @click="handleDelete(file)"
            >
              {{ file._deleting ? 'Deleting...' : 'Delete' }}
            </button>
            <span
              v-else
              style="color:#999;font-size:12px;font-style:italic"
              :data-testid="`in-use-${file.filename}`"
            >In use</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listCoverUploads, deleteCoverUpload } from '../api.js'

const files = ref([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await listCoverUploads()
    // API may return { items: [...] } or an array directly
    files.value = Array.isArray(data) ? data : (data.items || [])
  } catch (e) {
    error.value = 'Failed to load cover files.'
  } finally {
    loading.value = false
  }
}

async function handleDelete(file) {
  const msg = `Delete "${file.filename}"?\nThis file is unused and will be permanently removed.`
  if (!confirm(msg)) return

  file._deleting = true
  error.value = ''
  try {
    await deleteCoverUpload(file.filename)
    files.value = files.value.filter(f => f.filename !== file.filename)
  } catch (e) {
    file._deleting = false
    error.value = `Failed to delete "${file.filename}".`
  }
}

function formatSize(bytes) {
  if (bytes == null) return '-'
  if (bytes < 1024) return bytes + ' B'
  const kb = bytes / 1024
  if (kb < 1024) return kb.toFixed(1) + ' KB'
  const mb = kb / 1024
  return mb.toFixed(1) + ' MB'
}

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleDateString()
}

onMounted(load)
</script>
