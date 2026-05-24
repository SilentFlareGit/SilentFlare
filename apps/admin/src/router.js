import { createRouter, createWebHashHistory } from 'vue-router'
import { isLoggedIn } from './auth.js'

import LoginView from './views/LoginView.vue'
import PostsView from './views/PostsView.vue'
import PostFormView from './views/PostFormView.vue'
import MediaView from './views/MediaView.vue'

const routes = [
  { path: '/login', name: 'Login', component: LoginView },
  { path: '/posts', name: 'Posts', component: PostsView },
  { path: '/posts/new', name: 'NewPost', component: PostFormView },
  { path: '/posts/:id/edit', name: 'EditPost', component: PostFormView, props: true },
  { path: '/posts/:id/preview', name: 'PreviewPost', component: () => import('./views/PostPreviewView.vue'), props: true },
  { path: '/media', name: 'Media', component: MediaView },
  { path: '/', redirect: '/posts' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// Navigation guard — redirect unauthenticated users to /login
router.beforeEach((to) => {
  if (to.name !== 'Login' && !isLoggedIn()) {
    return { name: 'Login' }
  }
})

export default router
