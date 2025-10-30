#ifndef BACKEND_DEVICES_DEVICE_H
#define BACKEND_DEVICES_DEVICE_H

#include <string>
#include <stdint.h>

class Device {

public:
    Device(std::string& ip, uint8_t port) : ip(ip), port(port) {}
    void receive() {};
    void send() {};

    std::string getIp() const {
        return ip;
    }
    uint8_t getPort() const {
        return port;
    }
private:
    std::string ip;
    uint8_t port;

};

#endif //BACKEND_DEVICES_DEVICE_H