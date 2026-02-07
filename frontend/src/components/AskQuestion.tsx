'use client'

import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

interface Message {
  type: 'question' | 'answer' | 'error'
  content: string
  sources?: any[]
  timestamp: Date
}

export default function AskQuestion() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [typingText, setTypingText] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const exampleQuestions = [
    {
      icon: '�',
      question: "What are the latest data center developments this week?",
      category: "Latest"
    },
    {
      icon: '📋',
      question: "What is CR-98-2025 and what does the Task Force do?",
      category: "Legislation"
    },
    {
      icon: '🏗️',
      question: "What's happening with Eagle Harbor and the Chalk Point site?",
      category: "Eagle Harbor"
    },
    {
      icon: '⚡',
      question: "How will data centers impact the local power grid and water resources?",
      category: "Environment"
    },
    {
      icon: '📅',
      question: "When are the next public hearings or meetings I can attend?",
      category: "Participate"
    },
    {
      icon: '📜',
      question: "What is Executive Order 42-2025 and how does it affect our county?",
      category: "State Policy"
    },
  ]

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      })
    }
  }, [messages, loading])

  // Typing indicator effect
  useEffect(() => {
    if (!loading) {
      setTypingText('')
      return
    }

    const texts = ['Thinking', 'Thinking.', 'Thinking..', 'Thinking...']
    let index = 0
    const interval = setInterval(() => {
      setTypingText(texts[index])
      index = (index + 1) % texts.length
    }, 400)

    return () => clearInterval(interval)
  }, [loading])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || loading) return

    const userQuestion = question.trim()
    setQuestion('')
    
    // Add user question to messages
    setMessages(prev => [...prev, {
      type: 'question',
      content: userQuestion,
      timestamp: new Date()
    }])

    setLoading(true)

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      // Set timeout for the request
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 60000) // 60 second timeout
      
      const response = await axios.post(
        `${API_URL}/api/ask`, 
        { question: userQuestion },
        { 
          signal: controller.signal,
          timeout: 60000 
        }
      )
      
      clearTimeout(timeoutId)
      
      // Add AI answer to messages
      setMessages(prev => [...prev, {
        type: 'answer',
        content: response.data.answer,
        sources: response.data.sources,
        timestamp: new Date()
      }])
    } catch (err: any) {
      let errorMessage = 'Unable to get an answer. Please try again.'
      
      if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
        errorMessage = 'Request timed out. The server might be busy. Please try a simpler question or try again in a moment.'
      } else if (err.response?.status === 503) {
        errorMessage = 'Service temporarily unavailable. Please try again in a few moments.'
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      }
      
      setMessages(prev => [...prev, {
        type: 'error',
        content: errorMessage,
        timestamp: new Date()
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleExampleClick = (q: string) => {
    setQuestion(q)
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  const clearChat = () => {
    setMessages([])
    setQuestion('')
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-200">
        {/* Enhanced Header */}
        <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 text-white px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                  <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-2xl font-bold">Community Q&A Assistant</h2>
                  <p className="text-blue-100 text-sm">Powered by GPT-4o AI</p>
                </div>
              </div>
            </div>
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                className="px-4 py-2 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-lg text-sm font-semibold transition-all border border-white/30"
              >
                Clear Chat
              </button>
            )}
          </div>
        </div>

        {/* Chat Messages Area */}
        <div 
          ref={chatContainerRef} 
          className="bg-gradient-to-b from-gray-50 to-white min-h-[500px] max-h-[600px] overflow-y-auto p-6"
        >
          {messages.length === 0 ? (
            /* Welcome Screen */
            <div className="flex flex-col items-center justify-center h-full text-center py-8">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center mb-6 shadow-lg">
                <svg className="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                Ask Me Anything
              </h3>
              <p className="text-gray-600 mb-8 max-w-2xl mx-auto text-lg leading-relaxed">
                Get instant, accurate answers about data center policy, planning board decisions, 
                zoning changes, and environmental impacts. I analyze real-time government sources 
                and news to keep you informed.
              </p>
              
              <div className="w-full max-w-3xl">
                <p className="text-sm font-bold text-gray-700 mb-4 flex items-center justify-center">
                  <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Try these example questions:
                </p>
                <div className="grid gap-3">
                  {exampleQuestions.map((item, i) => (
                    <button
                      key={i}
                      onClick={() => handleExampleClick(item.question)}
                      className="group w-full text-left px-5 py-4 bg-white hover:bg-blue-50 rounded-xl transition-all border border-gray-200 hover:border-blue-300 hover:shadow-md"
                    >
                      <div className="flex items-start space-x-3">
                        <span className="text-2xl flex-shrink-0">{item.icon}</span>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-bold text-blue-600 uppercase tracking-wide">{item.category}</span>
                            <svg className="w-4 h-4 text-gray-400 group-hover:text-blue-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                          <p className="text-gray-800 font-medium text-sm">{item.question}</p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Chat Messages */
            <div className="space-y-4">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.type === 'question' ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
                  <div className={`max-w-[85%] ${
                    msg.type === 'question' 
                      ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-2xl rounded-tr-sm' 
                      : msg.type === 'error'
                      ? 'bg-red-50 text-red-900 rounded-2xl rounded-tl-sm border border-red-200'
                      : 'bg-white text-gray-800 rounded-2xl rounded-tl-sm border border-gray-200 shadow-sm'
                  } px-5 py-4`}>
                    {msg.type === 'question' ? (
                      <div>
                        <div className="flex items-center space-x-2 mb-2 opacity-90">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                          </svg>
                          <span className="text-xs font-semibold">You</span>
                        </div>
                        <p className="leading-relaxed">{msg.content}</p>
                      </div>
                    ) : msg.type === 'error' ? (
                      <div>
                        <div className="flex items-center space-x-2 mb-2">
                          <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="text-xs font-bold text-red-700">Error</span>
                        </div>
                        <p className="leading-relaxed text-sm">{msg.content}</p>
                      </div>
                    ) : (
                      <div>
                        <div className="flex items-center space-x-2 mb-3">
                          <div className="w-6 h-6 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center">
                            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                          </div>
                          <span className="text-xs font-bold text-gray-600">AI Assistant</span>
                        </div>
                        <p className="leading-relaxed text-gray-800 whitespace-pre-wrap mb-3">{msg.content}</p>
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-gray-200">
                            <p className="text-xs font-bold text-gray-600 mb-2 flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                              </svg>
                              Sources:
                            </p>
                            <ul className="space-y-2">
                              {msg.sources.map((source: any, i: number) => (
                                <li key={i} className="text-xs bg-gray-50 p-2 rounded-lg">
                                  <a
                                    href={source.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:text-blue-800 font-semibold hover:underline"
                                  >
                                    {source.title}
                                  </a>
                                  {source.date && (
                                    <span className="text-gray-500 block mt-1">
                                      {new Date(source.date).toLocaleDateString('en-US', { 
                                        year: 'numeric', 
                                        month: 'long', 
                                        day: 'numeric' 
                                      })}
                                    </span>
                                  )}
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
              
              {/* Typing Indicator */}
              {loading && (
                <div className="flex justify-start animate-fadeIn">
                  <div className="bg-white text-gray-800 rounded-2xl rounded-tl-sm border border-gray-200 shadow-sm px-5 py-4 flex items-center space-x-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-gray-600 font-medium">{typingText}</span>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Enhanced Input Area */}
        <div className="bg-white border-t border-gray-200 p-6">
          <form onSubmit={handleSubmit} className="flex items-end space-x-3">
            <div className="flex-1">
              <input
                ref={inputRef}
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about data center policy, zoning, meetings, or environmental impacts..."
                disabled={loading}
                className="w-full px-5 py-4 bg-gray-50 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-blue-500 focus:bg-white transition-all text-gray-800 placeholder-gray-400 disabled:opacity-50"
              />
            </div>
            <button
              type="submit"
              disabled={!question.trim() || loading}
              className="px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-bold rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:scale-105 active:scale-95 flex items-center space-x-2"
            >
              <span>Send</span>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </form>
          
          <p className="text-xs text-gray-500 mt-3 text-center">
            AI responses are generated based on available data and may not always be 100% accurate. Always verify with official sources for critical decisions.
          </p>
        </div>
      </div>
    </div>
  )
}
