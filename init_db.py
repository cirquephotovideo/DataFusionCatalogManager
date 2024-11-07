from models.database import Base, engine

def init_database():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    print("Database initialized successfully!")
