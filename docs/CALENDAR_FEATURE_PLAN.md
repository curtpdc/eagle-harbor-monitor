# Calendar & Event Tracking Enhancement

## Overview
Add calendar functionality to track upcoming data center events and historical timeline of key developments.

## Database Schema Changes

### 1. Add Event Table

```python
# backend/app/models.py

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    event_type = Column(String(100))  # meeting, deadline, hearing, vote, protest
    event_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime)  # For multi-day events
    location = Column(String(500))
    description = Column(Text)
    article_id = Column(Integer, ForeignKey('articles.id'))
    county = Column(String(100))
    
    # Event metadata
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(200))  # e.g., "Every 2nd Tuesday"
    
    # Status tracking
    is_past = Column(Boolean, default=False)
    is_cancelled = Column(Boolean, default=False)
    
    created_date = Column(DateTime, default=func.now())
```

### 2. Update Article Model

```python
# Add to Article model
event_date = Column(DateTime, index=True)  # When the article mentions an event
```

## AI Event Extraction

Enhance `AIService.analyze_article()` to extract event dates:

```python
# backend/app/services/ai_service.py

async def extract_events(self, article_data: Dict[str, Any]) -> List[Dict]:
    """Extract event dates and details from article content"""
    
    prompt = f"""
    Extract all upcoming events, meetings, deadlines, and important dates from this article about Maryland data centers.
    
    Article Title: {article_data['title']}
    Content: {article_data['content']}
    
    Return a JSON array of events with this structure:
    [
      {{
        "title": "Planning Board Meeting on Data Center Zoning",
        "event_type": "meeting|deadline|hearing|vote|protest|announcement",
        "event_date": "2026-02-15T14:00:00",
        "end_date": "2026-02-15T17:00:00",  // optional
        "location": "Planning Board Chambers, Upper Marlboro, MD",
        "description": "Public hearing on AR/RE zone amendment for data centers",
        "county": "prince_georges|charles|both"
      }}
    ]
    
    Only include specific dates/times mentioned. Return empty array if no events found.
    """
    
    # Call Azure OpenAI to extract events
    # Parse and return structured event data
```

## API Endpoints

```python
# backend/app/api/routes.py

@router.get("/api/events/upcoming")
async def get_upcoming_events(
    days: int = 90,
    county: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get upcoming events in next N days"""
    cutoff = datetime.now() + timedelta(days=days)
    query = db.query(Event).filter(
        Event.event_date >= datetime.now(),
        Event.event_date <= cutoff,
        Event.is_cancelled == False
    )
    if county:
        query = query.filter(Event.county.in_([county, 'both']))
    
    return query.order_by(Event.event_date).all()


@router.get("/api/events/timeline")
async def get_historical_timeline(
    days: int = 180,
    db: Session = Depends(get_db)
):
    """Get timeline of past events (last 180 days)"""
    cutoff = datetime.now() - timedelta(days=days)
    events = db.query(Event).filter(
        Event.event_date >= cutoff,
        Event.event_date <= datetime.now()
    ).order_by(Event.event_date.desc()).all()
    
    return events
```

## Frontend Calendar Component

```tsx
// frontend/src/components/EventCalendar.tsx

import { useState, useEffect } from 'react';
import Calendar from 'react-calendar';

interface Event {
  id: number;
  title: string;
  event_type: string;
  event_date: string;
  location?: string;
  county: string;
}

export default function EventCalendar() {
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  
  useEffect(() => {
    fetch('/api/events/upcoming?days=90')
      .then(res => res.json())
      .then(data => setEvents(data));
  }, []);
  
  const eventsOnDate = (date: Date) => {
    return events.filter(e => 
      new Date(e.event_date).toDateString() === date.toDateString()
    );
  };
  
  return (
    <div className="calendar-container">
      <h2>📅 Upcoming Data Center Events</h2>
      
      <Calendar
        value={selectedDate}
        onChange={setSelectedDate}
        tileContent={({ date }) => {
          const dayEvents = eventsOnDate(date);
          return dayEvents.length > 0 ? (
            <div className="event-indicator">{dayEvents.length}</div>
          ) : null;
        }}
      />
      
      <div className="event-list">
        <h3>Events on {selectedDate.toLocaleDateString()}</h3>
        {eventsOnDate(selectedDate).map(event => (
          <div key={event.id} className="event-card">
            <span className="event-type">{event.event_type}</span>
            <h4>{event.title}</h4>
            <p>{event.location}</p>
            <span className="county-badge">{event.county}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Timeline View

```tsx
// frontend/src/components/Timeline.tsx

export default function Timeline() {
  const [events, setEvents] = useState([]);
  
  useEffect(() => {
    fetch('/api/events/timeline?days=180')
      .then(res => res.json())
      .then(data => setEvents(data));
  }, []);
  
  return (
    <div className="timeline">
      <h2>📊 180-Day Event Timeline</h2>
      
      <div className="timeline-container">
        {events.map(event => (
          <div key={event.id} className="timeline-event">
            <div className="timeline-date">
              {new Date(event.event_date).toLocaleDateString()}
            </div>
            <div className="timeline-content">
              <span className="event-type-badge">{event.event_type}</span>
              <h4>{event.title}</h4>
              <p>{event.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Key Events to Track

Based on your Planning Board example, the system should extract:

### Upcoming Events
- ✅ **Planning Board Meetings** (2nd & 4th Thursdays)
- ✅ **County Council Hearings** (public comment periods)
- ✅ **Zoning Amendment Deadlines** (draft language submissions)
- ✅ **Task Force Meetings** (CR-98-2025 task force)
- ✅ **Public Comment Periods** (30-60 day windows)

### Historical Timeline (Past 180 Days)
- ✅ **Jan 29, 2026**: Planning Board votes to initiate AR/RE zone amendment
- ✅ **Executive Order dates**
- ✅ **Task force formation**
- ✅ **Community protests**
- ✅ **Legislative votes**

## Implementation Steps

1. **Database Migration**:
   ```bash
   cd backend
   # Add Event model to models.py
   # Run: alembic revision --autogenerate -m "Add events table"
   # Run: alembic upgrade head
   ```

2. **Update AI Service**:
   - Add event extraction to `analyze_article()`
   - Create separate `extract_events()` method

3. **Add API Endpoints**:
   - `/api/events/upcoming`
   - `/api/events/timeline`
   - `/api/events/create` (manual entry)

4. **Frontend Components**:
   - Install `react-calendar`: `npm install react-calendar`
   - Create EventCalendar component
   - Create Timeline component
   - Add to main page

5. **Data Population**:
   - Re-analyze existing articles to extract events
   - Manually add known recurring meetings
   - Scraper auto-extracts from new articles

## Example Event Extraction

From your Planning Board article:
```json
{
  "title": "Planning Board Meeting - Data Center Zoning Amendment",
  "event_type": "meeting",
  "event_date": "2026-01-29T10:00:00",
  "location": "Planning Board Chambers, Upper Marlboro, MD",
  "description": "Planning Board votes to initiate amendment allowing qualified data centers in AR and RE zones",
  "county": "prince_georges"
}
```

Would you like me to implement this calendar system now?
