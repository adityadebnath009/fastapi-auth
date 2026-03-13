from database.connection import SessionLocal

def get_db():

    db = SessionLocal() #creates a new database session.

    try:
        yield db
    finally:
        db.close() #closes the session
#                   returns connection to pool

# SessionLocal() takes a connection from the pool
#
# Your API uses it
#
# db.close() returns the connection back to the pool