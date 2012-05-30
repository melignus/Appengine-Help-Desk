import re, os, inspect, sys, datetime
from functools import wraps

thisPath = os.path.dirname(inspect.getfile(inspect.currentframe()))+'/'
if thisPath == '/':
    thisPath = './'
sys.path.append(thisPath+'libs/')

from flask import Flask, Response, redirect, \
        url_for, request, session, abort, \
        render_template, json, jsonify

# Google App Engine Block
try:
    import logging
    from google.appengine.api import \
            mail, users
    from google.appengine.ext.webapp.util import \
            run_wsgi_app
    from google.appengine.ext import \
            db
    run_on_google = True
except:
    run_on_google = False

sites = [
        'DIST',
        'WHS',
        'EHS',
        'FVHS',
        'MHS',
        'OVHS',
        'HBHS',
        'VVHS',
        'HBAS',
        'CDS',
        'CHS',
        'Food Services',
        'Transportation',
        ]

app = Flask(__name__)

page_params = {}

class Support_Ticket(db.Model):
    ticket_type = db.StringProperty()
    user_type = db.StringProperty()
    site = db.StringProperty()
    macro = db.StringProperty()
    micro = db.StringProperty()
    
    submitted_on = db.DateTimeProperty(auto_now_add=True)
    submitted_by = db.UserProperty()
    
    completed_on = db.DateTimeProperty()
    completed_by = db.UserProperty()

    assigned_to = db.UserProperty()
    description = db.StringProperty()

#    def __init__(self, ticket_type, user_type, site, macro, micro, submitted_by):
#        self.ticket_type = ticket_type
#        self.user_type = user_type
#        self.site = site
#        self.macro = macro
#        self.micro = micro
#        self.submitted_by = submitted_by
#        self.submitted_on = datetime.datetime.now()

@app.route('/')
def home():
    if run_on_google:
        logging.info(users.get_current_user())
        this_user = str(users.get_current_user())+'@hbuhsd.edu'
    else:
        this_user = 'test@hbuhsd.edu'

    page_params['title'] = 'Ticket Manager'
    page_params['message'] = 'tickets displayed are for user %s' % this_user
    return render_template('home.html', page_params=page_params)

@app.route('/new_ticket', methods=['POST', 'GET', 'PUT', 'DELETE'])
def new_ticket():
    if run_on_google:
        logging.info(users.get_current_user())
        this_user = str(users.get_current_user())+'@hbuhsd.edu'
    else:
        this_user = 'test@hbuhsd.edu'

    if request.method == 'POST':
        logging.info(request.form)
        these_params = request.form
        this_ticket = Support_Ticket(
                ticket_type=these_params['ticketType'],
                user_type=these_params['ticketUserType'],
                site=these_params['ticketSite'],
                macro=these_params['ticketMacroLocation'],
                micro=these_params['ticketMicroLocation'],
                description=these_params['ticketDescription'],
                submitted_by=users.get_current_user(),
                )
        this_ticket.put()
        return jsonify({'message': 'OK'})

    page_params['sites'] = sites
    page_params['title'] = 'New Ticket'
    page_params['message'] = 'please fill all fields to submit a new support ticket'
    return render_template('new_ticket.html', page_params=page_params)

@app.route('/ticket/<ticket_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def ticket(ticket_id):
    logging.info('method: %s' % request.method)
    logging.info('ticket_id: %s' % ticket_id)
    if request.method == 'GET':
        this_query = Support_Ticket.get_by_id(int(ticket_id))
        this_ticket = {
                'ticketType': this_query.ticket_type,
                'ticketUserType': this_query.user_type,
                'ticketMacroLocation': this_query.macro,
                'ticketSubmittedOn': str(this_query.submitted_on),
                'ticketSubmittedBy': str(this_query.submitted_by),
                'id': str(this_query.key().id()),
                }
        return Response(response=json.dumps(this_ticket), mimetype="application/json")
    else:
        return jsonify({'message': 'ERROR'})

@app.route('/tickets', methods=['GET'])
def tickets():
    logging.info('request: %s' % request)
    this_query = Support_Ticket.gql("WHERE submitted_by = :submitted_by", submitted_by=users.get_current_user())
    these_tickets = [
            {
                'ticketType': ticket.ticket_type,
                'ticketUserType': ticket.user_type,
                'ticketMacroLocation': ticket.macro,
                'ticketSubmittedOn': str(ticket.submitted_on),
                'ticketSubmittedBy': str(ticket.submitted_by),
                'id': str(ticket.key().id()),
            } for ticket in this_query]

    logging.info(these_tickets)
    return Response(response=json.dumps(these_tickets), mimetype="application/json")
    #return jsonify(these_tickets)#{'message': 'OK'})

@app.route('/test', methods=['POST', 'GET', 'PUT', 'DELETE'])
def test():
    return jsonify({'message': 'OK'})

@app.errorhandler(404)
def page_not_found(error):
    page_params['title'] = '404'
    page_params['message'] = 'The page you are looking for cannot be found'
    return render_template('404.html', page_params=page_params)

@app.errorhandler(403)
def http_forbidden(error):
    page_params['title'] = '403'
    page_params['message'] = 'Access to this page is restricted to HBUHSD staff only. To access this page you must have a valid @hbuhsd.edu email account'
    return render_template('403.html', page_params=page_params)

if __name__ == "__main__":
    if run_on_google == False:
        app.run(
                debug=True,
                host='0.0.0.0',
                port=5000,
                )
    else:
        run_wsgi_app(app)
