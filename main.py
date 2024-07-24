from flask import Flask, render_template_string, request
import requests
import feedparser

app = Flask(__name__)

def fetch_news(api_key, query):
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    response = requests.get(url)
    news_data = response.json()
    return news_data['articles']

def fetch_rss_feed(url):
    feed = feedparser.parse(url)
    return feed.entries

def aggregate_news(api_key, rss_urls, query):
    articles = fetch_news(api_key, query)
    for url in rss_urls:
        articles.extend(fetch_rss_feed(url))
    return articles

rss_urls = [
    'https://rss.cnn.com/rss/edition_technology.rss',
    'https://feeds.bbci.co.uk/news/technology/rss.xml'
]

with open('news_api_key.txt', 'r') as file:
    api_key = file.read().strip() 
    
@app.route('/')
def home():
    query = request.args.get('query', 'technology')
    articles = aggregate_news(api_key, rss_urls, query)
    show_all = request.args.get('show_all', 'false') == 'true'
    num_articles = len(articles)
    articles_to_show = articles if show_all else articles[:10]
    return render_template_string(html_content, articles=articles_to_show, num_articles=num_articles, show_all=show_all, query=query)

html_content = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>News Aggregator</title>
    <style>
      body { font-family: Arial, sans-serif; }
      .container { max-width: 800px; margin: 0 auto; padding: 20px; }
      h1 { text-align: center; }
      .article { margin-bottom: 20px; }
      .more-button { display: flex; justify-content: center; }
      .search-container { text-align: center; margin-bottom: 20px; }
      .search-box { display: none; margin-top: 10px; }
      .search-button { background: none; border: none; cursor: pointer; }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>News Aggregator</h1>
      <div class="search-container">
        <button class="search-button" onclick="toggleSearchBox()">
          <img src="{{ url_for('static', filename='search.png') }}" alt="Search" width="24" height="24">
        </button>
        <div class="search-box" id="searchBox">
          <form action="/" method="get">
            <input type="text" name="query" value="{{ query }}" placeholder="Search...">
            <button type="submit">Search</button>
          </form>
        </div>
      </div>
      {% for article in articles %}
        <div class="article">
          <h2>{{ article['title'] if 'title' in article else article.title }}</h2>
          <p>{{ article['description'] if 'description' in article else article.summary }}</p>
          <a href="{{ article['url'] if 'url' in article else article.link }}" target="_blank">Read more</a>
        </div>
      {% endfor %}
      {% if not show_all and num_articles > 10 %}
        <div class="more-button">
          <a href="/?query={{ query }}&show_all=true"><button>More</button></a>
        </div>
      {% endif %}
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
    </script>
  </body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
