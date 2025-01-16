from flask import Flask, request, render_template
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.spelling import Corrector
from whoosh.scoring import TF_IDF
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    page = int(request.args.get("page", 1))  # Current page number
    per_page = 10  # Results per page
    start = (page - 1) * per_page
    corrected_query = query
    results = []
    total_results = 0

    if query:
        try:
            ix = open_dir("index")
            with ix.searcher() as searcher:
                # Use Corrector for spelling correction
                corrector = searcher.corrector("content")
                corrected_query = " ".join(
                    corrector.suggest(word, limit=1)[0] if corrector.suggest(word, limit=1) else word
                    for word in query.split()
                )

                # Parse and search
                parser = QueryParser("content", ix.schema)
                q = parser.parse(corrected_query)
                raw_results = searcher.search(q)
                total_results = len(raw_results)

                # Extract necessary fields before the searcher is closed
                results = [
                    {"title": hit["title"], "url": hit["url"], "highlight": hit.highlights("content")}
                    for hit in raw_results[start:start + per_page]
                ]
        except Exception as e:
            print(f"Error during search: {e}")
            return render_template("error.html", message="An error occurred during the search.")

    return render_template(
        "results.html",
        query=query,
        corrected_query=corrected_query,
        results=results,
        page=page,
        total_pages=(total_results // per_page) + (1 if total_results % per_page else 0),
    )
