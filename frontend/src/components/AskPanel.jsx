import React, { useState } from 'react'
import axios from 'axios'

function AskPanel({ language }) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)

  const handleAsk = async () => {
    if (!question.trim()) return
    setLoading(true)
    try {
      const res = await axios.post('/api/ask', { question, language })
      setAnswer(res.data.answer)
    } catch (e) {
      setAnswer('Sorry, unable to process your question right now.')
    }
    setLoading(false)
  }

  return (
    <div className="bg-maritime-700 rounded-lg p-4">
      <h2 className="text-lg font-bold mb-2 text-maritime-200">
        {language === 'hi' ? 'प्रश्न पूछें' : 'Ask ORCA'}
      </h2>
      <textarea
        className="w-full p-2 rounded bg-maritime-600 text-white text-sm border border-maritime-500 focus:outline-none focus:border-maritime-300"
        rows="3"
        placeholder={language === 'hi' ? 'जैसे, नागपट्टिनम के पास मौसम' : 'e.g., weather near Nagapattinam'}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <button
        className="mt-2 w-full bg-maritime-500 hover:bg-maritime-400 text-white font-semibold py-2 px-4 rounded transition-colors"
        onClick={handleAsk}
        disabled={loading}
      >
        {loading ? 'Processing...' : language === 'hi' ? 'पूछें' : 'Ask'}
      </button>
      {answer && (
        <div className="mt-3 p-3 bg-maritime-900/80 border border-maritime-600 rounded text-xs text-gray-200 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto font-sans shadow-inner">
          {answer}
        </div>
      )}
    </div>
  )
}

export default AskPanel
