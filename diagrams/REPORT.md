# REPORT


## IMPLEMENTATION

Taking inspiration from the research made prior and following the steps of other systems [reference here from report](TBD) we started with the main goal of building a system that could interact with multiple cameras and drones. We decided that there should be a basestation that would act as a fog node where the cameras and drones could connect to and that would then establish connection with the cloud where the heavy lifting would be done. We assumed that the basestation could be any computer from small computer like a raspberry pi to a full desktop with the latter performing much better. With this in mind we assigned the functionalities of our system assuming that the basestation could not be a very powerfull machine and for this reason it will act as a just proxy for sending video and receiving commands to control the drone.

The cloud is then responsible for processing the video and evaluating if any threats are present, to record the video from all the cameras so it can be accessible later and to alert the users in this case.

With the responsabilities of each node clearly separated we could now see them as distinct entities that could be worked on independently as long as we defined the medium of communication between them. In the spirit of proceding with this separation and based on [Reference to webrtc]() we chose to stream the video from the basestation to the cloud in order to have the lower possible latency. This was also an important decision being that our ambition was to remote control the drone through the browser and WebRtc offers the best latency since it establishes a direct connection from the user to the server (in this case the basestation). On top of that webrtc encrypts the video that is sent which fits our use case perfectly.

Now we had the video streaming protocol and had to decide on how the webrtc connection could be established as well as general connection from the basestation to the cloud. Grpc [Reference to grpc]() presented the best option since it presents a great solution for the master-slaves architecture (the cloud being the master and the multiple basestations being the slaves) we were envisioning. The cloud would be running a grpc server to which the basestations could make requests to perform their multiple functions (connection, disconnection, setup webrtc connection). Another positive part of this technology is the fact that it is language agnostic meaning the basestation code could later be replaced with a better performing language without the need for changes on the cloud or vice-versa. It also allows for channel encryption in order to make sure all data exchanged between them is secure.

To summarize, the main functional responsabilities of the system should be:

Basestation:
* Connect To Cloud
* Disconnect from Cloud
* Allow user to register new cameras and drones
* Gather video from registered cameras
* Send video to cloud
* Act as proxy for drone remote control

Cloud:
* Manage basestations
* Receive video
* Evaluate, record and show video from cameras
* Allow the user to establish connection to the drone

With this defined we could now focus on each part individually.