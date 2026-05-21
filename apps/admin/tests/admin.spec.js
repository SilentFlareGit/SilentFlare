import { expect, test } from '@playwright/test'

const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const TEST_TITLE_PREFIX = 'E2E Admin'
const TEST_SLUG_PREFIX = 'e2e-admin'

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

async function fillMarkdownEditor(page, value) {
  const editor = page.getByTestId('post-content-editor').locator('.CodeMirror').first()
  await editor.click()
  await page.keyboard.type(value)
}

async function expectSaveAndReturnToPosts(page, message) {
  await expect(page.locator('.success-msg')).toContainText(message)
  await expect(page).toHaveURL(/#\/posts$/, { timeout: 10_000 })
  await expect(page.getByTestId('posts-table')).toBeVisible({ timeout: 10_000 })
}

test('admin can manage a draft post end to end', async ({ page, request }) => {
  const token = await loginThroughApi(request)
  await cleanupPosts(request, token)

  const uniqueId = Date.now().toString()
  const title = `${TEST_TITLE_PREFIX} ${uniqueId}`
  const slug = `${TEST_SLUG_PREFIX}-${uniqueId}`
  const updatedSummary = `Updated by Playwright ${uniqueId}`

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
    await fillMarkdownEditor(page, `# ${title}\n\nInitial E2E content.`)
    await page.getByTestId('post-category').fill('e2e')
    await page.getByTestId('post-tags').fill('e2e, playwright')
    await page.getByTestId('post-status').selectOption('draft')
    await page.getByTestId('post-submit').click()
    await expectSaveAndReturnToPosts(page, 'Post created successfully!')

    const row = page.getByTestId(`post-row-${slug}`)
    await expect(row).toBeVisible()
    await expect(row).toContainText(title)
    await expect(row).toContainText('draft')

    await page.getByTestId('post-search').fill(slug)
    await expect(row).toBeVisible()

    await page.getByTestId('status-filter').selectOption('draft')
    await expect(row).toBeVisible()

    await page.getByTestId('clear-filters').click()
    await expect(page.getByTestId('post-search')).toHaveValue('')
    await expect(page.getByTestId('status-filter')).toHaveValue('all')

    await page.getByTestId('post-search').fill(slug)
    await page.getByTestId('status-filter').selectOption('draft')
    await page.getByTestId(`toggle-status-${slug}`).click()
    await page.getByTestId('status-filter').selectOption('published')
    await expect(row).toBeVisible()
    await expect(row).toContainText('published')

    await page.getByTestId(`toggle-status-${slug}`).click()
    await page.getByTestId('status-filter').selectOption('draft')
    await expect(row).toBeVisible()
    await expect(row).toContainText('draft')

    await page.getByTestId(`edit-post-${slug}`).click()
    await expect(page.getByTestId('post-form')).toBeVisible()
    await page.getByTestId('post-summary').fill(updatedSummary)
    await page.getByTestId('post-submit').click()
    await expectSaveAndReturnToPosts(page, 'Post updated successfully!')
    await expect(row).toBeVisible()

    page.once('dialog', dialog => dialog.accept())
    await page.getByTestId(`delete-post-${slug}`).click()
    await expect(row).toBeHidden()
  } finally {
    await cleanupPosts(request, token, slug)
  }
})
