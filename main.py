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
    articles = aggregate_news(api_key, rss_urls, 'technology')
    show_all = request.args.get('show_all', 'false') == 'true'
    num_articles = len(articles)
    articles_to_show = articles if show_all else articles[:10]
    return render_template_string(html_content, articles=articles_to_show, num_articles=num_articles, show_all=show_all)

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
    </style>
  </head>
  <body>
    <div class="container">
      <h1>News Aggregator</h1>
      {% for article in articles %}
        <div class="article">
          <h2>{{ article['title'] if 'title' in article else article.title }}</h2>
          <p>{{ article['description'] if 'description' in article else article.summary }}</p>
          <a href="{{ article['url'] if 'url' in article else article.link }}" target="_blank">Read more</a>
        </div>
      {% endfor %}
      {% if not show_all and num_articles > 10 %}
        <div class="more-button">
          <a href="/?show_all=true"><button>More Articles</button></a>
        </div>
      {% endif %}
    </div>
  </body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
