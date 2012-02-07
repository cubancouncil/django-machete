import simplejson
from urllib import urlencode
from urllib2 import urlopen
from django.conf import settings

"""
Handy Google maps geocode search functions
"""

def find_geo_point(location):
    
    """
    Attempt to resolve ``location`` using Google's geocoder. Returns a tuple with the canonical address and a tuple containing longitude/latitude
    or False if no result found
    """
    
    geo_content = find_geo(location)
    
    if geo_content:
        placemark = geo_content['Placemark'][0]
        lng, lat = placemark['Point']['coordinates'][:2]
        return (placemark['address'], (lng, lat,),)
    else:
        return False;

def find_geo(location):
    
    """
    Query Google maps for geo information
    """
 
    # Encode the request
    
    data = urlencode({
        'q': location,
        'output': "json",
        'oe': "utf8",
        'sensor': "false",
        'key': settings.GOOGLE_MAPS_API_KEY
    })
    
    url = "http://maps.google.com/maps/geo?%s" % data
    
    try:
        response = urlopen(url)
        geo_content = simplejson.loads(response.read())
        if geo_content['Status']['code'] == 200:
            return geo_content
        else:
            raise
    except:
        return False