'use client'

import { useState } from 'react'
import EmailSubscribe from '@/components/EmailSubscribe'
import LatestAlerts from '@/components/LatestAlerts'
import AskQuestion from '@/components/AskQuestion'

export default function Home() {
  const [activeTab, setActiveTab] = useState('alerts')

  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-primary to-blue-900 text-white py-20">
        <div className="container mx-auto px-4 max-w-4xl text-center">
          <h1 className="text-5xl font-bold mb-6">
            Stay Informed About Data Centers<br />
            in Prince George&apos;s County
          </h1>
          <p className="text-xl mb-8 opacity-90">
            Free alerts when government meetings, policy changes, or environmental impacts affect your community.
          </p>
          <EmailSubscribe />
        </div>
      </section>

      {/* Stats Bar */}
      <section className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex justify-around max-w-4xl mx-auto">
            <div className="text-center">
              <div className="text-3xl font-bold text-primary">15+</div>
              <div className="text-sm text-gray-600">Sources Monitored</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-primary">24/7</div>
              <div className="text-sm text-gray-600">Monitoring</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-primary">Instant</div>
              <div className="text-sm text-gray-600">Alerts</div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="container mx-auto px-4 py-12 max-w-6xl">
        {/* Tabs */}
        <div className="flex space-x-4 border-b mb-8">
          <button
            onClick={() => setActiveTab('alerts')}
            className={`px-6 py-3 font-semibold transition ${
              activeTab === 'alerts'
                ? 'border-b-4 border-primary text-primary'
                : 'text-gray-600 hover:text-primary'
            }`}
          >
            Latest Alerts
          </button>
          <button
            onClick={() => setActiveTab('ask')}
            className={`px-6 py-3 font-semibold transition ${
              activeTab === 'ask'
                ? 'border-b-4 border-primary text-primary'
                : 'text-gray-600 hover:text-primary'
            }`}
          >
            Ask Questions
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'alerts' && <LatestAlerts />}
        {activeTab === 'ask' && <AskQuestion />}
      </section>

      {/* How It Works */}
      <section className="bg-gray-50 py-16">
        <div className="container mx-auto px-4 max-w-4xl">
          <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-primary text-white w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                1
              </div>
              <h3 className="font-bold text-xl mb-2">We Monitor</h3>
              <p className="text-gray-600">
                Our system continuously scrapes 15+ government and news sources for data center information.
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-primary text-white w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                2
              </div>
              <h3 className="font-bold text-xl mb-2">AI Analyzes</h3>
              <p className="text-gray-600">
                Advanced AI identifies critical policy changes, votes, and environmental impacts.
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-primary text-white w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                3
              </div>
              <h3 className="font-bold text-xl mb-2">You&apos;re Alerted</h3>
              <p className="text-gray-600">
                Get instant email alerts for critical news and a weekly digest every Friday.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4 max-w-4xl text-center">
          <h3 className="font-bold text-xl mb-4">Eagle Harbor Data Center Monitor</h3>
          <p className="text-gray-400 mb-6">
            Empowering communities with timely information about data center developments.
          </p>
          <div className="text-sm text-gray-500">
            <p>© 2026 Eagle Harbor Data Center Monitor. All rights reserved.</p>
            <p className="mt-2">
              <a href="/about" className="hover:text-white">About</a>
              {' • '}
              <a href="/privacy" className="hover:text-white">Privacy Policy</a>
            </p>
          </div>
        </div>
      </footer>
    </main>
  )
}
