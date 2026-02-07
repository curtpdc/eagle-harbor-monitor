'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'

interface Article {
  id: number
  title: string
  url: string
  summary: string | null
  source: string
  published_date: string | null
  discovered_date: string
  priority_score: number | null
  relevance_score: number | null
  category: string | null
  county: string | null
}

export default function LatestAlerts() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchArticles()
  }, [])

  const fetchArticles = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await axios.get(`${API_URL}/api/articles?limit=10&min_relevance=4`)
      setArticles(response.data.articles)
    } catch (err) {
      setError('Failed to load articles')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const getPriorityBadge = (priority: number | null) => {
    if (!priority) return null
    
    if (priority >= 8) {
      return <span className="bg-red-500 text-white px-3 py-1 rounded-full text-xs font-bold">CRITICAL</span>
    } else if (priority >= 6) {
      return <span className="bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-bold">HIGH</span>
    } else {
      return <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-bold">MEDIUM</span>
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent mb-4"></div>
        <p className="text-gray-600 font-medium">Loading latest updates from our community monitors...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl mb-4">⚠️</div>
        <p className="text-red-600 font-medium">{error}</p>
      </div>
    )
  }

  if (articles.length === 0) {
    return (
      <div className="text-center py-16 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border border-blue-100">
        <div className="text-6xl mb-4">📰</div>
        <h3 className="text-xl font-bold text-gray-800 mb-2">No Articles Yet</h3>
        <p className="text-gray-600 max-w-md mx-auto">
          Our monitoring system is actively tracking 15+ news sources. 
          New updates will appear here as they&apos;re discovered.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {articles.map((article) => (
        <div key={article.id} className="bg-white border-2 border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-lg hover:border-primary/30 transition-all duration-200">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-2 leading-tight hover:text-primary transition">
                {article.title}
              </h3>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <span className="font-medium text-primary">{article.source}</span>
                <span>•</span>
                <span>{formatDate(article.discovered_date)}</span>
                {article.county && article.county !== 'unclear' && (
                  <>
                    <span>•</span>
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                      {article.county === 'prince_georges' ? "Prince George's" :
                       article.county === 'charles' ? 'Charles County' :
                       article.county === 'both' ? "PG & Charles" :
                       article.county === 'maryland_statewide' ? 'Maryland' :
                       article.county}
                    </span>
                  </>
                )}
                {article.category && (
                  <>
                    <span>•</span>
                    <span className="px-2 py-1 bg-gray-100 rounded-full text-xs font-medium capitalize">{article.category}</span>
                  </>
                )}
              </div>
            </div>
            <div className="ml-4 flex-shrink-0">
              {getPriorityBadge(article.priority_score)}
            </div>
          </div>
          
          {article.summary && (
            <p className="text-gray-700 mb-4 leading-relaxed">{article.summary}</p>
          )}
          
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-800 transition"
          >
            Read Full Article →
          </a>
        </div>
      ))}
    </div>
  )
}
