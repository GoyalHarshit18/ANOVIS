from app.db.database import SessionLocal
from app.db.models import Base

db = SessionLocal()
for table in reversed(Base.metadata.sorted_tables):
    db.execute(table.delete())
db.commit()
db.close()
print('All rows cleared from the database successfully.')
