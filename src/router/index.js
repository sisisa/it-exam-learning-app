import { createRouter, createWebHistory } from 'vue-router'

import ExamSelectView from '@/views/ExamSelectView.vue'
import LearningView from '@/views/LearningView.vue'

const routes = [
  {
    path: '/',
    name: 'exam-select',
    component: ExamSelectView,
  },
  {
    path: '/learning/:examId',
    name: 'learning',
    component: LearningView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
