import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

// 対応する試験の一覧
const EXAM_LIST = [
  {
    id: 'it-passport',
    name: 'ITパスポート',
  },
  {
    id: 'fundamental-examination',
    name: '基本情報技術者',
  },
  {
    id: 'applied-information',
    name: '応用情報技術者',
  },
]

export const useLearningStore = defineStore('learning', () => {
  // 選択中の試験ID
  const selectedExamId = ref(null)

  // 演習に使用する問題一覧
  const questions = ref([])

  // 現在の問題番号（0から開始）
  const currentQuestionIndex = ref(0)

  // 現在の問題で選択している回答
  const selectedAnswer = ref(null)

  // 回答を確定したかどうか
  const isSubmitted = ref(false)

  // 演習が完了したかどうか
  const isCompleted = ref(false)

  // 演習中の解答履歴
  const answerHistory = ref([])

  // 試験一覧を取得
  const examList = computed(() => EXAM_LIST)

  // 選択中の試験情報を取得
  const selectedExam = computed(() => {
    return EXAM_LIST.find((exam) => exam.id === selectedExamId.value) ?? null
  })

  // 現在の問題を取得
  const currentQuestion = computed(() => {
    if (isCompleted.value) {
      return null
    }

    return questions.value[currentQuestionIndex.value] ?? null
  })

  // 現在の問題番号（1から開始）
  const currentQuestionNumber = computed(() => {
    if (questions.value.length === 0) {
      return 0
    }

    return currentQuestionIndex.value + 1
  })

  // 総問題数
  const totalQuestions = computed(() => questions.value.length)

  // 最後の問題かどうか
  const isLastQuestion = computed(() => {
    return questions.value.length > 0 && currentQuestionIndex.value === questions.value.length - 1
  })

  // 現在の回答が正解かどうか
  const isCorrect = computed(() => {
    if (!isSubmitted.value || !currentQuestion.value) {
      return null
    }

    return selectedAnswer.value === currentQuestion.value.correctAnswer
  })

  // 回答済みの問題数
  const answeredCount = computed(() => answerHistory.value.length)

  // 正解数
  const correctCount = computed(() => {
    return answerHistory.value.filter((answer) => answer.isCorrect).length
  })

  // 不正解数
  const incorrectCount = computed(() => {
    return answeredCount.value - correctCount.value
  })

  // 正答率（小数点以下を四捨五入）
  const accuracyRate = computed(() => {
    if (answeredCount.value === 0) {
      return 0
    }

    return Math.round((correctCount.value / answeredCount.value) * 100)
  })

  // 試験を選択して演習を開始
  function startLearning(examId, questionList) {
    const examExists = EXAM_LIST.some((exam) => exam.id === examId)

    if (!examExists) {
      throw new Error('指定された試験が存在しません。')
    }

    if (!Array.isArray(questionList) || questionList.length === 0) {
      throw new Error('演習に使用する問題データがありません。')
    }

    // 演習状態を初期化
    selectedExamId.value = examId
    questions.value = [...questionList]
    currentQuestionIndex.value = 0
    selectedAnswer.value = null
    isSubmitted.value = false
    isCompleted.value = false
    answerHistory.value = []
    console.log('questions.value', questions.value)
  }

  // 回答を選択
  function selectAnswer(optionId) {
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

  // 回答を確定して正誤判定
  function submitAnswer() {
    if (
      isCompleted.value ||
      isSubmitted.value ||
      !currentQuestion.value ||
      selectedAnswer.value === null
    ) {
      return false
    }

    const question = currentQuestion.value

    // 選択した回答と正解を比較
    const correct = selectedAnswer.value === question.correctAnswer

    // 解答履歴に記録
    answerHistory.value.push({
      examId: selectedExamId.value,
      questionId: question.id,
      category: question.category ?? null,
      selectedAnswer: selectedAnswer.value,
      correctAnswer: question.correctAnswer,
      isCorrect: correct,
      answeredAt: new Date().toISOString(),
    })

    isSubmitted.value = true

    return true
  }

  // 次の問題へ進む
  function nextQuestion() {
    if (!isSubmitted.value || isCompleted.value) {
      return false
    }

    // 最後の問題なら演習を完了する
    if (isLastQuestion.value) {
      isCompleted.value = true
      return true
    }

    // 次の問題に進み、回答状態をリセット
    currentQuestionIndex.value += 1
    selectedAnswer.value = null
    isSubmitted.value = false

    return true
  }

  // 演習状態をリセット
  function resetLearning() {
    selectedExamId.value = null
    questions.value = []
    currentQuestionIndex.value = 0
    selectedAnswer.value = null
    isSubmitted.value = false
    isCompleted.value = false
    answerHistory.value = []
  }

  return {
    // State
    selectedExamId,
    questions,
    currentQuestionIndex,
    selectedAnswer,
    isSubmitted,
    isCompleted,
    answerHistory,

    // Getters
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

    // Actions
    startLearning,
    selectAnswer,
    submitAnswer,
    nextQuestion,
    resetLearning,
  }
})
