from flask import Flask, render_template, request, jsonify
import time
import ssl
import grpc
import ServerBaseStation_pb2, ServerBaseStation_pb2_grpc
import uuid
import asyncio
from threading import Thread

app = Flask(__name__)

communication = {}

@app.route('/')
def main():
    return render_template('index.html', channel=communication)

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

class Channel:
    def __init__(self):
        self.requested:bool=False
        self.offer = {}
        self.answer = {}

class DroneWebRtc(ServerBaseStation_pb2_grpc.DroneWebRtcServicer):
    def __init__(self, communication):
        self.communication = communication

    async def Connect(
        self,
        request: ServerBaseStation_pb2.ConnectRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.ConnectResponse:
        stream_id=str(uuid.uuid4())
        self.communication.update({stream_id:Channel()})
        print('connect')
        return ServerBaseStation_pb2.ConnectResponse(stream_id=stream_id)
    
    async def Stream(
        self,
        request: ServerBaseStation_pb2.StreamOffer,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.StreamAnswer:
        offer = {'stream_id':request.stream_id,'offer':{'type':request.offer.type, 'sdp':request.offer.sdp}}
        comm = self.communication[request.stream_id]
        comm.offer = offer
        while not comm.answer:
            await asyncio.sleep(0.5)

        print(comm.answer)
        answer = ServerBaseStation_pb2.StreamAnswer(stream_id=comm.answer['stream_id'], 
                                      answer=ServerBaseStation_pb2.StreamDesc(
                                          type=comm.answer['answer']['type'],
                                          sdp=comm.answer['answer']['sdp']),
                                      )
        comm.answer = {}
        return answer

    async def Poll(
        self,
        request: ServerBaseStation_pb2.PollRequest,
        context: grpc.aio.ServicerContext,
    ) -> ServerBaseStation_pb2.PollResponse:
        id = request.stream_id
        return ServerBaseStation_pb2.PollResponse(stream_needed=self.communication[id].requested)

async def main():
    server = grpc.aio.server()
    ServerBaseStation_pb2_grpc.add_DroneWebRtcServicer_to_server(DroneWebRtc(communication), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    print("Starting server on ", listen_addr)
    await server.start()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')
    #asyncio.ensure_future(app.run('0.0.0.0', port=443, ssl_context=context, debug=False, use_reloader=False))
    #app.run('0.0.0.0', port=443, ssl_context=context, debug=True)
    await server.wait_for_termination()

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')

    thread = Thread(target=app.run,
    args=('0.0.0.0',), kwargs=dict(port=443, ssl_context=context, debug=False, use_reloader=False))
    thread.start()
    asyncio.run(main())