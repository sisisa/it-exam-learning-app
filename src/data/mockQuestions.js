// 試験別の仮の問題データ
// 正式な問題データを用意したら、JSONファイルの読み込みに置き換える

export const mockQuestions = {
  'it-passport': [
    {
      id: 'ip-001',
      exam: 'it-passport',
      category: 'ストラテジ系',
      question: '企業が経営戦略を策定する主な目的として、最も適切なものはどれか。',
      options: [
        { id: 'A', text: '企業の経営目標を達成するための方針を定める' },
        { id: 'B', text: 'すべての業務を自動化する' },
        { id: 'C', text: '従業員の人数を必ず削減する' },
        { id: 'D', text: '競合他社との取引を禁止する' },
        { id: 'E', text: '情報システムの導入をなくす' },
      ],
      correctAnswer: 'A',
    },
    {
      id: 'ip-002',
      exam: 'it-passport',
      category: 'テクノロジ系',
      question: 'コンピュータの主記憶装置の説明として、最も適切なものはどれか。',
      options: [
        { id: 'A', text: 'データを長期間保存するためだけに使用する' },
        { id: 'B', text: 'CPUが処理するプログラムやデータを一時的に保持する' },
        { id: 'C', text: 'コンピュータをネットワークに接続する' },
        { id: 'D', text: '印刷する文字や画像を紙に出力する' },
        { id: 'E', text: '電源の電圧を調整する' },
      ],
      correctAnswer: 'B',
    },
  ],

  'fundamental-information': [
    {
      id: 'fe-001',
      exam: 'fundamental-information',
      category: 'テクノロジ系',
      question: '2進数の「1010」を10進数で表したものはどれか。',
      options: [
        { id: 'A', text: '8' },
        { id: 'B', text: '9' },
        { id: 'C', text: '10' },
        { id: 'D', text: '11' },
        { id: 'E', text: '12' },
      ],
      correctAnswer: 'C',
    },
    {
      id: 'fe-002',
      exam: 'fundamental-information',
      category: 'テクノロジ系',
      question: 'データベースの主キーの役割として、最も適切なものはどれか。',
      options: [
        { id: 'A', text: 'テーブルのデータを必ず暗号化する' },
        { id: 'B', text: 'レコードを一意に識別する' },
        { id: 'C', text: 'データベースのバックアップを自動作成する' },
        { id: 'D', text: 'すべての列を文字列型に変換する' },
        { id: 'E', text: 'テーブル間の結合を禁止する' },
      ],
      correctAnswer: 'B',
    },
  ],

  'applied-information': [
    {
      id: 'ap-001',
      exam: 'applied-information',
      category: 'テクノロジ系',
      question: 'システムの可用性を高める方法として、最も適切なものはどれか。',
      options: [
        { id: 'A', text: '障害発生時に備えて冗長構成を採用する' },
        { id: 'B', text: '障害発生時の記録をすべて削除する' },
        { id: 'C', text: 'システムの監視を停止する' },
        { id: 'D', text: 'バックアップを作成しない' },
        { id: 'E', text: '単一の機器にすべての処理を集中させる' },
      ],
      correctAnswer: 'A',
    },
    {
      id: 'ap-002',
      exam: 'applied-information',
      category: 'ストラテジ系',
      question: 'プロジェクトのリスク管理で行う対応として、最も適切なものはどれか。',
      options: [
        { id: 'A', text: '発生する可能性のある問題を特定し、対応策を検討する' },
        { id: 'B', text: '問題が発生するまでリスクを記録しない' },
        { id: 'C', text: 'すべてのリスクを必ずゼロにする' },
        { id: 'D', text: 'リスクの発生確率を考慮せずに対応を決める' },
        { id: 'E', text: 'リスクの情報をプロジェクトメンバーに共有しない' },
      ],
      correctAnswer: 'A',
    },
  ],
}
