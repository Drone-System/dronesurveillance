from flask import Flask, render_template
import pandas as pd
import psycopg

conn = psycopg.connect(
    host="host.docker.internal",
    dbname="db",    
    user="some-postgres",
    password="mysecretpassword",
    port="5432"
)

app = Flask(__name__)

data = pd.read_sql('select name, ip from basestations', conn)

@app.route("/")
def home():
    # Convert DataFrame to list of dictionaries
    items = data.to_dict('records')
    return render_template("index.html", items=items)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)