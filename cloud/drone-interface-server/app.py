from flask import Flask, render_template, request, jsonify
import time
import ssl
import grpc
import ServerBaseStation_pb2, ServerBaseStation_pb2_grpc
import uuid
import asyncio
from threading import Thread

app = Flask(__name__)

address = f"localhost:50051"

channel =  grpc.aio.insecure_channel()
stub = ServerBaseStation_pb2_grpc.WebserverDroneCommuncationDetailsStub(channel)

communication = ServerBaseStation_pb2_grpc.DroneWebRtcServicer

@app.route('/')
def main():
    drones = stub.RequestAvailableDrones()
    return render_template('droneview.html', channel=communication)

@app.route('/request', methods = ['POST'])
async def somethingelse():
    data = request.get_json()
    id = data['id']
    if id not in communication:
        print(id)
        return jsonify({})
    channel = communication[id]
    channel.requested = True
    print(id, 'request true')
    while not channel.offer:
        await asyncio.sleep(0.5)
    print('read offer')
    offer = jsonify(channel.offer)
    channel.offer = {}
    return offer

@app.route('/answer', methods = ['POST'])
def answer():
    data = request.get_json()
    id = data['stream_id']
    communication[id].answer = data
    response = {}
    # print(data)
    return jsonify(response)



if __name__ == '__main__':
    # identifier = stub.Connect(ServerBaseStation_pb2.ConnectToCloudRequest(name='name'))

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')

    thread = Thread(target=app.run,
    args=('0.0.0.0',), kwargs=dict(port=443, ssl_context=context, debug=False, use_reloader=False))
    thread.start()