'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { useEffect, useState, Suspense } from 'react'
import axios from 'axios'

type Status = 'verifying' | 'success' | 'error'

function VerifyContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [status, setStatus] = useState<Status>('verifying')
  const [errorMessage, setErrorMessage] = useState('')
  const token = searchParams.get('token')

  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setStatus('error')
        setErrorMessage('No verification token found')
        return
      }

      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        await axios.get(`${API_URL}/api/verify/${token}`)
        setStatus('success')
      } catch (err: any) {
        setStatus('error')
        setErrorMessage(err.response?.data?.detail || 'Verification failed. Token may have expired.')
      }
    }

    verify()
  }, [token])

  return (
    <main className="min-h-screen bg-gradient-to-b from-green-50 to-white flex items-center justify-center p-4">
      <div className="max-w-md text-center">
        {status === 'verifying' && (
          <>
            <div className="text-6xl mb-4 animate-spin inline-block">⏳</div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Verifying Email...</h1>
            <p className="text-gray-600">Please wait while we confirm your email address.</p>
          </>
        )}

        {status === 'success' && (
          <div className="bg-white rounded-2xl shadow-xl p-8 border-2 border-green-200">
            <div className="text-6xl mb-4">✅</div>
            <h1 className="text-3xl font-bold text-green-700 mb-2">Email Verified!</h1>
            <p className="text-gray-600 mb-6 leading-relaxed">
              Thank you! You're now subscribed to real-time alerts about data center developments in Prince George's & Charles County.
            </p>
            <p className="text-sm text-gray-500 mb-8">
              You'll receive instant alerts for critical news and a comprehensive weekly digest every Friday at 3 PM.
            </p>
            <button
              onClick={() => router.push('/')}
              className="w-full px-6 py-3 bg-gradient-to-r from-primary to-blue-800 text-white font-bold rounded-lg hover:from-blue-800 hover:to-primary transition shadow-lg"
            >
              Return to Home
            </button>
            <p className="text-xs text-gray-500 mt-4">
              You can unsubscribe anytime by clicking the link in any email.
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="bg-white rounded-2xl shadow-xl p-8 border-2 border-red-200">
            <div className="text-6xl mb-4">❌</div>
            <h1 className="text-3xl font-bold text-red-700 mb-2">Verification Failed</h1>
            <p className="text-gray-600 mb-6 leading-relaxed">
              {errorMessage}
            </p>
            <p className="text-sm text-gray-600 mb-8">
              The verification link may have expired. No problem! Just subscribe again on the home page.
            </p>
            <button
              onClick={() => router.push('/')}
              className="w-full px-6 py-3 bg-gradient-to-r from-primary to-blue-800 text-white font-bold rounded-lg hover:from-blue-800 hover:to-primary transition shadow-lg"
            >
              Try Subscribing Again
            </button>
          </div>
        )}
      </div>
    </main>
  )
}

export default function VerifyPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center p-4">
        <div className="text-6xl animate-spin">⏳</div>
      </main>
    }>
      <VerifyContent />
    </Suspense>
  )
}
