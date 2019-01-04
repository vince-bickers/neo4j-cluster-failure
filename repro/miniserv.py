from flask import Flask
from waitress import serve

app = Flask(__name__)

# Just serving nothing to keep the Docker container running
serve(app)
