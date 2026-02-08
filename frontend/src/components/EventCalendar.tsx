'use client';

import React, { useEffect, useState } from 'react';

interface Event {
  id: number;
  title: string;
  event_type: string;
  event_date: string;
  end_date?: string;
  location?: string;
  description?: string;
  county: string;
  is_past?: boolean;
  is_cancelled?: boolean;
  article_id: number;
}

interface EventsResponse {
  events: Event[];
  count: number;
  period: string;
  as_of: string;
}

export default function EventCalendar() {
  const [upcomingEvents, setUpcomingEvents] = useState<Event[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<'upcoming' | 'timeline'>('upcoming');

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      
      // Fetch upcoming events (next 90 days)
      const upcomingRes = await fetch(`${API_BASE}/api/events/upcoming?days=90`);
      const upcomingData: EventsResponse = await upcomingRes.json();
      setUpcomingEvents(upcomingData.events);

      // Fetch timeline events (past 180 days)
      const timelineRes = await fetch(`${API_BASE}/api/events/timeline?days_back=180`);
      const timelineData: EventsResponse = await timelineRes.json();
      setTimelineEvents(timelineData.events);

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch events');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getEventTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      meeting: 'bg-blue-100 text-blue-800 border-blue-300',
      hearing: 'bg-purple-100 text-purple-800 border-purple-300',
      deadline: 'bg-red-100 text-red-800 border-red-300',
      vote: 'bg-green-100 text-green-800 border-green-300',
      protest: 'bg-orange-100 text-orange-800 border-orange-300',
      announcement: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      energy: 'bg-amber-100 text-amber-800 border-amber-300'
    };
    return colors[type] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const EventCard = ({ event, isPast = false }: { event: Event; isPast?: boolean }) => (
    <div
      className={`border-l-4 p-4 mb-4 rounded-r-lg shadow-sm ${
        getEventTypeColor(event.event_type)
      } ${isPast ? 'opacity-75' : ''}`}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-lg">{event.title}</h3>
        <span className="text-xs px-2 py-1 rounded bg-white bg-opacity-60">
          {event.event_type}
        </span>
      </div>
      
      <p className="text-sm font-medium mb-2">
        📅 {formatDate(event.event_date)}
        {event.end_date && event.end_date !== event.event_date && (
          <> to {formatDate(event.end_date)}</>
        )}
      </p>

      {event.location && (
        <p className="text-sm mb-2">
          📍 {event.location}
        </p>
      )}

      {event.description && (
        <p className="text-sm mt-2 opacity-90">{event.description}</p>
      )}

      <div className="flex gap-2 mt-3">
        <span className="text-xs px-2 py-1 rounded bg-white bg-opacity-40">
          {event.county === 'prince_georges'
            ? "Prince George's County"
            : event.county === 'charles'
            ? 'Charles County'
            : event.county === 'maryland_statewide'
            ? 'Maryland (Statewide)'
            : 'Both Counties'}
        </span>
        {isPast && <span className="text-xs px-2 py-1 rounded bg-gray-200">Past Event</span>}
        {event.is_cancelled && (
          <span className="text-xs px-2 py-1 rounded bg-red-200">Cancelled</span>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
        <p className="font-semibold">Error loading events</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-6">Data Center Events Calendar</h2>

        {/* View Toggle */}
        <div className="flex gap-2 mb-6 border-b border-gray-200">
          <button
            onClick={() => setView('upcoming')}
            className={`px-4 py-2 font-medium transition-colors ${
              view === 'upcoming'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-blue-600'
            }`}
          >
            Upcoming Events ({upcomingEvents?.length || 0})
          </button>
          <button
            onClick={() => setView('timeline')}
            className={`px-4 py-2 font-medium transition-colors ${
              view === 'timeline'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-blue-600'
            }`}
          >
            180-Day Timeline ({timelineEvents?.length || 0})
          </button>
        </div>

        {/* Events Display */}
        {view === 'upcoming' ? (
          <div>
            {upcomingEvents && upcomingEvents.length > 0 ? (
              <div>
                <p className="text-sm text-gray-600 mb-4">
                  Next 90 days of data center meetings, hearings, and deadlines
                </p>
                {upcomingEvents.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg mb-2">No upcoming events scheduled</p>
                <p className="text-sm">Check back later for new meetings and deadlines</p>
              </div>
            )}
          </div>
        ) : (
          <div>
            {timelineEvents && timelineEvents.length > 0 ? (
              <div>
                <p className="text-sm text-gray-600 mb-4">
                  Past 180 days of data center-related events
                </p>
                {timelineEvents.map((event) => (
                  <EventCard key={event.id} event={event} isPast />
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg mb-2">No events in timeline</p>
                <p className="text-sm">Events will appear here as they are tracked</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
