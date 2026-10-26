<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import Button from 'primevue/button'
import Card from 'primevue/card'
import RadioButton from 'primevue/radiobutton'
import Tag from 'primevue/tag'

import { useLearningStore } from '@/stores/useLearningStore'

const route = useRoute()
const router = useRouter()
const learningStore = useLearningStore()

// 現在の問題に対応する正解の選択肢
const correctAnswerOption = computed(() => {
  const question = learningStore.currentQuestion

  if (!question) {
    return null
  }

  return question.options.find((option) => option.id === question.correctAnswer) ?? null
})

// 直接URLを開いた場合など、演習状態がない場合は試験選択画面へ戻す
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

// 回答を選択する
function selectAnswer(optionId) {
  learningStore.selectAnswer(optionId)
}

// 回答を確定する
function submitAnswer() {
  learningStore.submitAnswer()
}

// 次の問題へ進む
function nextQuestion() {
  learningStore.nextQuestion()
}

// 試験選択画面へ戻る
function returnToExamSelect() {
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
        <p class="result-exam">
          {{ learningStore.selectedExam?.name }}
        </p>

        <div class="result-rate">
          <span class="result-rate-value"> {{ learningStore.accuracyRate }}% </span>
          <span class="result-rate-label">正答率</span>
        </div>

        <div class="result-summary">
          <div class="summary-item">
            <span>総問題数</span>
            <strong>{{ learningStore.totalQuestions }}問</strong>
          </div>

          <div class="summary-item">
            <span>回答数</span>
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
          <div class="question-progress">
            <div
              class="question-progress-bar"
              :style="{
                width: `${
                  (learningStore.currentQuestionNumber / learningStore.totalQuestions) * 100
                }%`,
              }"
            ></div>
          </div>

          <p class="question-category">
            {{ learningStore.currentQuestion.category }}
          </p>

          <p class="question-text">
            {{ learningStore.currentQuestion.question }}
          </p>

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
                :name="learningStore.currentQuestion.id"
                :value="option.id"
                :disabled="learningStore.isSubmitted"
                @update:model-value="selectAnswer"
              />

              <span class="option-id">{{ option.id }}</span>
              <span class="option-text">{{ option.text }}</span>
            </label>
          </div>

          <!-- 正誤判定 -->
          <section v-if="learningStore.isSubmitted" class="answer-result" aria-live="polite">
            <Tag
              :severity="learningStore.isCorrect ? 'success' : 'danger'"
              :value="learningStore.isCorrect ? '正解' : '不正解'"
            />

            <p class="correct-answer">
              正解：{{ correctAnswerOption?.id }}
              {{ correctAnswerOption?.text }}
            </p>
          </section>
        </template>

        <template #footer>
          <Button
            v-if="!learningStore.isSubmitted"
            label="回答する"
            icon="pi pi-check"
            class="action-button"
            :disabled="learningStore.selectedAnswer === null"
            @click="submitAnswer"
          />

          <Button
            v-else
            :label="learningStore.isLastQuestion ? '演習結果を見る' : '次の問題へ'"
            icon="pi pi-arrow-right"
            icon-pos="right"
            class="action-button"
            @click="nextQuestion"
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

.correct-answer {
  margin: 0;
  line-height: 1.7;
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
