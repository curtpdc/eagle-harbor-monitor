from app.database import engine
from app.models import Base

Base.metadata.create_all(bind=engine)
print('✅ Database schema updated with Event table and event_date column')
