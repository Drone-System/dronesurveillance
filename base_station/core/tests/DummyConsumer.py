from flask import Flask, Response
from kafka import KafkaConsumer
import sys
import datetime


topic = "0_0"
consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'])
consumer.subscribe(topics=[topic])
app = Flask(__name__)

@app.route('/')
def index():
    cons = KafkaConsumer(bootstrap_servers=['localhost:9092'])
    print(cons.topics())
    a = ""
    for topic in cons.topics():
        a += topic
    return a

# @app.route('/kaf/', methods=['GET'])
# def video():
#     return Response(kafks(), mimetype='multipart/x-mixed-replace; boundary=frame')
#     # print("Request")
#     # return kafks()

# def kafks():
#     while True:
#         frame = consumer.poll()
#         if frame is not None:
#             print(frame)
#             # Process the order
#             yield str(frame)
#             consumer.commit(frame)  # Mark order as completed
#     # for message in consumer:
#     #     if message.topic != "0_0":
#     #         continue
#     #     print("1- ", datetime.datetime.now())
#     #     yield (b'--frame\r\n'
#     #     b'Content-Type: image/jpg\r\n\r\n' + message.value + b'\r\n\r\n')
#         # # print(message.value)
#         # return message.value

@app.route('/kaf/', methods=['GET'])
def video():
    return Response(kafks(), mimetype='multipart/x-mixed-replace; boundary=frame')
    # print("Request")
    # return kafks()

def kafks():
    for message in consumer:
        if message.topic != topic:
            continue
        yield (b'--frame\r\n'
        b'Content-Type: image/jpg\r\n\r\n' + message.value + b'\r\n\r\n')
        # # print(message.value)
        # return message.value

if __name__ == "__main__":
    app.run(host="0.0.0.0")