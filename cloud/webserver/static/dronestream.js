let peerConnection = new RTCPeerConnection()
let datachannel

async function getData(id) {
const url = "https://localhost/request";
const response = await fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({'id': id})
});
//console.log(response.json())
return response.json()
}

async function watchStream(streamId) {

    data = await getData(streamId)
    console.log('data')
    console.log(data)
    const pc = new RTCPeerConnection()

    pc.ontrack = (event) => {
        const video = document.getElementById('drone-stream')
        if (video) {
            video.srcObject = event.streams[0]
        }
    }
    pc.ondatachannel = (event) => {
        console.log('channel')
        console.log(event.channel)
        datachannel = event.channel
    }
    await pc.setRemoteDescription(new RTCSessionDescription(data.offer));
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);

    const url = "https://localhost/answer";
    console.log(JSON.stringify({'stream_id': streamId, "answer": {
        "type": pc.localDescription.type,
        "sdp": pc.localDescription.sdp
    }}))
    const response = await fetch(url, {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({'stream_id': streamId, "answer": {
        "type": pc.localDescription.type,
        "sdp": pc.localDescription.sdp
    }})

    });
    console.log(response.json())

}

// init()
const drone_id = document.getElementById('videos')
watchStream(drone_id.dataset.droneId)


document.addEventListener('keypress', function(event){
    if (!event.repeat){
    console.log(event.key)
    datachannel.send(event.key)
    }
})

document.addEventListener('keyup', function(event){
    console.log('stop:', event.key)
    datachannel.send('stop ' + event.key)
})
// document.getElementById('create-answer').addEventListener('click', createAnswer)
// document.getElementById('add-answer').addEventListener('click', addAnswer)