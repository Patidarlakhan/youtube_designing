from database import engine, Base
import models  # Ensure all models are imported

# Drop all tables
Base.metadata.drop_all(bind=engine)

# Recreate tables
Base.metadata.create_all(bind=engine)

print("Database has been reset (tables dropped and created).")

