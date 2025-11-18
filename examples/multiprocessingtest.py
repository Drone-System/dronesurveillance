from multiprocessing import Process, Pipe
import asyncio
from time import sleep
from random import sample, randint
import os

class Test:
    def __init__(self, i):
        self.i = i


    def __del__(self):
        print("Deleting everything")

async def real(a: list):
    test = Test(10)
    for i in a:
        print(os.getpid(), i)
        sleep(2)

async def doNothing():
    pass

def run(a: list, conn: Pipe):
    loop = asyncio.new_event_loop()
    loop.create_task(real(a))
    # asyncio.run(real(a))
    # print("Finished")
    while True:
        if conn.poll(timeout=1):
            a = conn.recv()
            print(a)
            print(os.getpid(), "polled")
            if a == "False":
                print("RECEIVED")
                loop.run_until_complete(doNothing())
                loop.close()
                print("Exiting?")
                exit(0)
        
    exit(0)


if __name__ == "__main__":
    l = []
    conn = []
    for i in range(2):
        parent_conn, child_conn = Pipe()
        l.append(Process(target=run, args=(sample(range(1, 100), 10), child_conn)))
        conn.append(parent_conn)

    for p in l:
        p.start()
    alive = True
    while (alive):
        # print("alive")
        alive = False
        sleep(2)
        for i in range(len(l)):
            p = l[i]
            if (p.is_alive()):
                alive = True
                # print("sent")
                conn[i].send("False")

    print("exiting...")