<script setup>
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Card from 'primevue/card'
import { useLearningStore } from '@/stores/useLearningStore'
import { mockQuestions } from '@/data/mockQuestions'

const router = useRouter()
const learningStore = useLearningStore()

const startExam = (examId) => {
  const questionList = mockQuestions[examId]

  if (!questionList) {
    console.error(`問題データが見つかりません: ${examId}`)
    return
  }

  learningStore.startLearning(examId, questionList)

  router.push({
    name: 'learning',
    params: { examId },
  })
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center p-4 md:p-8">
    <section class="w-full max-w-6xl">
      <header class="mb-8 text-center">
        <h1 class="mb-3 text-3xl font-bold">IT資格試験 学習支援アプリ</h1>
      </header>

      <Card v-for="exam in learningStore.examList" :key="exam.id">
        <template #title>
          {{ exam.name }}
        </template>

        <template #content>
          <p class="mb-4 text-surface-500">{{ exam.name }}の問題に挑戦します。</p>

          <Button
            label="学習を開始"
            icon="pi pi-arrow-right"
            icon-pos="right"
            class="w-full"
            @click="startExam(exam.id)"
          />
        </template>
      </Card>
    </section>
  </main>
</template>
