'use client'

import { useState } from 'react'
import EmailSubscribe from '@/components/EmailSubscribe'
import LatestAlerts from '@/components/LatestAlerts'
import AskQuestion from '@/components/AskQuestion'

export default function Home() {
  const [activeTab, setActiveTab] = useState('alerts')

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary via-blue-800 to-indigo-900 text-white py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDE2YzAtMS4xMDUtLjg5NS0yLTItMnMtMiAuODk1LTIgMiAuODk1IDIgMiAyIDItLjg5NSAyLTJ6bS0yIDIwYy0xLjEwNSAwLTIgLjg5NS0yIDJzLjg5NSAyIDIgMiAyLS44OTUgMi0yLS44OTUtMi0yLTJ6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-20"></div>
        <div className="container mx-auto px-4 max-w-5xl text-center relative z-10">
          <div className="inline-block mb-4 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full border border-white/20">
            <span className="text-sm font-semibold">🏢 Community Data Center Monitor</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Stay Informed About<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-200 to-cyan-200">
              Data Center Developments
            </span>
          </h1>
          <p className="text-xl md:text-2xl mb-10 text-blue-100 max-w-3xl mx-auto leading-relaxed">
            Free, real-time alerts about government meetings, policy changes, and environmental 
            impacts affecting Prince George&apos;s & Charles County communities.
          </p>
          <EmailSubscribe />
          <p className="mt-6 text-sm text-blue-200">
            Join concerned citizens monitoring data center expansion in our region
          </p>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="bg-white border-b-2 border-gray-200 shadow-sm">
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="text-4xl font-bold bg-gradient-to-r from-primary to-blue-800 text-transparent bg-clip-text mb-1">15+</div>
              <div className="text-sm text-gray-600 font-medium">News Sources</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold bg-gradient-to-r from-primary to-blue-800 text-transparent bg-clip-text mb-1">24/7</div>
              <div className="text-sm text-gray-600 font-medium">Active Monitoring</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold bg-gradient-to-r from-primary to-blue-800 text-transparent bg-clip-text mb-1">Real-Time</div>
              <div className="text-sm text-gray-600 font-medium">Email Alerts</div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="container mx-auto px-4 py-16 max-w-6xl">
        {/* Tabs */}
        <div className="flex space-x-2 border-b-2 border-gray-200 mb-10">
          <button
            onClick={() => setActiveTab('alerts')}
            className={`px-8 py-4 font-bold transition-all rounded-t-lg ${
              activeTab === 'alerts'
                ? 'bg-primary text-white shadow-lg -mb-0.5 border-b-2 border-primary'
                : 'text-gray-600 hover:text-primary hover:bg-gray-50'
            }`}
          >
            📰 Latest Updates
          </button>
          <button
            onClick={() => setActiveTab('ask')}
            className={`px-8 py-4 font-bold transition-all rounded-t-lg ${
              activeTab === 'ask'
                ? 'bg-primary text-white shadow-lg -mb-0.5 border-b-2 border-primary'
                : 'text-gray-600 hover:text-primary hover:bg-gray-50'
            }`}
          >
            💬 Ask Questions
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'alerts' && <LatestAlerts />}
        {activeTab === 'ask' && <AskQuestion />}
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
