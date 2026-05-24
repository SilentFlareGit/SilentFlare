import { expect, test } from '@playwright/test'

const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const TEST_TITLE_PREFIX = 'E2E Admin'
const TEST_SLUG_PREFIX = 'e2e-admin'
const TINY_PNG_BASE64 =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGNgAAAAAgAB4iG8MwAAAABJRU5ErkJggg=='

test.setTimeout(90_000)

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

async function loginThroughApi(request) {
  const response = await request.post(`${API_BASE_URL}/auth/login`, {
    data: {
      username: 'admin',
      password: 'admin123',
    },
  })
  expect(response.ok()).toBeTruthy()
  const body = await response.json()
  return body.access_token
}

async function cleanupPosts(request, token, slugPrefix = TEST_SLUG_PREFIX) {
  const response = await request.get(`${API_BASE_URL}/admin/posts`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok()) return

  const body = await response.json()
  const posts = body.items || []

  for (const post of posts) {
    const isE2ePost =
      post.slug?.startsWith(slugPrefix) ||
      post.title?.startsWith(TEST_TITLE_PREFIX)

    if (!isE2ePost) continue

    await request.delete(`${API_BASE_URL}/admin/posts/${post.id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
  }
}

async function deleteCoverThroughApi(request, token, filename) {
  if (!filename) return

  await request.delete(`${API_BASE_URL}/admin/uploads/covers/${encodeURIComponent(filename)}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

async function fillMarkdownEditor(page, value) {
  const editor = page.getByTestId('post-content-editor').locator('.CodeMirror').first()
  await editor.click()
  await page.keyboard.type(value)
}

async function expectMarkdownPreview(page, heading, body) {
  const editor = page.getByTestId('post-content-editor')
  const preview = editor.locator('.bytemd-preview')
  await expect(preview).toContainText(heading)
  await expect(preview).toContainText(body)
}

async function expectSaveAndReturnToPosts(page, message) {
  await expect(page.locator('.success-msg')).toContainText(message)
  await expect(page).toHaveURL(/#\/posts$/, { timeout: 10_000 })
  await expect(page.getByTestId('posts-table')).toBeVisible({ timeout: 10_000 })
}

async function expectRowPublicLink(row, slug) {
  const link = row.getByRole('link', { name: /^View$/i })
  await expect(link).toBeVisible()
  await expect(link).toHaveAttribute('href', new RegExp(`/${escapeRegExp(slug)}(?:[/?#]|$)`))
}

async function expectNoRowPublicLink(row) {
  await expect(row.getByRole('link', { name: /^View$/i })).toHaveCount(0)
}

async function expectRowCoverThumbnail(page, slug, coverUrl) {
  const coverCell = page.getByTestId(`post-cover-${slug}`)
  await expect(coverCell).toBeVisible()
  await expect(coverCell).not.toContainText('No cover')

  const thumbnail = coverCell.getByTestId('cover-thumb')
  await expect(thumbnail).toBeVisible()
  const thumbnailSrc = await thumbnail.getAttribute('src')
  expect(thumbnailSrc === coverUrl || thumbnailSrc?.includes('/uploads/covers/')).toBeTruthy()
}

function filenameFromCoverUrl(coverUrl) {
  try {
    return new URL(coverUrl).pathname.split('/').pop()
  } catch {
    return coverUrl.split(/[?#]/)[0].split('/').pop()
  }
}

async function expectMediaPageShowsUsedCover(page, coverUrl) {
  const filename = filenameFromCoverUrl(coverUrl)
  expect(filename).toBeTruthy()

  await page.getByTestId('nav-media').click()
  await expect(page).toHaveURL(/#\/media$/)
  await expect(page.getByTestId('media-table')).toBeVisible()

  const row = page.getByTestId(`media-row-${filename}`)
  await expect(row).toBeVisible()
  await expect(row.getByTestId(`in-use-${filename}`)).toBeVisible()
  await expect(row.getByTestId(`delete-media-${filename}`)).toHaveCount(0)
}

async function expectDraftVisibilityHint(page) {
  await expect(
    page.getByText(/draft.*(not.*public|not publicly visible|only visible|private)|not.*public.*draft/i)
  ).toBeVisible()
}

async function expectEditPublicLink(page, slug) {
  const link = page.getByRole('link', { name: /View Public Post/i })
  await expect(link).toBeVisible()
  await expect(link).toHaveAttribute('href', new RegExp(`/${escapeRegExp(slug)}(?:[/?#]|$)`))
}

async function uploadTinyCoverImage(page) {
  await page.getByTestId('cover-file-input').setInputFiles({
    name: 'cover-e2e.png',
    mimeType: 'image/png',
    buffer: Buffer.from(TINY_PNG_BASE64, 'base64'),
  })

  const coverUrlInput = page.getByTestId('post-cover-url')
  await expect(coverUrlInput).toHaveValue(/\/uploads\/covers\/.+\.png(?:$|\?)/)
  const coverUrl = await coverUrlInput.inputValue()

  const preview = page.getByTestId('cover-preview')
  await expect(preview).toBeVisible()
  await expect(preview).toHaveAttribute('src', coverUrl)

  return coverUrl
}

async function uploadUnusedCoverImage(request, token, uniqueId) {
  const response = await request.post(`${API_BASE_URL}/admin/uploads/cover`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    multipart: {
      file: {
        name: `unused-cover-e2e-${uniqueId}.png`,
        mimeType: 'image/png',
        buffer: Buffer.from(TINY_PNG_BASE64, 'base64'),
      },
    },
  })

  expect(response.ok()).toBeTruthy()
  const body = await response.json()
  const coverUrl = body.cover_url || body.coverUrl || body.url || body.location
  expect(coverUrl).toBeTruthy()

  const filename = filenameFromCoverUrl(coverUrl)
  expect(filename).toBeTruthy()

  return { coverUrl, filename }
}

async function expectCanDeleteUnusedCoverMedia(page, filename) {
  await page.getByTestId('nav-media').click()
  await expect(page).toHaveURL(/#\/media$/)
  await page.getByTestId('media-refresh').click()
  await expect(page.getByTestId('media-table')).toBeVisible()

  const row = page.getByTestId(`media-row-${filename}`)
  await expect(row).toBeVisible()

  const deleteButton = row.getByTestId(`delete-media-${filename}`)
  await expect(deleteButton).toBeVisible()

  page.once('dialog', dialog => dialog.accept())
  await deleteButton.click()
  await expect(row).toHaveCount(0)
}

test('admin can manage a draft post end to end', async ({ page, request }) => {
  const token = await loginThroughApi(request)
  await cleanupPosts(request, token)

  const uniqueId = Date.now().toString()
  const title = `${TEST_TITLE_PREFIX} ${uniqueId}`
  const slug = `${TEST_SLUG_PREFIX}-${uniqueId}`
  const updatedSummary = `Updated by Playwright ${uniqueId}`
  const previewBody = `Initial E2E content ${uniqueId}.`
  let uploadedCoverUrl = ''
  let unusedCoverFilename = ''
  let unusedCoverDeleted = false

  try {
    await page.goto('/')

    await page.getByTestId('login-username').fill('admin')
    await page.getByTestId('login-password').fill('admin123')
    await page.getByTestId('login-submit').click()

    await expect(page.getByTestId('posts-table')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Posts' })).toBeVisible()

    await page.getByTestId('new-post-link').click()
    await expect(page.getByTestId('post-form')).toBeVisible()

    await page.getByTestId('post-title').fill(title)
    await expect(page.getByTestId('post-slug')).toHaveValue(slug)
    await page.getByTestId('post-summary').fill(`Draft created by Playwright ${uniqueId}`)
    await fillMarkdownEditor(page, `# ${title}\n\n${previewBody}`)
    await expectMarkdownPreview(page, title, previewBody)
    await page.getByTestId('post-category').fill('e2e')
    await page.getByTestId('post-tags').fill('e2e, playwright')
    await page.getByTestId('post-seo-title').fill(`SEO ${title}`)
    await page.getByTestId('post-meta-description').fill(`Meta description for ${title}`)
    uploadedCoverUrl = await uploadTinyCoverImage(page)
    await page.getByTestId('post-status').selectOption('draft')
    await page.getByTestId('post-submit').click()
    await expectSaveAndReturnToPosts(page, 'Post created successfully!')

    const row = page.getByTestId(`post-row-${slug}`)
    await expect(row).toBeVisible()
    await expect(row).toContainText(title)
    await expect(row).toContainText('draft')
    await expectNoRowPublicLink(row)
    await expect(page.getByTestId(`post-seo-status-${slug}`)).toHaveText('SEO OK')
    await expectRowCoverThumbnail(page, slug, uploadedCoverUrl)
    await expectMediaPageShowsUsedCover(page, uploadedCoverUrl)
    const unusedCover = await uploadUnusedCoverImage(request, token, uniqueId)
    unusedCoverFilename = unusedCover.filename
    await expectCanDeleteUnusedCoverMedia(page, unusedCoverFilename)
    unusedCoverDeleted = true

    await page.goto('/#/posts')
    await expect(page.getByTestId('posts-table')).toBeVisible()

    await page.getByTestId('post-search').fill(slug)
    await expect(row).toBeVisible()

    await page.getByTestId('status-filter').selectOption('draft')
    await expect(row).toBeVisible()

    await page.getByTestId('clear-filters').click()
    await expect(page.getByTestId('post-search')).toHaveValue('')
    await expect(page.getByTestId('status-filter')).toHaveValue('all')

    await page.getByTestId('post-search').fill(slug)
    await page.getByTestId(`edit-post-${slug}`).click()
    await expect(page.getByTestId('post-form')).toBeVisible()
    await expect(page.getByTestId('post-status')).toHaveValue('draft')
    await expect(page.getByTestId('post-cover-url')).toHaveValue(uploadedCoverUrl)
    await expect(page.getByTestId('cover-preview')).toBeVisible()
    await expect(page.getByTestId('cover-preview')).toHaveAttribute('src', uploadedCoverUrl)
    await expectDraftVisibilityHint(page)
    await expect(page.getByRole('link', { name: /View Public Post/i })).toHaveCount(0)
    await expect(page.getByTestId('post-seo-title')).toHaveValue(`SEO ${title}`)
    await expect(page.getByTestId('post-meta-description')).toHaveValue(`Meta description for ${title}`)
    await page.getByTestId('post-summary').fill(updatedSummary)
    await page.getByTestId('post-submit').click()
    await expectSaveAndReturnToPosts(page, 'Post updated successfully!')
    await expect(row).toBeVisible()

    await page.getByTestId('post-search').fill(slug)
    await page.getByTestId('status-filter').selectOption('draft')
    await page.getByTestId(`toggle-status-${slug}`).click()
    await page.getByTestId('status-filter').selectOption('published')
    await expect(row).toBeVisible()
    await expect(row).toContainText('published')
    await expectRowPublicLink(row, slug)

    await page.getByTestId(`edit-post-${slug}`).click()
    await expect(page.getByTestId('post-form')).toBeVisible()
    await expect(page.getByTestId('post-status')).toHaveValue('published')
    await expectEditPublicLink(page, slug)
    await page.goto('/#/posts')
    await expect(page.getByTestId('posts-table')).toBeVisible()
    await page.getByTestId('post-search').fill(slug)
    await page.getByTestId('status-filter').selectOption('published')
    await expect(row).toBeVisible()

    await page.getByTestId(`toggle-status-${slug}`).click()
    await page.getByTestId('status-filter').selectOption('draft')
    await expect(row).toBeVisible()
    await expect(row).toContainText('draft')
    await expectNoRowPublicLink(row)

    page.once('dialog', dialog => dialog.accept())
    await page.getByTestId(`delete-post-${slug}`).click()
    await expect(row).toBeHidden()
  } finally {
    if (unusedCoverFilename && !unusedCoverDeleted) {
      await deleteCoverThroughApi(request, token, unusedCoverFilename)
    }
    await cleanupPosts(request, token, slug)
  }
})
