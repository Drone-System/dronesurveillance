#include <iostream>
#include "managers/DeviceManager.h"
#include "database/DatabaseManager.h"
#include <libpq-fe.h>
int main()
{
    bool running = true;
    DeviceManager man{};
    DatabaseManager dbMan{};

    man.add("127.0.0.1", 22);
    man.print_devices();

    dbMan.doSomeTests();

    // while (running)
    // {
    //     std::cout << "This is Working\n";
    // }


    return 0;
}