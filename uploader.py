import os
from flask import Flask
from werkzeug.utils import secure_filename
UPLOAD_FOLDER = './static/users'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # limiting size of file to 16 megabyte


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def change_name(filename, new_value):
    return filename.replace(filename.rsplit('.', 1)[0], new_value)


def save_file(image, new_value):
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        filename = change_name(filename, new_value)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    else:
        return False
