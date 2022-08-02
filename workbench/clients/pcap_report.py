"""This client pulls PCAP 'views' (view summarize what's in a sample)."""

import zerorpc
import os
import pprint
from . import client_helper
import flask

STATIC_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'static/')

APP = flask.Flask(__name__, template_folder=STATIC_DIR,
                  static_folder=STATIC_DIR, static_url_path='')

WORKBENCH = None

def run():
    """This client pulls PCAP files for building report.

    Returns:
        A list with `view_pcap` , `meta` and `filename` objects.
    """

    global WORKBENCH
    
    # Grab grab_server_argsrver args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    WORKBENCH = zerorpc.Client(timeout=300, heartbeat=60)
    WORKBENCH.connect('tcp://'+args['server']+':'+args['port'])

    data_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '../data/pcap')
    file_list = [os.path.join(data_path, child) for child in \
                os.listdir(data_path)]
    results = []
    for filename in file_list:

        # Skip OS generated files
        if '.DS_Store' in filename: continue

        # Process the pcap file
        with open(filename,'rb') as f:
            md5 = WORKBENCH.store_sample(f.read(), filename, 'pcap')
            result = WORKBENCH.work_request('view_pcap', md5)
            result.update(WORKBENCH.work_request('meta', result['view_pcap']['md5']))
            result['filename'] = result['meta']['filename'].split('/')[-1]
            results.append(result)

    return results

@APP.route('/')
def flask_app():
    '''Return redered template for the flask app'''
    results = run()
    return flask.render_template('templates/index.html', results=results)

@APP.route('/files/<md5>/')
def show_files(md5):
    '''Renders template with `view` of the md5.'''
    if not WORKBENCH:
        return flask.redirect('/')

    md5_view = WORKBENCH.work_request('view', md5)
    return flask.render_template('templates/md5_view.html', md5_view=md5_view['view'], md5=md5)



@APP.route('/md5/<md5>/')
def show_md5_view(md5):
    '''Renders template with `stream_sample` of the md5.'''

    if not WORKBENCH:
        return flask.redirect('/')

    md5_view = WORKBENCH.stream_sample(md5)
    return flask.render_template('templates/md5_view.html', md5_view=list(md5_view), md5=md5)



def test():
    '''Tests for rendering pcap_report.'''
    run()

if __name__ == '__main__':
    APP.run(host='0.0.0.0', debug=True)

