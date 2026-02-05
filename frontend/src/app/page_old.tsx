'use client'

import { useState } from 'react'
import EmailSubscribe from '@/components/EmailSubscribe'
import LatestAlerts from '@/components/LatestAlerts'
import AskQuestion from '@/components/AskQuestion'
import EventCalendar from '@/components/EventCalendar'

export default function Home() {
  const [activeTab, setActiveTab] = useState('calendar')

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      {/* Navigation */}
      <nav className="bg-white shadow-md border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl font-bold">EH</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Eagle Harbor Monitor</h1>
                <p className="text-xs text-gray-500">Data Center Development Tracking</p>
              </div>
            </div>
            <div className="hidden md:flex items-center space-x-6">
              <a href="#alerts" className="text-gray-600 hover:text-blue-600 font-medium transition">Updates</a>
              <a href="#calendar" className="text-gray-600 hover:text-blue-600 font-medium transition">Calendar</a>
              <a href="#subscribe" className="text-gray-600 hover:text-blue-600 font-medium transition">Subscribe</a>
              <a href="#about" className="text-gray-600 hover:text-blue-600 font-medium transition">About</a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section - Modern & Professional */}
      <section id="hero" className="relative bg-gradient-to-br from-blue-700 via-indigo-800 to-purple-900 text-white py-20 overflow-hidden">
        {/* Animated background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
          }}></div>
        </div>
        
        <div className="container mx-auto px-6 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center px-4 py-2 bg-white/20 backdrop-blur-sm rounded-full border border-white/30 mb-6">
              <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
              <span className="text-sm font-semibold">Live Monitoring Active</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-extrabold mb-6 leading-tight">
              Stay Ahead of<br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-blue-300">
                Data Center Policy
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl mb-8 text-blue-100 max-w-2xl mx-auto font-light leading-relaxed">
              Track government meetings, zoning changes, and environmental reviews in <strong className="font-semibold text-white">Prince George's & Charles County, Maryland</strong>
            </p>
            
            <div id="subscribe" className="mb-6">
              <EmailSubscribe />
            </div>
            
            <div className="flex items-center justify-center space-x-8 text-sm text-blue-200">
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Free Forever
              </div>
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Real-Time Alerts
              </div>
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                AI-Powered Analysis
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section - Professional Cards */}
      <section className="bg-white py-12 shadow-sm">
        <div className="container mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 max-w-6xl mx-auto">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100 hover:shadow-lg transition">
              <div className="text-4xl font-extrabold text-blue-700 mb-2">20+</div>
              <div className="text-sm font-medium text-gray-700">Active Data Sources</div>
              <div className="text-xs text-gray-500 mt-1">News, meetings, records</div>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-100 hover:shadow-lg transition">
              <div className="text-4xl font-extrabold text-green-700 mb-2">24/7</div>
              <div className="text-sm font-medium text-gray-700">Continuous Monitoring</div>
              <div className="text-xs text-gray-500 mt-1">Always tracking updates</div>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-100 hover:shadow-lg transition">
              <div className="text-4xl font-extrabold text-purple-700 mb-2">AI</div>
              <div className="text-sm font-medium text-gray-700">Smart Analysis</div>
              <div className="text-xs text-gray-500 mt-1">GPT-4o powered insights</div>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-6 border border-orange-100 hover:shadow-lg transition">
              <div className="text-4xl font-extrabold text-orange-700 mb-2">Instant</div>
              <div className="text-sm font-medium text-gray-700">Email Notifications</div>
              <div className="text-xs text-gray-500 mt-1">Priority-based alerts</div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Tabs - Enhanced Design */}
      <section id="content" className="container mx-auto px-6 py-16 max-w-7xl">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
          {/* Tab Navigation */}
          <div className="flex border-b border-gray-200 bg-gray-50">
            <button
              onClick={() => setActiveTab('calendar')}
              className={`flex-1 px-6 py-5 font-bold text-center transition-all relative ${
                activeTab === 'calendar'
                  ? 'bg-white text-blue-700 shadow-sm'
                  : 'text-gray-600 hover:text-blue-600 hover:bg-gray-100'
              }`}
            >
              {activeTab === 'calendar' && <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-600 to-indigo-600"></div>}
              <div className="text-3xl mb-1">📅</div>
              <div className="text-sm md:text-base">Event Calendar</div>
            </button>
            <button
              onClick={() => setActiveTab('alerts')}
              className={`flex-1 px-6 py-5 font-bold text-center transition-all relative ${
                activeTab === 'alerts'
                  ? 'bg-white text-blue-700 shadow-sm'
                  : 'text-gray-600 hover:text-blue-600 hover:bg-gray-100'
              }`}
            >
              {activeTab === 'alerts' && <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-600 to-indigo-600"></div>}
              <div className="text-3xl mb-1">📰</div>
              <div className="text-sm md:text-base">Latest Updates</div>
            </button>
            <button
              onClick={() => setActiveTab('ask')}
              className={`flex-1 px-6 py-5 font-bold text-center transition-all relative ${
                activeTab === 'ask'
                  ? 'bg-white text-blue-700 shadow-sm'
                  : 'text-gray-600 hover:text-blue-600 hover:bg-gray-100'
              }`}
            >
              {activeTab === 'ask' && <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-600 to-indigo-600"></div>}
              <div className="text-3xl mb-1">💬</div>
              <div className="text-sm md:text-base">Ask AI</div>
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-8">
            {activeTab === 'calendar' && <EventCalendar />}
            {activeTab === 'alerts' && <LatestAlerts />}
            {activeTab === 'ask' && <AskQuestion />}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-gradient-to-br from-gray-50 to-blue-50 py-20 border-y-2 border-gray-200">
        <div className="container mx-auto px-4 max-w-5xl">
          <h2 className="text-4xl font-bold text-center mb-4 text-gray-900">How It Works</h2>
          <p className="text-center text-gray-600 mb-16 text-lg">
            Automated monitoring keeps our community informed and empowered
          </p>
          
          <div className="grid md:grid-cols-3 gap-12">
            <div className="text-center group">
              <div className="bg-gradient-to-br from-primary to-blue-800 text-white w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-bold mx-auto mb-6 shadow-lg group-hover:scale-110 transition-transform">
                1
              </div>
              <h3 className="font-bold text-2xl mb-3 text-gray-900">We Monitor</h3>
              <p className="text-gray-600 leading-relaxed">
                Our system continuously tracks 15+ government and news sources, 
                scanning for data center-related developments 24/7.
              </p>
            </div>
            
            <div className="text-center group">
              <div className="bg-gradient-to-br from-primary to-blue-800 text-white w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-bold mx-auto mb-6 shadow-lg group-hover:scale-110 transition-transform">
                2
              </div>
              <h3 className="font-bold text-2xl mb-3 text-gray-900">AI Analyzes</h3>
              <p className="text-gray-600 leading-relaxed">
                Advanced AI identifies critical policy changes, planning board decisions, 
                and environmental impacts affecting your community.
              </p>
            </div>
            
            <div className="text-center group">
              <div className="bg-gradient-to-br from-primary to-blue-800 text-white w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-bold mx-auto mb-6 shadow-lg group-hover:scale-110 transition-transform">
                3
              </div>
              <h3 className="font-bold text-2xl mb-3 text-gray-900">You're Alerted</h3>
              <p className="text-gray-600 leading-relaxed">
                Receive instant email alerts for critical news and comprehensive 
                weekly digests every Friday at 3 PM.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white py-16">
        <div className="container mx-auto px-4 max-w-5xl">
          <div className="text-center mb-8">
            <h3 className="font-bold text-2xl mb-3">🏢 Eagle Harbor Data Center Monitor</h3>
            <p className="text-gray-300 text-lg max-w-2xl mx-auto leading-relaxed">
              Empowering Prince George&apos;s & Charles County communities with timely, 
              accurate information about data center developments.
            </p>
          </div>
          
          <div className="border-t border-gray-700 pt-8 text-center">
            <div className="text-sm text-gray-400 space-y-2">
              <p>© 2026 Eagle Harbor Data Center Monitor. All rights reserved.</p>
              <p className="text-gray-500">
                A community service providing transparent access to public information
              </p>
            </div>
          </div>
        </div>
      </footer>
    </main>
  )
}
