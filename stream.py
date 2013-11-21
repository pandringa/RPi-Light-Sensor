import urllib
import urllib2
from random import randint


def create_datastream(name, value, feedID, key = 'CgG1MFaXSc2HyJAku-xB93v3rLCSAKxLTTZCbFM2eHZQaz0g'):
   nameValid = True
   name = str(name)
   for i in range(len(name)):
      if name[i] == " ":
         nameValid = False

   if not nameValid:
      print "Invalid Data Stream name: Should not include spaces"
   else:
      url = "http://api.cosm.com/v2/feeds/"+str(feedID)+"/datastreams"
      f = open("datafile.json", "w")
      f.write('{"version":"1.0.0","datastreams" : [{"id" : "'+name+'"}]}')
      f.close()
            
      headers = { 'X-ApiKey' : key }
      data = open("datafile.json").read()

      req = urllib2.Request(url, data, headers)
      response = urllib2.urlopen(req)
      the_page = response.read()


create_datastream("0", 1000, 98565)
