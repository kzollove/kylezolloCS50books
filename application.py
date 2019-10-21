import os
import requests

from flask import Flask, session, render_template, redirect, request, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from ast import literal_eval

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#######   KEY: J7hfLkKaYDCxKsASYaFQAA #######


####### SUB PROGRAMS ############
#Queries database. Takes a dictionary of submitted parameters
def booksearch(bookQuery):
    books = db.execute("""SELECT title, name, year, isbn, books.id
                                FROM books
                                JOIN authors
                                ON books.author_id=authors.id
                                WHERE LOWER(title) LIKE LOWER(:book)
                                OR LOWER(name) LIKE LOWER(:book)
                                OR isbn LIKE :book
                                """,
                                {'book': '%' + bookQuery + '%'}).fetchall()
    return books

#Formats the list of tuples as a dictionary of 'title': {author, year} dictionaries
def buildDict(sqlArr):
    booksDict = {}
    for book in sqlArr:
        booksDict[book[0]] = {}
        booksDict[book[0]]['author'] = book[1]
        booksDict[book[0]]['year'] = book[2]
        booksDict[book[0]]['isbn'] = book[3]
        booksDict[book[0]]['id'] = book[4]

    return booksDict

######## MAIN ##########

@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    #User reached via POST
    #i.e. is submitting registration
    if request.method == "POST":

        #check username entered
        if not request.form.get("username"):
            return render_template("register.html", error="Username not submitted")

        #check password entered
        elif not request.form.get("password"):
            return render_template("register.html", error="Password not submitted")

        #check password confirmed
        elif not request.form.get("confirm"):
            return render_template("register.html", error="Confirm password")

        #check password matches confirmation
        elif request.form.get("password") != request.form.get("confirm"):
            return render_template("register.html", error="Confirmation does not match password")


        #Query database for entry
        rows = db.execute("SELECT * FROM users WHERE username=:username",
                            {"username":request.form.get("username")}).fetchone()

        #Ensure username is novel
        if rows is not None:
            return render_template("register.html", error="Username already in use")

        #Make new entry in database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                    {"username": request.form.get("username"), "hash": generate_password_hash(request.form.get("password"))})
        db.commit()

        flash("You were successfully registered!")
        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    #clear any current session
    session.clear()

    #User reached via POST
    #i.e. submitting a log in form
    if request.method == "POST":

        #check username entered
        if not request.form.get("username"):
            return render_template("login.html", error="Username not submitted")

        #check password entered
        elif not request.form.get("password"):
            return render_template("login.html", error="Password not submitted")

        #Query database for entry
        rows = db.execute("SELECT * FROM users WHERE username=:username",
                            {"username":request.form.get("username")}).fetchone()

        #Ensure username exists, password matches
        try:
            if not check_password_hash(rows[2], request.form.get("password")):
                return render_template("login.html", error="Invalid username or password")
        except TypeError:
            return render_template("login.html", error="Invalid username or password")

        #Remember user
        session["user_id"] = rows[0]

        #Return to homepage
        return redirect("/")

    #User reached via get
    #i.e. is attempting to log in
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


reqDict = {}
@app.route("/search", methods=["GET", "POST"])
def search():

    #If an autocomplete query is submitted
    if request.method == "GET":

        books = booksearch(request.args.get("q"))

        #Sends data back to view
        return jsonify(buildDict(books))

    #If a POST request is sent
    if request.method == "POST":

        #if nothing submitted
        if not (request.form.get('book')):
            return render_template("index.html", error="Must submit atleast one search field")

        books = booksearch(request.form.get('book'))

        return render_template("results.html", books=buildDict(books))
       

@app.route("/bookpage", methods=["GET"])
def bookpage():
    if request.method == "GET":
        books = buildDict([request.args.get('info').split(',')])
        
        #Check if book has ratings, add them to 
        for book in books:
            isbn = books[book]['isbn']
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "J7hfLkKaYDCxKsASYaFQAA", "isbns": isbn})
        rates = [res.json()['books'][0]['work_ratings_count'], res.json()['books'][0]['average_rating']]

        return render_template("bookpage.html", books=books, rates=rates)


@app.route("/reviewsubmission", methods=["GET", "POST"])
@login_required
def reviewsubmission():

    username = db.execute("SELECT username FROM users WHERE id=:id", {'id': session["user_id"]}).fetchone()[0]   

    if request.method == "GET":
        infoList = [request.args.get('info').split(',')]
        return render_template("review.html", books=buildDict(infoList), username=username.capitalize())

    if request.method == "POST":

        books = literal_eval(request.form.get("books"))
        for book in books:
            books[book]['review'] = request.form.get("review")
        #Check that review and rating are both submitted, else error
        if not request.form.get('review') or not request.form.get('rate'):


            return render_template("review.html", books=books, username=username.capitalize(), error="Please enter a review and a rating")
        
        user_id = session["user_id"]
        for book in books:
            book_id = books[book]['id']

        #prevent multiple reviews from same user
        pastreviews = db.execute("""SELECT * FROM reviews
                        WHERE user_id=:user_id
                        AND book_id=:book_id""",
                        {'user_id': user_id, 'book_id': book_id}).fetchone()
        print(pastreviews)            

        if pastreviews:
            return render_template("review.html", books=books, username=username.capitalize(), error="You have already reviewed this book. Please search for a different book")
        
        # Submit reviews to database
        db.execute("""INSERT INTO reviews (user_id, book_id, review, rating)
                        VALUES (:user_id, :book_id, :review, :rating)""",
                        {'user_id': user_id, 'book_id': book_id, 'review': request.form.get('review'), 'rating': request.form.get('rate')})
        db.commit()
        return render_template("index.html", message="Review submitted!")


@app.route("/api/<isbn>", methods=["GET"])
@login_required
def api(isbn):

    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"Error": "No entry for this book"}), 404
    
    book = db.execute("""
                        SELECT (title, name, year)
                        FROM books
                        JOIN authors ON books.author_id=authors.id
                        WHERE isbn=:isbn
                        """,
                        {'isbn': isbn}).fetchall()[0][0]


    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "J7hfLkKaYDCxKsASYaFQAA", "isbns": isbn})

    book_isbn = res.json()['books'][0]['isbn']
    review_count = res.json()['books'][0]['reviews_count']
    average_rating = res.json()['books'][0]['average_rating']

    book = book.replace('(', '')
    book = book.replace(')', '')
    bookList = book.split(',')
    title = bookList[0]
    author = bookList[1].replace('\"', '')
    year = bookList[2]

    return jsonify({'title': title, 'author': author, 'year': year, 'isbn': book_isbn, 'review_count': review_count, 'average_rating': average_rating})



   

    if request.args.get('isbn') == '2':
        return "successsss"

    
