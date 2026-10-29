<script setup>
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Card from 'primevue/card'
import { useLearningStore } from '@/stores/useLearningStore'

const router = useRouter()
const learningStore = useLearningStore()

/**
 * 試験種別に応じて問題データを取得する
 */
const fetchQuestions = async (examId) => {
  const filePaths = {
    'it-passport': '/data/it/questions.json',
    'fundamental-examination': '/data/fe/questions.json',
    'applied-information': '/data/ap/questions.json',
  }

  const filePath = filePaths[examId]

  if (!filePath) {
    throw new Error(`未対応の試験です: ${examId}`)
  }

  const response = await fetch(filePath)

  if (!response.ok) {
    throw new Error(`問題データの取得に失敗しました: ${response.status}`)
  }

  const questions = await response.json()

  // JSON内のexamが選択した試験と一致する問題を取得
  return questions.filter((question) => question.exam === examId)
}

const startExam = async (examId) => {
  try {
    const questionList = await fetchQuestions(examId)

    console.log('questionList', questionList)
    console.log('examId', examId)

    if (questionList.length === 0) {
      console.error(`問題データが見つかりません: ${examId}`)
      return
    }

    learningStore.startLearning(examId, questionList)

    router.push({
      name: 'learning',
      params: { examId },
    })
  } catch (error) {
    console.error('問題データの取得エラー:', error)
  }
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
