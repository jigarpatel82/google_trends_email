from bs4 import BeautifulSoup
from pytrends.request import TrendReq
import pandas as pd
from flask import Flask, request, jsonify, url_for
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
import os

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscribers.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
sender_email= os.environ.get('email')
sender_password = os.environ.get('password')
server_config = smtplib.SMTP('smtp-mail.outlook.com', 587)


db = SQLAlchemy(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Model for storing subscribers
class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    verified = db.Column(db.Boolean, default=False)
    geo = db.Column(db.String(50))
    api_method = db.Column(db.String(50))
    category = db.Column(db.Integer)
    keywords = db.Column(db.String(255))
    timeframe = db.Column(db.String(50))

# Initialize the database
# @app.before_first_request
# def create_tables():
#     db.create_all()
    
with app.app_context():
    db.create_all()


def send_verification_email(email, token):
    receiver_email = email

    # Construct verification link
    link = url_for('confirm_email', token=token, _external=True)

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Confirm Your Subscription'

    # Email body with the verification link
    body = f"Please click the link to confirm your subscription: {link}"
    message.attach(MIMEText(body, 'plain'))

    # Sending the email
    try:
        server = server_config
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print(f"Verification email sent to {email} successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

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
    print('inside subscribe route')
    data = request.json
    email = data.get('email')
    geo = data.get('geo', 'US')
    api_method = data.get('apiMethod', 'interest over time')
    category = data.get('category', 0)
    keywords = data.get('keywords', [])
    timeframe = data.get('timeframe', 'today 5-y')

    # Check if the email already exists
    # existing_subscriber = Subscriber.query.filter_by(email=email).first()
    # if existing_subscriber:
    #     return jsonify({"message": "Email is already subscribed."}), 400

    # Add new subscriber with unverified status
    new_subscriber = Subscriber(
        email=email, 
        geo=geo, 
        api_method=api_method, 
        category=category, 
        keywords=','.join(keywords), 
        timeframe=timeframe
    )
    db.session.add(new_subscriber)
    db.session.commit()

    # Send verification email
    print('generating token')
    token = generate_confirmation_token(email)
    print('token generated')
    send_verification_email(email, token)
    print('verification email sent')

    return jsonify({"message": "Subscription created! Please verify your email."}), 200

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
        return jsonify({"message": "You have confirmed your account!"}), 200

@app.route('/api/subscribers', methods=['GET'])
def get_subscribers():
    subscribers = Subscriber.query.filter_by(verified=True).all()
    return jsonify([{
        "email": s.email,
        "geo": s.geo,
        "api_method": s.api_method,
        "category": s.category,
        "keywords": s.keywords,
        "timeframe": s.timeframe
    } for s in subscribers])


def google_trends(geo, api_method, category=0, keywords=[], timeframe='today 5-y'):
    pytrends = TrendReq()
    
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


def create_chart():
    """This will create a chart to pass on to user's email of the current trends"""
    pass


def send_email(email, trends_data):
    receiver_email = email

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Daily Google Trends Report'

    # Create the email content
    body = f"Here is your Google Trends data:\n\n{trends_data}"
    message.attach(MIMEText(body, 'plain'))

    # Sending the email
    try:
        server = server_config
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print(f"Email sent to {email} successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


@app.route('/api/sendGoogleTrends', methods=['POST'])
def send_google_trends():
    print('inside send data')
    data = request.json
    email = data.get('email')
    geo = data.get('geo', 'US')
    api_method = data.get('apiMethod', 'interest over time')
    category = data.get('category', 0)
    keywords = data.get('keywords', [])
    timeframe = data.get('timeframe', 'today 5-y')
    print(data)
    
    # fetch trends data
    trends_data = google_trends(geo, api_method, category, keywords, timeframe)
    trends_data.to_csv("google_data_new4.csv", index=False)
    send_email(email, trends_data)
    
    return jsonify({"message": "email sent successfully"}), 200
    

if __name__ == '__main__':
    app.run(debug=True)