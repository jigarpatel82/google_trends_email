from bs4 import BeautifulSoup
from pytrends.request import TrendReq
import pandas as pd

def google_trends(geo, api_method, category=0, keywords=[], timeframe='today 5-y'):
    pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25), retries=2, backoff_factor=0.1, requests_args={'verify':False})
    
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
# keywords = ['magic mushrooms', 'mushrooms', 'psychedelic']
# data = google_interest_over_time(keywords)
# print(data)

data = google_trends(geo='CA', api_method='trending searches')
data.to_csv('google_data.csv')