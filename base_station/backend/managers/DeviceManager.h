#ifndef BACKEND_MANAGERS_DEVICEMANAGER_H
#define BACKEND_MANAGERS_DEVICEMANAGER_H

#include <vector>
#include "devices/device.h"

class DeviceManager {

public:
    DeviceManager() {};

    void add(std::string ip, uint8_t port)
    {
        std::cout << "Added device\n";
        v.push_back(Device{ip, port});
    }

    void print_devices() const {
        for (auto& d: v) {
            std::cout << d.getIp() << ":" << static_cast<int>(d.getPort()) << "\n";
        }
    }
private:
    std::vector<Device> v;

};

#endif //BACKEND_MANAGERS_DEVICEMANAGER_H