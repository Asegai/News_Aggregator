from flask import Flask, render_template_string
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
    html_content = '''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>News Aggregator</title>
      </head>
      <body>
        <h1>News Aggregator</h1>
        {% for article in articles %}
          <div>
            <h2>{{ article['title'] if 'title' in article else article.title }}</h2>
            <p>{{ article['description'] if 'description' in article else article.summary }}</p>
            <a href="{{ article['url'] if 'url' in article else article.link }}">Read more</a>
          </div>
        {% endfor %}
      </body>
    </html>
    '''
    return render_template_string(html_content, articles=articles)

if __name__ == '__main__':
    app.run(debug=True)
