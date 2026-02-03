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
  category: string | null
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
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
      const response = await axios.get(`${API_URL}/articles?limit=10`)
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
    return <div className="text-center py-12">Loading latest alerts...</div>
  }

  if (error) {
    return <div className="text-center py-12 text-red-600">{error}</div>
  }

  if (articles.length === 0) {
    return (
      <div className="text-center py-12 text-gray-600">
        No articles found yet. Check back soon!
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {articles.map((article) => (
        <div key={article.id} className="bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {article.title}
              </h3>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <span>{article.source}</span>
                <span>•</span>
                <span>{formatDate(article.discovered_date)}</span>
                {article.category && (
                  <>
                    <span>•</span>
                    <span className="capitalize">{article.category}</span>
                  </>
                )}
              </div>
            </div>
            <div className="ml-4">
              {getPriorityBadge(article.priority_score)}
            </div>
          </div>
          
          {article.summary && (
            <p className="text-gray-700 mb-4">{article.summary}</p>
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
