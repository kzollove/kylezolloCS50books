import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open("books.csv")
    reader = csv.reader(f)
    #skip header line
    next(reader)

    for isbn, title, author, year in reader:


        db.execute("""INSERT INTO authors (name)
                        VALUES (:author)
                        ON CONFLICT DO NOTHING""",
                        {"author": author})

        db.execute("INSERT INTO books (title, author_id, year, isbn) VALUES (:title, (SELECT id FROM authors WHERE name=:author), :year, :isbn)", 
                        {"title": title, "author": author, "year": year, "isbn": isbn})

        print(f"Inserted {title} by {author} into database")
    db.commit()

if __name__ == "__main__":
    main()