# Secure Drone Surveillance System for Critical Infrastructure
*Description:* Develop a secure drone-based surveillance solution for infrastructure such
as bridges or restricted industrial areas. The drone will capture real-time video streams
and transmit them to a cloud backend, where object detection models (e.g., YOLO) can
identify specific threats (e.g., intrusions, hazardous events). Data should be encrypted and
securely transferred. The platform must include a dashboard for event replay, monitoring
alerts, and secured user access.
*Learning Outcomes:* Integrate drones and camera feeds into a secure streaming pipeline.
Use onboard or edge AI for object detection and classification. Implement encrypted
transmission and storage of media data. Build user dashboards for secure alert review and
video access.
*Milestones:* 1. Drone or simulated camera setup and integration. 2. Object detection
model deployment and tuning. 3. Cloud backend for alert processing and encrypted
storage. 4. Dashboard development for authorized user interaction. 5. Final testing in
simulated security incident scenarios.


#

## TODOS

* [x] Adjust database to not have groups
* [x] Connect cloud webserver to proper database and ajust permissions
* [x] Make basestation add and basestation user add and remove work
* [x] Develop Proxy server with grpc server
* [x] Show cameras in browser
* [ ] Filter cameras by basestation with permissions
* [ ] Make Grpc use secure connection
* [x] Develop Drone manager
* [ ] Integrate basestation webserver with core and database
* [x] Integrate drone manager with camera manager
* [ ] Deploy cloud part with IaC into aws
* [ ] CELEBRATE