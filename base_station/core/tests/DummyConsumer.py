from flask import Flask, Response
from kafka import KafkaConsumer
import sys
import datetime


topic = "0_0"
consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'])
consumer.subscribe(topics=["0_0", "0_1"])
# consumer2 = KafkaConsumer("0_1", bootstrap_servers=['localhost:9092'])
app = Flask(__name__)

@app.route('/')
def index():
    cons = KafkaConsumer(bootstrap_servers=['localhost:9092'])
    print(cons.topics())
    a = ""
    for topic in cons.topics():
        a += topic
    return a

@app.route('/kaf/', methods=['GET'])
def video():
    return Response(kafks(), mimetype='multipart/x-mixed-replace; boundary=frame')
    # print("Request")
    # return kafks()

def kafks():
    for message in consumer:
        if message.topic != "0_1":
            continue
        print("1- ", datetime.datetime.now())
        yield (b'--frame\r\n'
        b'Content-Type: image/jpg\r\n\r\n' + message.value + b'\r\n\r\n')
        # # print(message.value)
        # return message.value

@app.route('/kaf2/', methods=['GET'])
def video2():
    return Response(kafks1(), mimetype='multipart/x-mixed-replace; boundary=frame')
    # print("Request")
    # return kafks()

def kafks1():
    for message in consumer:
        if message.topic != "0_1":
            continue
        print("2", datetime.datetime.now())
        yield (b'--frame\r\n'
        b'Content-Type: image/jpg\r\n\r\n' + message.value + b'\r\n\r\n')
        # # print(message.value)
        # return message.value

if __name__ == "__main__":
    app.run(host="0.0.0.0")