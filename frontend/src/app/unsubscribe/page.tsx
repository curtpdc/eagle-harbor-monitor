'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { useEffect, useState, Suspense } from 'react'
import axios from 'axios'

type Status = 'unsubscribing' | 'success' | 'error'

function UnsubscribeContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [status, setStatus] = useState<Status>('unsubscribing')
  const [errorMessage, setErrorMessage] = useState('')
  const token = searchParams.get('token')

  useEffect(() => {
    const unsubscribe = async () => {
      if (!token) {
        setStatus('error')
        setErrorMessage('No unsubscribe token found')
        return
      }

      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        await axios.get(`${API_URL}/api/unsubscribe/${token}`)
        setStatus('success')
      } catch (err: any) {
        setStatus('error')
        setErrorMessage(err.response?.data?.detail || 'Unsubscribe failed. Token may be invalid.')
      }
    }

    unsubscribe()
  }, [token])

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center p-4">
      <div className="max-w-md text-center">
        {status === 'unsubscribing' && (
          <>
            <div className="text-6xl mb-4 animate-spin inline-block">⏳</div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Processing...</h1>
            <p className="text-gray-600">Please wait while we process your request.</p>
          </>
        )}

        {status === 'success' && (
          <div className="bg-white rounded-2xl shadow-xl p-8 border-2 border-yellow-200">
            <div className="text-6xl mb-4">👋</div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">Unsubscribed</h1>
            <p className="text-gray-600 mb-6 leading-relaxed">
              We're sorry to see you go. You've been unsubscribed from all alerts.
            </p>
            <p className="text-sm text-gray-500 mb-8">
              If you change your mind, you can always resubscribe on the home page.
            </p>
            <button
              onClick={() => router.push('/')}
              className="w-full px-6 py-3 bg-gradient-to-r from-gray-600 to-gray-800 text-white font-bold rounded-lg hover:from-gray-700 hover:to-gray-900 transition shadow-lg"
            >
              Return to Home
            </button>
            <p className="text-xs text-gray-500 mt-4">
              Thank you for being part of our community.
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="bg-white rounded-2xl shadow-xl p-8 border-2 border-red-200">
            <div className="text-6xl mb-4">⚠️</div>
            <h1 className="text-3xl font-bold text-red-700 mb-2">Error</h1>
            <p className="text-gray-600 mb-6 leading-relaxed">
              {errorMessage}
            </p>
            <p className="text-sm text-gray-600 mb-8">
              If you need help, please contact our support team.
            </p>
            <button
              onClick={() => router.push('/')}
              className="w-full px-6 py-3 bg-gradient-to-r from-primary to-blue-800 text-white font-bold rounded-lg hover:from-blue-800 hover:to-primary transition shadow-lg"
            >
              Return to Home
            </button>
          </div>
        )}
      </div>
    </main>
  )
}

export default function UnsubscribePage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center p-4">
        <div className="text-6xl animate-spin">⏳</div>
      </main>
    }>
      <UnsubscribeContent />
    </Suspense>
  )
}
