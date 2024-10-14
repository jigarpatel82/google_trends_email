from bs4 import BeautifulSoup
from pytrends.request import TrendReq
import pandas as pd
from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
import os
import plotly.graph_objects as go
import plotly.io as pio
import sendgrid 
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import base64


app = Flask(__name__)
CORS(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscribers.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
sender_email= os.environ.get('email')
sender_password = os.environ.get('password')


db = SQLAlchemy(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    verified = db.Column(db.Boolean, default=False)
    subscriptions = db.relationship('Subscription', backref='subscriber', lazy=True)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subscriber_id = db.Column(db.Integer, db.ForeignKey('subscriber.id'), nullable=False)
    geo = db.Column(db.String(50))
    api_method = db.Column(db.String(50))
    category = db.Column(db.Integer)
    keywords = db.Column(db.String(255))
    timeframe = db.Column(db.String(50))

    
with app.app_context():
    db.create_all()


def send_verification_email(email, token):
    receiver_email = email

    # Construct verification link
    link = url_for('confirm_email', token=token, _external=True)
    
    message = Mail(
        from_email=(sender_email),
        to_emails=(receiver_email),
        subject='Google trends subscription',
        html_content = f'''
            <h1>Subscription confirmation</h1>
            <p>Please click the link to confirm your subscription:{link}</p>
        '''
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        print(sg)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(f'Error sending email: {e}.')
    else:
        print('Email sent successfully')
        
        
# Generate a verification token
def generate_confirmation_token(email):
    return s.dumps(email, salt='email-confirmation')

# Verify token
def confirm_token(token, expiration=3600):
    try:
        email = s.loads(token, salt='email-confirmation', max_age=expiration)
    except Exception:
        return False
    return email

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    email = data.get('email')
    geo = data.get('geo', 'US')
    api_method = data.get('apiMethod', 'interest over time')
    category = data.get('category', 0)
    keywords = data.get('keywords', [])
    timeframe = data.get('timeframe', 'today 5-y')

    # Check if the subscriber exists
    subscriber = Subscriber.query.filter_by(email=email).first()
    if not subscriber:
        # If the subscriber does not exist, create one
        subscriber = Subscriber(email=email)
        db.session.add(subscriber)
        db.session.commit()

    # Add a new subscription for the subscriber
    new_subscription = Subscription(
        subscriber_id=subscriber.id, 
        geo=geo, 
        api_method=api_method, 
        category=category, 
        keywords=','.join(keywords), 
        timeframe=timeframe
    )
    db.session.add(new_subscription)
    db.session.commit()

    # Send verification email if not verified
    if not subscriber.verified:
        token = generate_confirmation_token(email)
        send_verification_email(email, token)
        return jsonify({"message": "Subscription created! Please verify your email."}), 200
    else:
        subscriptions = Subscription.query.filter_by(subscriber_id=subscriber.id).all()
        for subscription in subscriptions:
            geo = subscription.geo
            api_method = subscription.api_method
            category = subscription.category
            keywords_data = subscription.keywords
            keywords = keywords_data.split(',')
            timeframe = subscription.timeframe
            sub_id = subscriber.id
            trends_data = google_trends(geo, api_method, category, keywords, timeframe)
            if api_method == "interest over time":
                create_chart(data=trends_data, keywords=keywords, sub_id=sub_id)
                print('chart created')
                print(f'this is the sub email{subscriber.email}')
            else:
                trends_data.to_csv(f"google_data_{sub_id}.csv", index=False)  
            send_email(subscriber.email, trends_data, api_method=api_method)

        return jsonify({"message": "Subscription created successfully!"}), 200


@app.route('/confirm/<token>', methods=['GET'])
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        return jsonify({"message": "The confirmation link is invalid or has expired."}), 400

    subscriber = Subscriber.query.filter_by(email=email).first_or_404()

    if subscriber.verified:    
        return jsonify({"message": "Account already confirmed."}), 200
    else:
        subscriber.verified = True
        db.session.commit()
        # fetch trends data
        subscriptions = Subscription.query.filter_by(subscriber_id=subscriber.id).all()
        for subscription in subscriptions:
            geo = subscription.geo
            api_method = subscription.api_method
            category = subscription.category
            keywords_data = subscription.keywords
            keywords = keywords_data.split(',')
            timeframe = subscription.timeframe
            sub_id = subscriber.id
            trends_data = google_trends(geo, api_method, category, keywords, timeframe)
            if api_method == "interest over time":
                create_chart(data=trends_data, keywords=keywords, sub_id=sub_id)
                print('chart created')
                print(f'this is the sub email{subscriber.email}')
            else:
                trends_data.to_csv(f"google_data_{sub_id}.csv", index=False)  
            send_email(subscriber.email, trends_data, api_method=api_method)
        return jsonify({"message": "You have confirmed your account!"}), 200

@app.route('/api/subscribers', methods=['GET'])
def get_subscribers():
    subscribers = Subscriber.query.filter_by(verified=True).all()
    return jsonify([{
        "email": s.email,
        "subscriptions": [{
            "geo": sub.geo,
            "api_method": sub.api_method,
            "category": sub.category,
            "keywords": sub.keywords,
            "timeframe": sub.timeframe
        } for sub in s.subscriptions]
    } for s in subscribers])



def google_trends(geo, api_method, category=0, keywords=[], timeframe='today 5-y'):
    
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    
    pytrends = TrendReq(hl='en-US',retries=3, backoff_factor=20)
    
    if api_method == 'interest over time':
    # build payload
        pytrends.build_payload(keywords, geo=geo, timeframe=timeframe, cat=category, gprop='')
        
        trends = pytrends.interest_over_time()
        
        return trends
    elif api_method == 'trending searches':
        trends = pytrends.realtime_trending_searches(pn=geo)
        return trends
    elif api_method == 'interest by region':
        trends = pytrends.interest_by_region(resolution=geo, inc_low_vol=True, inc_geo_code=True)
        return trends



def create_chart(data, keywords, sub_id):
    """This will create a chart using Plotly to pass on to user's email of the current trends"""

    # Create a Plotly figure
    fig = go.Figure()

    # Add a trace for each keyword
    for keyword in keywords:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data[keyword],
            mode='lines',
            name=keyword
        ))

    # Update layout with titles and labels
    fig.update_layout(
        title='Google Trends Over Time',
        xaxis_title='Date',
        yaxis_title='Search Interest',
        legend_title='Keywords',
        template='plotly_white',  # Optional: Set a template for style
        autosize=False,
        width=1000,
        height=600
    )

    # Save the figure as a PNG image
    pio.write_image(fig, f'/Users/sanchi/Desktop/Jigar/google_trends_scrapper/google_trends_chart-{sub_id}.png')

    # Alternatively, save as an HTML file if you need interactivity
    # fig.write_html(f'google_trends_chart-{sub_id}.html')

    return jsonify({'message': 'chart created successfully'})

def send_email(email, trends_data, api_method):
    receiver_email = email
    
    message = Mail(
        from_email=(sender_email),
        to_emails=(receiver_email),
        subject='Google trends subscription',
        html_content = f'''
            <h1>Google Trends Data</h1>
            <p>{trends_data}</p>
        '''
    )
    
    
    # Attach the chart image
    subscriber = Subscriber.query.filter_by(email=email).first_or_404()
    if api_method == 'interest over time':
        attachment_path = f'/Users/sanchi/Desktop/Jigar/google_trends_scrapper/google_trends_chart-{subscriber.id}.png'
        with open(attachment_path, 'rb') as f:
            data = f.read()
            message.attachment = sendgrid.Attachment(
                disposition='inline',
                file_name=f'google_trends_chart-{subscriber.id}.png',
                file_type='image/png',
                file_content=base64.b64encode(data).decode(),
                content_id='google_trends_chart',
    )
    else:
        attachment_path = f'/Users/sanchi/Desktop/Jigar/google_trends_scrapper/google_data_{subscriber.id}.csv'
        with open(attachment_path, 'rb') as f:
            data = f.read()
            message.attachment = sendgrid.Attachment(
                disposition='attachment',
                file_name=f'google_trends_chart-{subscriber.id}.csv',
                file_type='text/csv',
                file_content=base64.b64encode(data).decode(),
                content_id='google_trends_chart',
    )
            
    # Sending the email
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        print(sg)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(f'Error sending email: {e}.')
    else:
        print('Email sent successfully')

if __name__ == '__main__':
    app.run(debug=True)