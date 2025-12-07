from datetime import datetime, timedelta
import psycopg
import time
class Database:
    def __init__(self):
        # -------------------- Database --------------------
        # Retry connection logic for Docker startup
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try: # THIS SHOULD BE PASSED IN CONSTRUCTOR
                self.conn = psycopg.connect(
                    host="db",
                    dbname="db",
                    user="postgres",
                    password="mysecretpassword",
                    port="5432",
                    autocommit=True
                )
                print("Database connection successful!")
                break
            except psycopg.OperationalError as e:
                if attempt < max_retries - 1:
                    print(f"Database connection attempt {attempt + 1} failed. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to connect to database after {max_retries} attempts")
                    raise

        self.times = {}

        
    def registerBasestation(self, basestation_name: str, password: str) -> int:

        # add basestation name
        id = -1
        # return id
        with self.conn.cursor() as cur:
            cur.execute("CALL create_basestation(%s, %s)", basestation_name, password)
            cur.execute("SELECT id from basestations where name=%s", basestation_name)
            row = cur.fetchone()
            id = row[0]
        self.time[id] = datetime.now()

        return id

    def removeBasestation(self, basestation_id: int) -> bool:

        # remove from db with id

        # return true if success false if not

        return True

    def updateTime(self, basestation_id: int) -> bool:
        if basestation_id in self.times:
            self.times[basestation_id] = datetime.now()
            return True
        return False
    
    def doCleanUp(self) -> int:
        # return number of basestations deleted
        to_delete = []
        for basestation, time in self.times:
            if datetime.now() >= time + timedelta(minutes=5):
                to_delete.append(basestation)
        
        res = 0
        for b in to_delete:
            if self.removeBasestation(b):
                res += 1

        return res
    
    def getBasestations(self):
        res = []
        with self.conn.cursor() as cur:
            cur.execute("SELECT id from basestations")
            res = cur.fetchall()
            # id = row[0]
        return [e[0] for e in res]
