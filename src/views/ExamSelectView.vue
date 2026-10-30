<script setup>
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Card from 'primevue/card'
import { useLearningStore } from '@/stores/useLearningStore'

const router = useRouter()
const learningStore = useLearningStore()

/**
 * オプション配列を { id, text } の形式に正規化
 */
const normalizeOptions = (options) => {
  if (!Array.isArray(options)) return []
  return options.map((opt) => {
    const key = Object.keys(opt)[0]
    return {
      id: key,
      text: opt[key],
    }
  })
}

/**
 * 試験種別に応じて問題データを取得・整形
 */
const fetchQuestions = async (examId) => {
  const filePaths = {
    'it-passport': '/data/it/questions.json',
    'fundamental-examination': '/data/fe/questions.json',
    'applied-examination': '/data/ap/questions.json',
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

  // 選択された試験の問題のみ抽出し、optionsを正規化
  return questions
    .filter((question) => question.exam === examId)
    .map((question) => ({
      ...question,
      options: normalizeOptions(question.options),
    }))
}

const startExam = async (examId) => {
  try {
    const questionList = await fetchQuestions(examId)

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

      <Card v-for="exam in learningStore.examList" :key="exam.id" class="mb-4">
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
