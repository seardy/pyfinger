from fingerprint import Fingerprint
import paho.mqtt.client as paho
import threading
import json

search_thread = None


def on_message(client, userdata, message):
    if message.topic == "enroll/begin":
        fp.abort = True
        data = json.loads(message.payload)
        global search_thread
        search_thread.join()
        fp.enroll(data['identificacion'])
	if fp.abort:
	  client.publish("enroll/abort","")
	  client.publish("search/finished","")
	  fp.abort = False
    if message.topic == "delete" :
        fp.abort = True
	global search_thread
	search_thread.join()
	fp.delete(message.payload)
        client.publish("search/finished", "")
	fp.abort = False
    if message.topic == "search/finished":
        search_thread = threading.Thread(target=fp.search)
        search_thread.start()

fp = Fingerprint()
client = paho.Client("routine")
client.connect("localhost")
client.on_message = on_message
client.subscribe("search/finished")
client.subscribe("enroll/begin")
client.subscribe("delete")
client.loop_forever()
