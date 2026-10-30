<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import Button from 'primevue/button'
import Card from 'primevue/card'
import RadioButton from 'primevue/radiobutton'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'

import { useLearningStore } from '@/stores/useLearningStore'

const route = useRoute()
const router = useRouter()
const learningStore = useLearningStore()

// 解答確定後に表示・入力する任意項目
const incorrectCauses = ref('')
const investigationRecords = ref('')
const isSaving = ref(false)

// 現在の問題に対応する正解の選択肢オブジェクトを取得
const correctAnswerOption = computed(() => {
  const question = learningStore.currentQuestion
  if (!question) return null
  return question.options.find((option) => option.id === question.correctAnswer) ?? null
})

// 直アクセス等の制御（未選択状態なら試験選択へ戻す）
onMounted(() => {
  const routeExamId = route.params.examId
  if (
    !learningStore.selectedExam ||
    learningStore.selectedExamId !== routeExamId ||
    learningStore.totalQuestions === 0
  ) {
    router.replace({ name: 'exam-select' })
  }
})

// 選択肢を選ぶ
const selectAnswer = (optionId) => {
  learningStore.selectAnswer(optionId)
}

// 解答を確定し正誤判定を表示（まだAPI保存はしない）
const submitAnswer = () => {
  learningStore.submitAnswer()
}

// Express API経由で answers.json へ解答データを保存する処理
const saveAnswerToExpress = async (record) => {
  try {
    isSaving.value = true

    // 相対パスでリクエスト（Viteプロキシ経由で http://localhost:3000/api/answers へ転送される）
    const response = await fetch('/api/answers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        examId: learningStore.selectedExamId,
        answerData: record,
      }),
    })

    if (!response.ok) {
      const errorDetail = await response.json().catch(() => ({}))
      throw new Error(errorDetail.message || `ステータスコード: ${response.status}`)
    }

    const data = await response.json()
    console.log('保存結果:', data.message)
  } catch (error) {
    console.error('API保存エラー:', error)
  } finally {
    isSaving.value = false
  }
}

// 「次の問題へ」押下時に任意入力項目も含めて保存し、次の問題へ移動
const handleNextQuestion = async () => {
  // ストアへのデータ記録とオブジェクト生成
  const record = learningStore.recordAnswer({
    incorrect_causes: incorrectCauses.value,
    investigation_records: investigationRecords.value,
  })

  // Expressサーバー経由でJSONファイルへ保存
  if (record) {
    await saveAnswerToExpress(record)
  }

  // 入力欄をクリア
  incorrectCauses.value = ''
  investigationRecords.value = ''

  //次の問題に行くための処理
  learningStore.nextQuestion()
}

// 試験選択画面へ戻る
const returnToExamSelect = () => {
  learningStore.resetLearning()
  router.push({ name: 'exam-select' })
}
</script>

<template>
  <main class="learning-page">
    <!-- 演習完了画面 -->
    <Card v-if="learningStore.isCompleted" class="result-card">
      <template #title> 演習結果 </template>

      <template #content>
        <p class="result-exam">{{ learningStore.selectedExam?.name }}</p>

        <div class="result-rate">
          <span class="result-rate-value">{{ learningStore.accuracyRate }}%</span>
          <span class="result-rate-label">正答率</span>
        </div>

        <div class="result-summary">
          <div class="summary-item">
            <span>総問題数</span>
            <strong>{{ learningStore.totalQuestions }}問</strong>
          </div>
          <div class="summary-item">
            <span>解答数</span>
            <strong>{{ learningStore.answeredCount }}問</strong>
          </div>
          <div class="summary-item">
            <span>正解数</span>
            <strong>{{ learningStore.correctCount }}問</strong>
          </div>
          <div class="summary-item">
            <span>不正解数</span>
            <strong>{{ learningStore.incorrectCount }}問</strong>
          </div>
        </div>
      </template>

      <template #footer>
        <Button label="試験選択画面へ戻る" icon="pi pi-arrow-left" @click="returnToExamSelect" />
      </template>
    </Card>

    <!-- 問題演習画面 -->
    <template v-else-if="learningStore.currentQuestion">
      <header class="learning-header">
        <Button
          label="試験選択へ戻る"
          icon="pi pi-arrow-left"
          severity="secondary"
          text
          @click="returnToExamSelect"
        />
        <p class="exam-name">{{ learningStore.selectedExam?.name }}｜問題演習</p>
      </header>

      <Card class="question-card">
        <template #title>
          <div class="question-heading">
            <span>問題 {{ learningStore.currentQuestionNumber }}</span>
            <span class="question-count">
              {{ learningStore.currentQuestionNumber }} / {{ learningStore.totalQuestions }} 問
            </span>
          </div>
        </template>

        <template #content>
          <!-- 進捗バー -->
          <div class="question-progress">
            <div
              class="question-progress-bar"
              :style="{
                width: `${(learningStore.currentQuestionNumber / learningStore.totalQuestions) * 100}%`,
              }"
            ></div>
          </div>

          <!-- カテゴリ & 問題文 -->
          <p class="question-category">{{ learningStore.currentQuestion.category }}</p>
          <p class="question-text">{{ learningStore.currentQuestion.question }}</p>

          <!-- 4択の選択肢表示 -->
          <div class="option-list">
            <label
              v-for="option in learningStore.currentQuestion.options"
              :key="option.id"
              class="option-item"
              :class="{
                'option-item-selected': learningStore.selectedAnswer === option.id,
                'option-item-disabled': learningStore.isSubmitted,
              }"
            >
              <RadioButton
                :model-value="learningStore.selectedAnswer"
                :input-id="`option-${option.id}`"
                :name="String(learningStore.currentQuestion.id)"
                :value="option.id"
                :disabled="learningStore.isSubmitted"
                @update:model-value="selectAnswer"
              />
              <span class="option-id">{{ option.id }}</span>
              <span class="option-text">{{ option.text }}</span>
            </label>
          </div>

          <!-- 【解答確定後に表示されるエリア】 -->
          <section v-if="learningStore.isSubmitted" class="answer-result mt-6" aria-live="polite">
            <Tag
              :severity="learningStore.isCorrect ? 'success' : 'danger'"
              :value="learningStore.isCorrect ? '正解' : '不正解'"
            />

            <p class="correct-answer font-semibold mt-2">
              正解 <br />{{ correctAnswerOption?.id }}：{{ correctAnswerOption?.text }}
            </p>

            <!-- 任意入力項目：間違った原因 & 調査記録 -->
            <div class="memo-fields mt-4 grid gap-4">
              <div class="flex-col gap-2">
                <label for="incorrect-causes" class="font-semibold text-sm">
                  間違った原因（任意）
                </label>
                <Textarea
                  id="incorrect-causes"
                  v-model="incorrectCauses"
                  placeholder="例：言葉の意味を誤解していた、計算ミスなど"
                  rows="5"
                  fluid
                />

                <label for="investigation-records" class="font-semibold text-sm">
                  調査記録（任意）
                </label>
                <Textarea
                  id="investigation-records"
                  v-model="investigationRecords"
                  placeholder="例：ファインチューニング＝事前学習モデルに特定データを追加学習させる手法"
                  rows="5"
                  fluid
                />
              </div>
            </div>
          </section>
        </template>

        <template #footer>
          <!-- 解答前：4択選択後に押すボタン -->
          <Button
            v-if="!learningStore.isSubmitted"
            label="解答する"
            icon="pi pi-check"
            class="action-button"
            :disabled="learningStore.selectedAnswer === null"
            @click="submitAnswer"
          />

          <!-- 解答後：結果とメモを確認後に次の問題へ進むボタン -->
          <Button
            v-else
            :label="learningStore.isLastQuestion ? '演習結果を見る' : '次の問題へ'"
            icon="pi pi-arrow-right"
            icon-pos="right"
            class="action-button"
            :loading="isSaving"
            @click="handleNextQuestion"
          />
        </template>
      </Card>
    </template>
  </main>
</template>

<style scoped>
.learning-page {
  width: min(100% - 32px, 800px);
  margin: 0 auto;
  padding: 32px 0 64px;
}

.learning-header {
  margin-bottom: 20px;
}

.exam-name {
  margin: 12px 0 0;
  font-size: 1.1rem;
  font-weight: 700;
}

.question-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.question-count {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
  font-weight: 400;
}

.question-progress {
  height: 6px;
  margin-bottom: 24px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--p-surface-200);
}

.question-progress-bar {
  height: 100%;
  border-radius: inherit;
  background: var(--p-primary-color);
  transition: width 0.2s ease;
}

.question-category {
  margin-bottom: 12px;
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}

.question-text {
  margin: 0 0 28px;
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.8;
  white-space: pre-wrap;
}

.option-list {
  display: grid;
  gap: 12px;
}

.option-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--p-content-border-color);
  border-radius: 10px;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    background-color 0.2s ease;
}

.option-item-selected {
  border-color: var(--p-primary-color);
  background: var(--p-primary-50);
}

.option-item-disabled {
  cursor: default;
}

.option-id {
  flex-shrink: 0;
  font-weight: 700;
}

.option-text {
  line-height: 1.6;
}

.answer-result {
  display: grid;
  justify-items: start;
  gap: 12px;
  margin-top: 28px;
  padding: 20px;
  border-radius: 10px;
  background: var(--p-surface-50);
}

.action-button {
  width: 100%;
}

.result-card {
  margin-top: 24px;
}

.result-exam {
  color: var(--p-text-muted-color);
}

.result-rate {
  display: grid;
  justify-items: center;
  gap: 4px;
  padding: 24px 0;
}

.result-rate-value {
  color: var(--p-primary-color);
  font-size: 3rem;
  font-weight: 700;
}

.result-rate-label {
  color: var(--p-text-muted-color);
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  border-radius: 8px;
  background: var(--p-surface-50);
}

.summary-item span {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}

.summary-item strong {
  font-size: 1.2rem;
}

@media (max-width: 520px) {
  .learning-page {
    padding-top: 20px;
  }

  .question-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }

  .result-summary {
    grid-template-columns: 1fr;
  }
}
</style>
