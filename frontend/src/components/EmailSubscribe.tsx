'use client'

import { useState } from 'react'
import axios from 'axios'

export default function EmailSubscribe() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')
    setError('')

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await axios.post(`${API_URL}/api/subscribe`, { email })
      setMessage(response.data.message)
      setEmail('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          required
          className="flex-1 px-4 py-3 rounded-lg border-2 border-white/30 bg-white/10 text-white placeholder-white/60 focus:outline-none focus:border-white"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-8 py-3 bg-accent hover:bg-orange-600 text-white font-bold rounded-lg transition disabled:opacity-50"
        >
          {loading ? 'Subscribing...' : 'Subscribe'}
        </button>
      </form>
      
      {message && (
        <div className="mt-4 p-4 bg-green-500/20 border border-green-500 rounded-lg text-white">
          {message}
        </div>
      )}
      
      {error && (
        <div className="mt-4 p-4 bg-red-500/20 border border-red-500 rounded-lg text-white">
          {error}
        </div>
      )}
    </div>
  )
}
