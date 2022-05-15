from database import Base,engine,Employee


# Only Creates DB, We Wouldnt want to create the database all the time now would we?
Base.metadata.create_all(engine)
