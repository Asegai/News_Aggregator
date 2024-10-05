from flask import Flask, render_template_string, request
import requests
import feedparser
from textblob import TextBlob
from cachetools import cached, TTLCache
import datetime



app = Flask(__name__)

cache = TTLCache(maxsize=100, ttl=600)

last_fetched_time = None

@cached(cache)
def fetch_news(api_key, query):
    global last_fetched_time
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    response = requests.get(url)
    news_data = response.json()
    last_fetched_time = datetime.datetime.now()
    return news_data['articles']

@cached(cache)
def fetch_rss_feed(url):
    feed = feedparser.parse(url)
    return feed.entries

def aggregate_news(api_key, rss_urls, query):
    articles = fetch_news(api_key, query)
    for url in rss_urls:
        rss_articles = fetch_rss_feed(url)
        for article in rss_articles:
            article['source'] = {'name': url.split('/')[2]}
        articles.extend(rss_articles)
    return articles

def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    if sentiment > 0:
        return "Positive"
    elif sentiment < 0:
        return "Negative"
    else:
        return "Neutral"

def filter_removed_articles(articles):
    return [
        article for article in articles 
        if article.get('title') and '[Removed]' not in article['title'] and
           article.get('description') and '[Removed]' not in article['description']
    ]

def validate_query(query):
    if not query or query.strip() == "":
        return False
    return True

def last_updated():
    global last_fetched_time
    if last_fetched_time is not None:
        return last_fetched_time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return "News has not been fetched yet."

rss_urls = [
    'https://rss.cnn.com/rss/edition_tech.rss',
    'https://feeds.bbci.co.uk/news/tech/rss.xml',
    'https://www.theverge.com/rss/index.xml',
    'https://techcrunch.com/feed/',
    'https://www.wired.com/feed/rss',
    'https://www.engadget.com/rss.xml',
    'https://arstechnica.com/feed/',
    'https://feeds.mashable.com/Mashable'
]

api_key = '9903ee12bcb04fcab57b84705f5a047b'

@app.route('/')
def home():
    query = request.args.get('query', 'latest')
    if not validate_query(query):
        return render_template_string(error_html, message="Search query cannot be empty.")
    
    page = int(request.args.get('page', 1))
    articles_per_page = 10
    
    articles = aggregate_news(api_key, rss_urls, query)
    articles = filter_removed_articles(articles)
    
    total_articles = len(articles)
    total_pages = (total_articles + articles_per_page - 1) // articles_per_page
    start_idx = (page - 1) * articles_per_page
    end_idx = min(start_idx + articles_per_page, total_articles)
    articles_to_show = articles[start_idx:end_idx]
    
    for article in articles_to_show:
        article['sentiment'] = analyze_sentiment(article['description'] if 'description' in article else article['summary'])

    pagination_range = 5
    start_page = max(1, page - pagination_range)
    end_page = min(total_pages, page + pagination_range)
    if end_page - start_page < 2 * pagination_range:
        if start_page == 1:
            end_page = min(start_page + 2 * pagination_range, total_pages)
        if end_page == total_pages:
            start_page = max(1, end_page - 2 * pagination_range)

    last_updated_time = last_updated()

    return render_template_string(html_content, 
                                  articles=articles_to_show, 
                                  total_pages=total_pages, 
                                  current_page=page, 
                                  query=query,
                                  start_page=start_page,
                                  end_page=end_page,
                                  last_updated=last_updated_time)

@app.route('/about')
def about():
    return render_template_string(about_html)

@app.route('/last-updated')
def get_last_updated():
    return last_updated()

html_content = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>News Central</title>
    <style>
      @font-face {
        font-family: 'Title Font';
        src: url("{{ url_for('static', filename='title_font.ttf') }}") format('truetype');
      }
      body { 
        font-family: Arial, sans-serif; 
        background-color: #FFA500;
        color: #FFFFFF;
        transition: background-color 0.3s, color 0.3s;
        text-shadow: 2px 2px 4px #000000;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        min-height: 100vh;
      }
      .dark-mode { 
        background-color: #121212; 
        color: #e0e0e0; 
        text-shadow: 2px 2px 4px #000000;
      }
      .container { 
        flex: 1;
        max-width: 800px; 
        margin: 0 auto; 
        padding: 10px 20px; 
      }
      h1 { 
        text-align: center; 
        font-family: 'Title Font', Arial, sans-serif; 
        font-size: 4em;
        font-weight: bold;
        color: #FFFFFF;
        text-shadow: 3px 3px 6px #000000;
      }
      h2, p {
        font-weight: bold;
        color: #FFFFFF;
        text-shadow: 2px 2px 4px #000000;
      }
      .source {
        font-size: 0.8em;
        color: #FFFFFF;
        margin-bottom: 10px;
      }
      .sentiment { 
        display: flex; 
        align-items: center; 
      }
      .sentiment img { 
        margin-right: 10px; 
      }
      .more-button { 
        display: flex; 
        justify-content: center; 
      }
      .search-container { 
        text-align: center; 
        margin-bottom: 20px; 
      }
      .search-box { 
        display: none; 
        margin-top: 10px; 
      }
      .search-button { 
        background: none; 
        border: none; 
        cursor: pointer; 
      }
      .dark-mode-toggle { 
        position: absolute; 
        top: 10px; 
        left: 10px; 
        cursor: pointer; 
      }
      a {
        color: #FFFFFF;
        text-shadow: 2px 2px 4px #000000;
      }
      .pagination {
        display: flex;
        justify-content: center;
        margin-top: 20px;
        flex-wrap: wrap;
      }
      .pagination a {
        color: #FFFFFF;
        text-shadow: 2px 2px 4px #000000;
        margin: 0 5px;
        padding: 5px 10px;
        text-decoration: none;
        background-color: #333;
        border-radius: 5px;
        font-size: 0.9em;
      }
      .pagination a.active {
        background-color: #000;
      }
      .pagination a:hover {
        background-color: #555;
      }
      .copy-popup {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: rgba(0, 0, 0, 0.8);
        color: #FFFFFF;
        padding: 10px 20px;
        border-radius: 10px;
        text-align: center;
        z-index: 1000;
        display: none;
      }
      .share-button {
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 0;
        font-size: 0;
        margin top: 10px;
      }
      .share-button img {
        display: block;
        width: 24px;
        height: 24px;
      }
      .footer {
        background-color: #46b6ff;
        color: #FFFFFF;
        text-align: center;
        padding: 10px;
        box-shadow: 0 -1px 5px rgba(0,0,0,0.3);
      }
      @media (max-width: 600px) {
        .container {
          padding: 10px;
        }
        h1 {
          font-size: 2em;
        }
        .pagination a {
          padding: 3px 6px;
          font-size: 0.8em;
        }
      }
    </style>
  </head>
  <body>
    <img src="{{ url_for('static', filename='dark_mode.png') }}" alt="Dark Mode" width="24" height="24" class="dark-mode-toggle" onclick="toggleDarkMode()"> <!--<a href="https://www.flaticon.com/free-icons/dark" title="dark icons">Dark icons created by adriansyah - Flaticon</a>-->
    <div class="container">
      <h1>N e w s  C e n t r a l</h1>
      <div class="search-container">
        <button class="search-button" onclick="toggleSearchBox()"> <!--<a href="https://www.flaticon.com/free-icons/search" title="search icons">Search icons created by Freepik - Flaticon</a>-->
          <img src="{{ url_for('static', filename='search.png') }}" alt="Search" width="24" height="24">
        </button>
        <div class="search-box" id="searchBox">
          <form action="/" method="get">
            <input type="text" name="query" value="{{ query }}" placeholder="Search..." aria-label="Search">
            <button type="submit">Search</button>
          </form>
        </div>
      </div>
      {% for article in articles %}
        <div class="article">
          <h2>{{ article['title'] if 'title' in article else article.title }}</h2>
          <p>{{ article['description'] if 'description' in article else article.summary }}</p>
          <p class="source">Source: {{ article['source']['name'] if 'source' in article and 'name' in article['source'] else 'Unknown Source' }}</p>
          <p class="sentiment">
            {% if article['sentiment'] == 'Positive' %}
              <img src="{{ url_for('static', filename='positive_sentiment.png') }}" alt="Positive" width="20" height="20"> 
              Reception: Positive <!-- <a href="https://www.flaticon.com/free-icons/happiness" title="happiness icons">Happiness icons created by Freepik - Flaticon</a> -->
            {% elif article['sentiment'] == 'Negative' %}
              <img src="{{ url_for('static', filename='negative_sentiment.png') }}" alt="Negative" width="20" height="20"> 
              Reception: Negative <!-- <a href="https://www.flaticon.com/free-icons/sad" title="sad icons">Sad icons created by Freepik - Flaticon</a> -->
            {% else %}
              <img src="{{ url_for('static', filename='neutral_sentiment.png') }}" alt="Neutral" width="20" height="20">
              Reception: Neutral <!-- <a href="https://www.flaticon.com/free-icons/neutral" title="neutral icons">Neutral icons created by justicon - Flaticon</a> -->
            {% endif %}
          </p>
          <a href="{{ article['url'] if 'url' in article else article.link }}">Read more</a>
          <button class="share-button" onclick="copyLink('{{ article['url'] if 'url' in article else article.link }}')"> <!--<a href="https://www.flaticon.com/free-icons/share" title="share icons">Share icons created by Freepik - Flaticon</a>-->
            <img src="{{ url_for('static', filename='share.png') }}" alt="Share">
          </button>
        </div>
      {% endfor %}
      <div class="pagination">
        {% if current_page > 1 %}
          <a href="/?query={{ query }}&page={{ current_page - 1 }}">&laquo; Previous</a>
        {% endif %}
        {% for i in range(start_page, end_page + 1) %}
          <a href="/?query={{ query }}&page={{ i }}" class="{{ 'active' if i == current_page else '' }}">{{ i }}</a>
        {% endfor %}
        {% if current_page < total_pages %}
          <a href="/?query={{ query }}&page={{ current_page + 1 }}">Next &raquo;</a>
        {% endif %}
      </div>
    </div>
    <div id="copyPopup" class="copy-popup">Link copied!</div>
    <div class="footer">
      <a href="/about">About Us</a>
      <p>Last updated: {{ last_updated }}</p>
    </div>
    <script>
      function toggleSearchBox() {
        var searchBox = document.getElementById('searchBox');
        if (searchBox.style.display === 'none') {
          searchBox.style.display = 'block';
        } else {
          searchBox.style.display = 'none';
        }
      }

      function toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        // #! Save preference
        if (document.body.classList.contains('dark-mode')) {
          localStorage.setItem('darkMode', 'enabled');
        } else {
          localStorage.setItem('darkMode', 'disabled');
        }
      }

      // #! Preference check
      if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
      }

      function copyLink(url) {
        navigator.clipboard.writeText(url).then(function() {
          var popup = document.getElementById('copyPopup');
          popup.style.display = 'block';
          setTimeout(function() {
            popup.style.display = 'none';
          }, 2000);
        });
      }
    </script>
  </body>
</html>
'''

error_html = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Error</title>
    <style>
      @font-face {
        font-family: 'Title Font';
        src: url("{{ url_for('static', filename='title_font.ttf') }}") format('truetype');
      }
      body {
        font-family: Arial, sans-serif;
        background-color: #FFA500;
        color: #FFFFFF;
        text-align: center;
        padding: 20px;
        margin: 0; 
        display: flex;
        flex-direction: column;
        min-height: 100vh;
      }
      .dark-mode { 
        background-color: #121212; 
        color: #e0e0e0; 
      }
      .dark-mode-toggle { 
        position: absolute; 
        top: 10px; 
        left: 10px; 
        cursor: pointer; 
      }
      .error-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background-color: #FFA500;
        border-radius: 5px;
      }
      h1, p {
        color: #FFFFFF;
        text-shadow: 2px 2px 4px #000000;
      }
      a {
        color: #FFFFFF;
        text-decoration: underline;
        text-shadow: 2px 2px 4px #000000;
      }
    </style>
  </head>
  <body>
    <img src="{{ url_for('static', filename='dark_mode.png') }}" alt="Dark Mode" width="24" height="24" class="dark-mode-toggle" onclick="toggleDarkMode()"> 
    <div class="error-container">
      <h1>Error</h1>
      <p>{{ message }}</p>
      <a href="/" aria-label="Go back to the homepage">Go back to the homepage</a>
    </div>
    <script>
      function toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        if (document.body.classList.contains('dark-mode')) {
          localStorage.setItem('darkMode', 'enabled');
        } else {
          localStorage.setItem('darkMode', 'disabled');
        }
      }

      if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
      }
    </script>
  </body>
</html>
'''

about_html = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>About Us</title>
    <style>
      @font-face {
        font-family: 'title_font';
        src: url("{{ url_for('static', filename='title_font.ttf') }}") format('truetype');
      }
      body {
        font-family: Arial, sans-serif;
        background-color: #FFA500;
        color: #FFFFFF;
        text-align: center;
        padding: 20px;
        margin: 0;
        display: flex;
        flex-direction: column;
        min-height: 100vh;
      }
      .dark-mode { 
        background-color: #121212; 
        color: #e0e0e0; 
      }
      .dark-mode-toggle { 
        position: absolute; 
        top: 10px; 
        left: 10px; 
        cursor: pointer; 
      }
      h1 {
        font-family: 'title_font', Arial, sans-serif;
        color: #FFFFFF;
        text-shadow: 2px 2px 4px #000000;
      }
      a {
        color: #FFFFFF;
        text-decoration: underline;
        text-shadow: 2px 2px 4px #000000;
      }
    </style>
  </head>
  <body>
    <img src="{{ url_for('static', filename='dark_mode.png') }}" alt="Dark Mode" width="24" height="24" class="dark-mode-toggle" onclick="toggleDarkMode()"> 
    <h1>About Us</h1>
    <p>Welcome to News Central. We are dedicated to bringing you the latest news from around the world.</p>
    <a href="/" aria-label="Go back to the homepage">Go back to the homepage</a>
    <script>
      function toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        if (document.body.classList.contains('dark-mode')) {
          localStorage.setItem('darkMode', 'enabled');
        } else {
          localStorage.setItem('darkMode', 'disabled');
        }
      }

      if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
      }
    </script>
  </body>
</html>

'''

if __name__ == '__main__':
    app.run(debug=True)
