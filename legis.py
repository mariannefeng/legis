from flask import Flask, request, render_template, Blueprint, jsonify, flash, redirect, url_for
from flask_socketio import SocketIO, emit
from dateutil.relativedelta import relativedelta
import datetime
import requests
import requests_cache
import random
import collections

import legis_legwork as leg
import VARS as vars


app = Flask(__name__)
socketio = SocketIO(app)

app.secret_key = 'super secret key'
# create additional static directory
blueprint = Blueprint('clouds', __name__, static_url_path='/clouds', static_folder='clouds/')
app.register_blueprint(blueprint)

# cache for requests
requests_cache.install_cache('test_cache', backend='sqlite', expire_after=300)

DATA_HOSTNAME = "localhost"
DATA_PORT = "5000"


@socketio.on('md change')
def md_change(data):
    md_change = open(vars.WHAT_WERE_DOING_MD, 'r+')
    md_change.truncate()

    md_change.write(str(data))
    md_change.close()
    emit('ACK', '')


@app.route('/')
def index():
    background_color = random.choice(vars.BULMA_COLORS)
    button_colors = [color for color in vars.BULMA_COLORS if color != background_color]
    button_color = random.choice(button_colors)
    return render_template('index.html',
                           background_color=background_color,
                           button_color=button_color)



@app.route('/thank_you')
def sources():
    with open(vars.THANK_YOU_MD, 'r') as z:
        content = z.read()
    parsed_text = content.strip()
    return render_template('md_template.html',
                           text=parsed_text,
                           title='Thank you')


@app.route('/whats_happenin')
def what_happen():
    with open(vars.WHAT_WERE_DOING_MD, 'r') as f:
        content = f.read()
    parsed_text = content.strip()
    return render_template('md_template.html',
                           text=parsed_text,
                           title='The official list of us doing things')


@app.route('/whats_happenin_edit')
def what_happen_edit():
    with open(vars.WHAT_WERE_DOING_MD, 'r') as f:
        content = f.read()
    return render_template('what_happen_edit.html', text=content.strip())


@app.route('/my_reps', methods=['POST'])
def return_data():
    errs = []
    for field, value in request.form.items():
        if not value:
            errs.append(field)
    if errs:
        if len(errs) == 1:
            flash("Field Required: {}".format(errs[0]).title())
        else:
            flash("Fields Required: {}".format(', '.join(errs)).title())
        return redirect(url_for('index'))

    human = leg.Constituent(**request.form)
    result = human.get_reps()
    if human.google_error:
        flash("Error from Google Civic API: {}".format(human.google_error))
        return redirect(url_for('index'))
    return render_template('reps.html', reps=result)

if __name__ == '__main__':
    socketio.run(app, port=5001, host="0.0.0.0")
