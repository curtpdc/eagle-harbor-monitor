'use client'

import { useState } from 'react'
import EmailSubscribe from '@/components/EmailSubscribe'
import LatestAlerts from '@/components/LatestAlerts'
import AskQuestion from '@/components/AskQuestion'
import EventCalendar from '@/components/EventCalendar'

export default function Home() {
  const [activeTab, setActiveTab] = useState('calendar')

  return (
    <main className="min-h-screen bg-white">
      {/* Clean, Professional Navigation */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex items-center justify-between h-20">
            {/* Logo & Brand */}
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Eagle Harbor Monitor</h1>
                <p className="text-sm text-gray-600">Prince George's & Charles County, MD</p>
              </div>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-6">
              <a href="#updates" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">Updates</a>
              <a href="#calendar" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">Calendar</a>
              <a href="#ask" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">Ask AI</a>
              <a 
                href="#subscribe" 
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-md hover:shadow-lg transition-all"
              >
                Get Alerts
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section - Bold & Clear */}
      <section className="bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white py-24">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="max-w-5xl mx-auto">
            {/* Main Heading */}
            <div className="text-center mb-12">
              <div className="inline-flex items-center px-4 py-2 bg-white/20 rounded-full mb-6">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                <span className="text-sm font-semibold">Live Monitoring Active</span>
              </div>
              
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold mb-6 leading-tight">
                Track Data Center<br/>
                Developments in Your<br/>
                <span className="text-blue-200">Community</span>
              </h1>
              
              <p className="text-xl md:text-2xl text-blue-100 mb-10 max-w-3xl mx-auto leading-relaxed">
                Real-time monitoring of zoning changes, planning board meetings, and environmental reviews 
                in <strong className="text-white">Prince George's & Charles County, Maryland</strong>
              </p>

              {/* Email Subscription */}
              <div id="subscribe" className="max-w-2xl mx-auto mb-8">
                <EmailSubscribe />
              </div>

              <p className="text-sm text-blue-200">
                ✓ Free Forever &nbsp;•&nbsp; ✓ Instant Alerts &nbsp;•&nbsp; ✓ AI-Powered Analysis
              </p>
            </div>

            {/* Key Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16">
              <div className="text-center">
                <div className="text-4xl font-bold mb-2">20+</div>
                <div className="text-sm text-blue-200">Data Sources</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold mb-2">24/7</div>
                <div className="text-sm text-blue-200">Monitoring</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold mb-2">AI</div>
                <div className="text-sm text-blue-200">Powered</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold mb-2">Free</div>
                <div className="text-sm text-blue-200">Community Service</div>
              </div>
            </div>
          </div>
        </div>
      </section>



      {/* Main Content Section */}
      <section className="bg-gray-50 py-16">
        <div className="container mx-auto px-4 lg:px-8">
          {/* Modern Tab Navigation */}
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden max-w-6xl mx-auto">
            <div className="border-b border-gray-200">
              <div className="flex">
                <button
                  onClick={() => setActiveTab('calendar')}
                  className={`flex-1 px-6 py-5 font-semibold transition-all ${
                    activeTab === 'calendar'
                      ? 'bg-blue-50 text-blue-700 border-b-4 border-blue-600'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <div className="text-3xl mb-1">📅</div>
                  <div>Event Calendar</div>
                </button>
                <button
                  onClick={() => setActiveTab('alerts')}
                  className={`flex-1 px-6 py-5 font-semibold transition-all ${
                    activeTab === 'alerts'
                      ? 'bg-blue-50 text-blue-700 border-b-4 border-blue-600'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <div className="text-3xl mb-1">📰</div>
                  <div>Latest Updates</div>
                </button>
                <button
                  onClick={() => setActiveTab('ask')}
                  className={`flex-1 px-6 py-5 font-semibold transition-all ${
                    activeTab === 'ask'
                      ? 'bg-blue-50 text-blue-700 border-b-4 border-blue-600'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <div className="text-3xl mb-1">💬</div>
                  <div>Ask AI</div>
                </button>
              </div>
            </div>

            {/* Tab Content */}
            <div className="p-8">
              {activeTab === 'calendar' && <EventCalendar />}
              {activeTab === 'alerts' && <LatestAlerts />}
              {activeTab === 'ask' && <AskQuestion />}
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-white py-20 border-t">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl lg:text-5xl font-extrabold text-gray-900 mb-4">How It Works</h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Automated monitoring keeps our community informed
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-12">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-600 text-white rounded-2xl flex items-center justify-center text-3xl font-black mx-auto mb-6 shadow-lg">
                  1
                </div>
                <h3 className="font-bold text-2xl mb-4 text-gray-900">We Monitor</h3>
                <p className="text-gray-600 leading-relaxed">
                  Our system continuously tracks 20+ government and news sources for data center developments.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-600 text-white rounded-2xl flex items-center justify-center text-3xl font-black mx-auto mb-6 shadow-lg">
                  2
                </div>
                <h3 className="font-bold text-2xl mb-4 text-gray-900">AI Analyzes</h3>
                <p className="text-gray-600 leading-relaxed">
                  Advanced AI identifies critical policy changes, planning decisions, and environmental impacts.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-600 text-white rounded-2xl flex items-center justify-center text-3xl font-black mx-auto mb-6 shadow-lg">
                  3
                </div>
                <h3 className="font-bold text-2xl mb-4 text-gray-900">You're Informed</h3>
                <p className="text-gray-600 leading-relaxed">
                  Receive instant email alerts and access on-demand insights through our AI assistant.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            <div>
              <h3 className="text-white font-bold text-lg mb-4">Eagle Harbor Monitor</h3>
              <p className="text-sm leading-relaxed">
                Empowering community leadership through transparent monitoring of data center developments in Prince George's & Charles County, Maryland.
              </p>
            </div>
            <div>
              <h3 className="text-white font-bold text-lg mb-4">Resources</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#updates" className="hover:text-white transition">Latest Updates</a></li>
                <li><a href="#calendar" className="hover:text-white transition">Event Calendar</a></li>
                <li><a href="#ask" className="hover:text-white transition">AI Assistant</a></li>
                <li><a href="#subscribe" className="hover:text-white transition">Subscribe</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-white font-bold text-lg mb-4">Contact</h3>
              <a href="mailto:info@eagleharbormonitor.org" className="text-blue-400 hover:text-blue-300 transition text-sm">
                info@eagleharbormonitor.org
              </a>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm">
            <p>&copy; 2026 Eagle Harbor Monitor. Free community service.</p>
          </div>
        </div>
      </footer>
    </main>
  )
}
