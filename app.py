from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import openai
from flask_pretty import Prettify
import requests

openai.api_type = "azure"
openai.api_base = "https://openairedflags.openai.azure.com/"
openai.api_version = "2023-05-15"
openai.api_key = os.getenv("OPENAI_API_KEY")
api_key = os.getenv("GOOGLE_API_KEY")
cx = os.getenv("GOOGLE_CX")
base_url = "https://www.googleapis.com/customsearch/v1"

app = Flask(__name__)
prettify = Prettify(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:////tmp/test.db')#'sqlite:////tmp/test.db'  # Use the correct path for your application
db = SQLAlchemy(app)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(80), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Page {self.path}>'

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path == '':
        # Display all the pages if the path is root
        pages = Page.query.order_by(Page.timestamp.desc()).all()
        return render_template('index.html', pages=pages)

    page = Page.query.filter_by(path=path).first()
    if page is None:
        params = {
            "key": api_key,
            "cx": cx,
            "q": path
        }
        response = requests.get(base_url, params=params)
        data = response.json()
        print(data['items'])
        usermessage = "Write a blog post about '''"+str(path) +"'''. Respond in HTML format within the <body> tag. Do not include the <body> tag in your response. Include the search results for information "+str(data['items'][0]['title']) + " " + str(data['items'][0]['snippet']) + " " + str(data['items'][0]['link']) + " " + str(data['items'][1]['title']) + " " + str(data['items'][1]['snippet']) + " " + str(data['items'][1]['link'])
        # Generate content for the new page
        response = openai.ChatCompletion.create(
          deployment_id = "symptoms",
          messages = [
            {
              "role": "system",
              "content": "You are an influencer"
            },
            {
              "role": "user",
              "content": usermessage
            }
          ]
        )
        print(str(path))
        content = response.choices[0].message["content"]
        print(content)
        new_content = content#"This is a new page"
        page = Page(path=path, content=new_content)
        db.session.add(page)
        db.session.commit()

    # Render the content of the page
    return render_template('page.html', content=page.content)

if __name__ == '__main__':
    app.run(debug=True)
