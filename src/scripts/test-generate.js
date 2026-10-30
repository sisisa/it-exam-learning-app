/**
 * 問題生成APIの動作テスト用スクリプト
 */
const runGenerateTest = async () => {
  console.log('Ollama (qwen3.6) による新問題の生成テストを開始します（最大3分間待ちます）...')

  // 3分（180,000ms）のタイムアウトを設定
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 180000)

  try {
    const response = await fetch('http://localhost:3000/api/ollama/generate-question', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTPステータス ${response.status}: ${errorText}`)
    }

    const result = await response.json()
    console.log('\n--- 生成された問題データ ---')
    console.log(JSON.stringify(result.data, null, 2))
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error('テスト実行エラー: 生成処理がタイムアウト（3分超過）しました。')
    } else {
      console.error('テスト実行エラー:', error.message)
    }
  }
}

runGenerateTest()
