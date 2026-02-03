'use client'

import { useState } from 'react'
import axios from 'axios'

export default function AskQuestion() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const exampleQuestions = [
    "What is the current moratorium status?",
    "When is the next Planning Board meeting?",
    "What zones are affected by the data center amendment?",
    "What is CR-98-2025?",
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return

    setLoading(true)
    setError('')
    setAnswer(null)

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
      const response = await axios.post(`${API_URL}/ask`, { question })
      setAnswer(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleExampleClick = (q: string) => {
    setQuestion(q)
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white border rounded-lg p-6 shadow-sm">
        <h2 className="text-2xl font-bold mb-4">Ask About Data Centers</h2>
        <p className="text-gray-600 mb-6">
          Get answers from our AI assistant trained on local data center news and policy.
        </p>

        <form onSubmit={handleSubmit} className="mb-6">
          <div className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-primary"
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="px-6 py-3 bg-primary text-white font-bold rounded-lg hover:bg-blue-800 transition disabled:opacity-50"
            >
              {loading ? 'Thinking...' : 'Ask'}
            </button>
          </div>
        </form>

        {/* Example Questions */}
        <div className="mb-6">
          <p className="text-sm text-gray-600 mb-2">Try these questions:</p>
          <div className="flex flex-wrap gap-2">
            {exampleQuestions.map((q, i) => (
              <button
                key={i}
                onClick={() => handleExampleClick(q)}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-sm rounded-full transition"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Answer */}
        {answer && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-bold text-lg mb-3">Answer:</h3>
            <p className="text-gray-800 whitespace-pre-wrap mb-4">{answer.answer}</p>
            
            {answer.sources && answer.sources.length > 0 && (
              <div className="mt-4 pt-4 border-t border-blue-200">
                <p className="font-semibold text-sm mb-2">Sources:</p>
                <ul className="space-y-2">
                  {answer.sources.map((source: any, i: number) => (
                    <li key={i} className="text-sm">
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        {source.title}
                      </a>
                      {source.date && (
                        <span className="text-gray-500 ml-2">
                          ({new Date(source.date).toLocaleDateString()})
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}
      </div>
    </div>
  )
}
