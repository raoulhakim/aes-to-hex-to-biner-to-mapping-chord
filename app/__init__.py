from flask import Flask
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'rahasia-kunci-sementara'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app/static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 100000 * 1024 * 1024  # 100 GB Max size file yang di decrypt
app.config['CHORD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Chord')

# Pastikan folder upload ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from app import routes 