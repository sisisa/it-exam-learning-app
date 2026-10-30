import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const EXAM_LIST = [
  { id: 'it-passport', name: 'ITパスポート' },
  { id: 'fundamental-examination', name: '基本情報技術者' },
  { id: 'applied-examination', name: '応用情報技術者' },
]

export const useLearningStore = defineStore('learning', () => {
  const selectedExamId = ref(null)
  const questions = ref([])
  const currentQuestionIndex = ref(0)
  const selectedAnswer = ref(null)
  const isSubmitted = ref(false)
  const isCompleted = ref(false)
  const answerHistory = ref([])

  const examList = computed(() => EXAM_LIST)

  const selectedExam = computed(() => {
    return EXAM_LIST.find((exam) => exam.id === selectedExamId.value) ?? null
  })

  const currentQuestion = computed(() => {
    if (isCompleted.value) return null
    return questions.value[currentQuestionIndex.value] ?? null
  })

  const currentQuestionNumber = computed(() => {
    if (questions.value.length === 0) return 0
    return currentQuestionIndex.value + 1
  })

  const totalQuestions = computed(() => questions.value.length)

  const isLastQuestion = computed(() => {
    return questions.value.length > 0 && currentQuestionIndex.value === questions.value.length - 1
  })

  const isCorrect = computed(() => {
    if (!isSubmitted.value || !currentQuestion.value) return null
    return selectedAnswer.value === currentQuestion.value.correctAnswer
  })

  const answeredCount = computed(() => answerHistory.value.length)

  const correctCount = computed(() => {
    return answerHistory.value.filter((answer) => answer.isCorrect).length
  })

  const incorrectCount = computed(() => answeredCount.value - correctCount.value)

  const accuracyRate = computed(() => {
    if (answeredCount.value === 0) return 0
    return Math.round((correctCount.value / answeredCount.value) * 100)
  })

  // アロー関数：演習開始
  const startLearning = (examId, questionList) => {
    const examExists = EXAM_LIST.some((exam) => exam.id === examId)
    if (!examExists) {
      throw new Error('指定された試験が存在しません。')
    }
    if (!Array.isArray(questionList) || questionList.length === 0) {
      throw new Error('演習に使用する問題データがありません。')
    }

    selectedExamId.value = examId
    questions.value = [...questionList]
    currentQuestionIndex.value = 0
    selectedAnswer.value = null
    isSubmitted.value = false
    isCompleted.value = false
    answerHistory.value = []
  }

  // アロー関数：解答選択
  const selectAnswer = (optionId) => {
    if (isCompleted.value || isSubmitted.value || !currentQuestion.value) {
      return false
    }
    const optionExists = currentQuestion.value.options.some((option) => option.id === optionId)
    if (!optionExists) {
      return false
    }
    selectedAnswer.value = optionId
    return true
  }

  // アロー関数：解答確定（画面を正誤判定表示フラグONにする）
  const submitAnswer = () => {
    if (
      isCompleted.value ||
      isSubmitted.value ||
      !currentQuestion.value ||
      selectedAnswer.value === null
    ) {
      return false
    }

    isSubmitted.value = true
    return true
  }

  // アロー関数：解答記録をストアの履歴に追加（任意入力項目を含む）
  const recordAnswer = (additionalData = {}) => {
    if (!currentQuestion.value || selectedAnswer.value === null) {
      return null
    }

    const question = currentQuestion.value
    const correct = selectedAnswer.value === question.correctAnswer

    const record = {
      examId: selectedExamId.value,
      questionId: question.id,
      category: question.category ?? null,
      selectedAnswer: selectedAnswer.value,
      correctAnswer: question.correctAnswer,
      isCorrect: correct,
      incorrect_causes: additionalData.incorrect_causes || '',
      investigation_records: additionalData.investigation_records || '',
      answeredAt: new Date().toISOString(),
    }

    answerHistory.value.push(record)
    return record
  }

  // アロー関数：次の問題へ進む
  const nextQuestion = () => {
    if (!isSubmitted.value || isCompleted.value) return false

    if (isLastQuestion.value) {
      isCompleted.value = true
      return true
    }

    currentQuestionIndex.value += 1
    selectedAnswer.value = null
    isSubmitted.value = false
    return true
  }

  // アロー関数：状態リセット
  const resetLearning = () => {
    selectedExamId.value = null
    questions.value = []
    currentQuestionIndex.value = 0
    selectedAnswer.value = null
    isSubmitted.value = false
    isCompleted.value = false
    answerHistory.value = []
  }

  return {
    selectedExamId,
    questions,
    currentQuestionIndex,
    selectedAnswer,
    isSubmitted,
    isCompleted,
    answerHistory,
    examList,
    selectedExam,
    currentQuestion,
    currentQuestionNumber,
    totalQuestions,
    isLastQuestion,
    isCorrect,
    answeredCount,
    correctCount,
    incorrectCount,
    accuracyRate,
    startLearning,
    selectAnswer,
    submitAnswer,
    recordAnswer,
    nextQuestion,
    resetLearning,
  }
})
