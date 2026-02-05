'use client'

import { useState } from 'react'
import EmailSubscribe from '@/components/EmailSubscribe'
import LatestAlerts from '@/components/LatestAlerts'
import AskQuestion from '@/components/AskQuestion'
import EventCalendar from '@/components/EventCalendar'

export default function Home() {
  const [activeTab, setActiveTab] = useState('calendar')

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Professional Navigation Bar */}
      <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50 backdrop-blur-lg bg-white/95">
        <div className="container mx-auto px-4 lg:px-6">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Brand */}
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 rounded-xl flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900 leading-tight">Eagle Harbor Monitor</h1>
                <p className="text-xs text-gray-500 leading-tight">Community Data Center Oversight</p>
              </div>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <a href="#updates" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors">Updates</a>
              <a href="#calendar" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors">Calendar</a>
              <a href="#ask" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors">Ask AI</a>
              <a href="#about" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors">About</a>
              <a 
                href="#subscribe" 
                className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-all hover:shadow-md"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Subscribe
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section - Community Leadership Portal */}
      <section className="relative bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 text-white overflow-hidden">
        {/* Animated Grid Background */}
        <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:32px_32px]"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 to-transparent"></div>
        
        <div className="relative container mx-auto px-4 lg:px-6 py-16 lg:py-24">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Column: Value Proposition */}
            <div>
              <div className="inline-flex items-center px-4 py-2 bg-blue-500/20 backdrop-blur-sm rounded-full border border-blue-400/30 mb-6">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                <span className="text-sm font-semibold text-blue-100">Live Community Monitoring</span>
              </div>
              
              <h1 className="text-4xl lg:text-6xl font-extrabold mb-6 leading-tight">
                Empowering Our<br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-300 via-cyan-300 to-teal-300">
                  Community Leadership
                </span>
              </h1>
              
              <p className="text-xl text-blue-100 mb-8 leading-relaxed max-w-xl">
                Real-time tracking of data center developments, zoning changes, and policy decisions in 
                <strong className="text-white font-semibold"> Prince George's & Charles County, Maryland</strong>.
              </p>

              {/* Key Features */}
              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="flex items-start space-x-3">
                  <svg className="w-6 h-6 text-green-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <h3 className="font-bold text-white">24/7 Monitoring</h3>
                    <p className="text-sm text-blue-200">15+ sources tracked</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <svg className="w-6 h-6 text-green-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <h3 className="font-bold text-white">AI Analysis</h3>
                    <p className="text-sm text-blue-200">Instant insights</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <svg className="w-6 h-6 text-green-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <h3 className="font-bold text-white">Email Alerts</h3>
                    <p className="text-sm text-blue-200">Priority-based</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <svg className="w-6 h-6 text-green-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <h3 className="font-bold text-white">Free Forever</h3>
                    <p className="text-sm text-blue-200">Community service</p>
                  </div>
                </div>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4">
                <a 
                  href="#subscribe" 
                  className="inline-flex items-center justify-center px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Get Email Alerts
                </a>
                <a 
                  href="#ask" 
                  className="inline-flex items-center justify-center px-8 py-4 bg-white/10 backdrop-blur-sm hover:bg-white/20 text-white font-bold rounded-xl border border-white/30 transition-all"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  Ask AI Assistant
                </a>
              </div>
            </div>

            {/* Right Column: Subscription Form */}
            <div id="subscribe" className="bg-white/10 backdrop-blur-lg rounded-2xl border border-white/20 p-8 shadow-2xl">
              <EmailSubscribe />
            </div>
          </div>
        </div>
      </section>

      {/* Impact Stats */}
      <section className="bg-white py-12 border-b">
        <div className="container mx-auto px-4 lg:px-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-4xl lg:text-5xl font-black text-blue-600 mb-2">20+</div>
              <div className="text-sm font-semibold text-gray-700">Data Sources</div>
              <div className="text-xs text-gray-500 mt-1">News & Government</div>
            </div>
            <div className="text-center">
              <div className="text-4xl lg:text-5xl font-black text-green-600 mb-2">24/7</div>
              <div className="text-sm font-semibold text-gray-700">Monitoring</div>
              <div className="text-xs text-gray-500 mt-1">Continuous Tracking</div>
            </div>
            <div className="text-center">
              <div className="text-4xl lg:text-5xl font-black text-purple-600 mb-2">AI</div>
              <div className="text-sm font-semibold text-gray-700">Powered</div>
              <div className="text-xs text-gray-500 mt-1">GPT-4o Analysis</div>
            </div>
            <div className="text-center">
              <div className="text-4xl lg:text-5xl font-black text-orange-600 mb-2">Free</div>
              <div className="text-sm font-semibold text-gray-700">Community</div>
              <div className="text-xs text-gray-500 mt-1">Public Service</div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Tabs */}
      <section id="content" className="container mx-auto px-4 lg:px-6 py-12 lg:py-16">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
          {/* Modern Tab Navigation */}
          <div className="flex border-b border-gray-200 overflow-x-auto">
            <button
              onClick={() => setActiveTab('calendar')}
              className={`flex-1 min-w-[140px] px-6 py-4 font-bold text-sm lg:text-base transition-all relative ${
                activeTab === 'calendar'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'bg-gray-50 text-gray-600 hover:text-blue-600 hover:bg-gray-100'
              }`}
            >
              {activeTab === 'calendar' && <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-600"></div>}
              <div className="text-2xl mb-1">📅</div>
              <div>Event Calendar</div>
            </button>
            <button
              onClick={() => setActiveTab('alerts')}
              className={`flex-1 min-w-[140px] px-6 py-4 font-bold text-sm lg:text-base transition-all relative ${
                activeTab === 'alerts'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'bg-gray-50 text-gray-600 hover:text-blue-600 hover:bg-gray-100'
              }`}
            >
              {activeTab === 'alerts' && <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-600"></div>}
              <div className="text-2xl mb-1">📰</div>
              <div>Latest Updates</div>
            </button>
            <button
              onClick={() => setActiveTab('ask')}
              className={`flex-1 min-w-[140px] px-6 py-4 font-bold text-sm lg:text-base transition-all relative ${
                activeTab === 'ask'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'bg-gray-50 text-gray-600 hover:text-blue-600 hover:bg-gray-100'
              }`}
            >
              {activeTab === 'ask' && <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-600"></div>}
              <div className="text-2xl mb-1">💬</div>
              <div>Ask AI</div>
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-6 lg:p-8">
            {activeTab === 'calendar' && <EventCalendar />}
            {activeTab === 'alerts' && <LatestAlerts />}
            {activeTab === 'ask' && <AskQuestion />}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="about" className="bg-gradient-to-br from-gray-50 to-blue-50 py-16 lg:py-24 border-y">
        <div className="container mx-auto px-4 lg:px-6">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl lg:text-5xl font-extrabold text-gray-900 mb-4">How It Works</h2>
              <p className="text-lg lg:text-xl text-gray-600 max-w-3xl mx-auto">
                Automated monitoring keeps our community informed and empowered
              </p>
            </div>
            
            <div className="grid lg:grid-cols-3 gap-12">
              <div className="text-center group">
                <div className="bg-gradient-to-br from-blue-600 to-blue-800 text-white w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-black mx-auto mb-6 shadow-xl group-hover:scale-110 transition-transform">
                  1
                </div>
                <h3 className="font-bold text-2xl mb-4 text-gray-900">We Monitor</h3>
                <p className="text-gray-600 leading-relaxed">
                  Our system continuously tracks 15+ government and news sources, 
                  scanning for data center-related developments 24/7.
                </p>
              </div>
              
              <div className="text-center group">
                <div className="bg-gradient-to-br from-blue-600 to-blue-800 text-white w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-black mx-auto mb-6 shadow-xl group-hover:scale-110 transition-transform">
                  2
                </div>
                <h3 className="font-bold text-2xl mb-4 text-gray-900">AI Analyzes</h3>
                <p className="text-gray-600 leading-relaxed">
                  Advanced AI identifies critical policy changes, planning board decisions, 
                  and environmental impacts affecting your community.
                </p>
              </div>
              
              <div className="text-center group">
                <div className="bg-gradient-to-br from-blue-600 to-blue-800 text-white w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-black mx-auto mb-6 shadow-xl group-hover:scale-110 transition-transform">
                  3
                </div>
                <h3 className="font-bold text-2xl mb-4 text-gray-900">You Stay Informed</h3>
                <p className="text-gray-600 leading-relaxed">
                  Receive instant email alerts for urgent updates, weekly digests, 
                  and on-demand insights through our AI assistant.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12 border-t border-gray-800">
        <div className="container mx-auto px-4 lg:px-6">
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            <div>
              <h3 className="text-white font-bold text-lg mb-4">Eagle Harbor Monitor</h3>
              <p className="text-sm leading-relaxed">
                Empowering community leadership through transparent, real-time monitoring of data center developments in Prince George's & Charles County, Maryland.
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
              <p className="text-sm mb-4">
                Questions or feedback? We'd love to hear from you.
              </p>
              <a href="mailto:info@eagleharbormonitor.org" className="inline-flex items-center text-blue-400 hover:text-blue-300 transition text-sm font-semibold">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                info@eagleharbormonitor.org
              </a>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm">
            <p>&copy; 2026 Eagle Harbor Monitor. All rights reserved. A community service initiative.</p>
          </div>
        </div>
      </footer>
    </main>
  )
}
