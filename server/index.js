import express from 'express'
import fs from 'fs'
import path from 'path'

const app = express()
const PORT = process.env.PORT || 3000

app.use(express.json())

// 試験IDに対応する保存先ファイルの相対パス設定
const EXAM_FILE_PATHS = {
  'fundamental-examination': 'data/fe/answers.json',
  'applied-information': 'data/ap/answers.json',
  'it-passport': 'data/it/answers.json',
}

/**
 * 試験IDから絶対パスを取得するアロー関数
 */
const getFilePath = (examId) => {
  const relativePath = EXAM_FILE_PATHS[examId]
  if (!relativePath) return null
  return path.join(process.cwd(), relativePath)
}

/**
 * 解答保存 API (POST /api/answers)
 */
app.post('/api/answers', (req, res) => {
  const { examId, answerData } = req.body

  if (!examId || !answerData) {
    return res.status(400).json({
      success: false,
      message: 'examId および answerData が指定されていません。',
    })
  }

  const filePath = getFilePath(examId)
  if (!filePath) {
    return res.status(400).json({
      success: false,
      message: `未対応の試験IDです: ${examId}`,
    })
  }

  const dirPath = path.dirname(filePath)

  try {
    // 保存先ディレクトリが存在しない場合は自動作成
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true })
    }

    // 既存の解答データを読み込み
    let currentAnswers = []
    if (fs.existsSync(filePath)) {
      const fileContent = fs.readFileSync(filePath, 'utf-8').trim()
      currentAnswers = fileContent ? JSON.parse(fileContent) : []
    }

    // 新規データを追加
    currentAnswers.push(answerData)

    // JSONファイルにインデント整形して上書き保存
    fs.writeFileSync(filePath, JSON.stringify(currentAnswers, null, 2), 'utf-8')

    return res.status(200).json({
      success: true,
      message: `${examId} の answers.json に正常に保存されました。`,
    })
  } catch (error) {
    console.error('解答データ保存エラー:', error)
    return res.status(500).json({
      success: false,
      message: 'answers.json の保存処理中にエラーが発生しました。',
      error: error.message,
    })
  }
})

app.listen(PORT, () => {
  console.log(`[Express Server] http://localhost:${PORT} で起動中`)
})

/**
 * Ollama 連携エンドポイント
 */
app.post('/api/ollama/chat', async (req, res) => {
  const { prompt, systemPrompt } = req.body

  try {
    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'qwen3.6',
        prompt: prompt,
        system: systemPrompt || 'あなたはIT資格試験の学習を支援する高度なAIアシスタントです。',
        stream: false,
      }),
    })

    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.status}`)
    }

    const data = await response.json()
    return res.json({ response: data.response })
  } catch (error) {
    console.error('Ollama連携エラー:', error)
    return res.status(500).json({
      error: 'Ollamaとの連携に失敗しました。',
      details: error.message,
    })
  }
})

/**
 * テスト用:Ollama (qwen2.5:1.5b) を用いた基本情報技術者試験の問題生成API
 */
app.post('/api/ollama/generate-question', async (req, res) => {
  try {
    const feQuestionsPath = path.join(process.cwd(), 'data/fe/questions.json')
    const feAnswersPath = path.join(process.cwd(), 'data/fe/answers.json')

    // 既存問題データの読み込み（サンプル構造参照用）
    let sampleQuestion = {}
    if (fs.existsSync(feQuestionsPath)) {
      const questionsData = JSON.parse(fs.readFileSync(feQuestionsPath, 'utf-8'))
      if (questionsData.length > 0) {
        sampleQuestion = questionsData[0]
      }
    }

    // 解答履歴の読み込み（弱点・メモの抽出）
    let weaknesses = []
    if (fs.existsSync(feAnswersPath)) {
      const answersData = JSON.parse(fs.readFileSync(feAnswersPath, 'utf-8'))
      // 不正解データから間違えた原因や調査記録を取得
      weaknesses = answersData
        .filter((item) => !item.isCorrect)
        .map((item) => ({
          category: item.category,
          incorrect_causes: item.incorrect_causes,
          investigation_records: item.investigation_records,
        }))
        .filter((item) => item.incorrect_causes || item.investigation_records)
    }

    // Ollamaへ送るシステムプロンプト・ユーザープロンプトの構築
    const systemPrompt = `あなたは基本情報技術者試験（FE）の出題委員です。
    指定されたJSONフォーマットに厳格に従い、新しい四肢択一問題を1問作成してJSONのみを出力してください。`

    const userPrompt = `
    【出力フォーマット】
    ${JSON.stringify(sampleQuestion, null, 2)}

    【ユーザーの苦手傾向・学習メモ】
    ${JSON.stringify(weaknesses.slice(-3), null, 2)}

    【指示】
    ユーザーの苦手傾向や学習メモを参考にして、基本情報技術者試験（fundamental-examination）の新しいオリジナル問題を1問作成してください。
    `

    // Ollama API の呼び出し
    const ollamaResponse = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'qwen2.5:1.5b', // 最軽量モデルを適用してテストしている
        prompt: userPrompt,
        system: systemPrompt,
        stream: false,
        options: {
          num_ctx: 1024, // コンテキスト文脈を1024トークンに縮小（メモリ消費を最小化）
          num_predict: 400, // 出力最大トークン数を制限（生成時間を数秒程度に短縮）
          temperature: 0.5, // ランダム性を抑えてフォーマット崩れを防止
        },
      }),
    })

    if (!ollamaResponse.ok) {
      throw new Error(`Ollama応答エラー: ${ollamaResponse.status}`)
    }

    const responseData = await ollamaResponse.json()
    const rawText = responseData.response.trim()

    // JSON文字列のクリーニングとパース
    const cleanJsonText = rawText.replace(/^```json\s*/, '').replace(/\s*```$/, '')
    const generatedQuestion = JSON.parse(cleanJsonText)

    return res.status(200).json({
      success: true,
      data: generatedQuestion,
    })
  } catch (error) {
    console.error('問題生成エラー:', error)
    return res.status(500).json({
      success: false,
      message: '問題生成処理に失敗しました。',
      error: error.message,
    })
  }
})
