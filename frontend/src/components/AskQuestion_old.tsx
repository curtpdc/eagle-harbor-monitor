'use client'

import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

interface Message {
  type: 'question' | 'answer'
  content: string
  sources?: any[]
  timestamp: Date
}

export default function AskQuestion() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  const exampleQuestions = [
    "What is CR-98-2025 and what does it mean?",
    "When is the next Planning Board meeting?",
    "What zones are affected by the data center amendment?",
    "What is the current Chalk Point Power Plant status?",
    "What are the environmental concerns?",
  ]

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return

    const userQuestion = question
    setQuestion('')
    
    // Add user question to messages
    setMessages(prev => [...prev, {
      type: 'question',
      content: userQuestion,
      timestamp: new Date()
    }])

    setLoading(true)
    setError('')

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await axios.post(`${API_URL}/api/ask`, { question: userQuestion })
      
      // Add AI answer to messages
      setMessages(prev => [...prev, {
        type: 'answer',
        content: response.data.answer,
        sources: response.data.sources,
        timestamp: new Date()
      }])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to get an answer. Please try again.')
      setTimeout(() => setError(''), 5000)
    } finally {
      setLoading(false)
    }
  }

  const handleExampleClick = (q: string) => {
    setQuestion(q)
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl shadow-xl overflow-hidden border border-blue-100">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary to-blue-800 text-white px-6 py-5">
          <h2 className="text-2xl font-bold mb-1">💬 Community Q&A Assistant</h2>
          <p className="text-blue-100 text-sm">
            Ask questions about data center developments in Prince George&apos;s & Charles County
          </p>
        </div>

        {/* Chat Messages Area */}
        <div ref={chatContainerRef} className="bg-white min-h-[500px] max-h-[700px] overflow-y-auto p-6 space-y-4 flex flex-col">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-12">
              <div className="text-6xl mb-4">🏢</div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">
                Welcome to Community Q&A
              </h3>
              <p className="text-gray-600 mb-8 max-w-md mx-auto leading-relaxed">
                Get instant answers about data center policy, planning board decisions, zoning changes, and environmental impacts. Our AI assistant analyzes real-time news and government sources to provide accurate, up-to-date information.
              </p>
              
              <div className="text-left w-full max-w-lg">
                <p className="text-sm font-semibold text-gray-700 mb-4">💡 Example questions to get started:</p>
                <div className="grid gap-2">
                  {exampleQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleExampleClick(q)}
                      className="w-full text-left px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 rounded-lg transition text-sm text-gray-700 border border-blue-200 hover:border-blue-300 font-medium"
                    >
                      <span className="text-primary font-bold">Q:</span> {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.type === 'question' ? 'justify-end' : 'justify-start'} mb-2`}>
                  <div className={`max-w-[85%] md:max-w-[70%] ${msg.type === 'question' ? 'bg-primary text-white rounded-3xl rounded-tr-lg' : 'bg-gray-100 text-gray-800 rounded-3xl rounded-tl-lg'} px-5 py-3 shadow-sm`}>
                    {msg.type === 'question' ? (
                      <p className="leading-relaxed text-sm md:text-base">{msg.content}</p>
                    ) : (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xl">🤖</span>
                          <span className="text-xs font-semibold text-gray-600">AI Assistant</span>
                        </div>
                        <p className="leading-relaxed text-sm md:text-base whitespace-pre-wrap">{msg.content}</p>
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-4 pt-3 border-t border-gray-300">
                            <p className="text-xs font-semibold text-gray-600 mb-2">📚 Based on sources:</p>
                            <ul className="space-y-1">
                              {msg.sources.map((source: any, i: number) => (
                                <li key={i} className="text-xs">
                                  <a
                                    href={source.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-primary hover:underline font-medium break-words"
                                  >
                                    {source.title}
                                  </a>
                                  {source.date && <span className="text-gray-500"> • {new Date(source.date).toLocaleDateString()}</span>}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start mb-2">
                  <div className="bg-gray-100 rounded-3xl rounded-tl-lg px-5 py-3 shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                      </div>
                      <span className="text-sm text-gray-600">Reading sources and thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mx-6 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm font-medium">
            ⚠️ {error}
          </div>
        )}

        {/* Input Area */}
        <div className="bg-gradient-to-r from-gray-50 to-blue-50 border-t border-gray-200 p-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about data center developments, zoning, policy..."
              className="flex-1 px-5 py-4 border-2 border-gray-300 rounded-xl focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition text-gray-800 placeholder-gray-500 text-sm md:text-base"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="px-6 md:px-8 py-4 bg-gradient-to-r from-primary to-blue-800 text-white font-bold rounded-xl hover:from-blue-800 hover:to-primary transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl text-sm md:text-base"
            >
              {loading ? (
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                'Send'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
