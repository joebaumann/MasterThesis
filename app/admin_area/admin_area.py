"""
This file is just for testing purposes and can be deleted at any time...
"""


import glob
import json
import os
from datetime import datetime

import boto3
import config
import xmltodict
from flask import (Blueprint, Markup, current_app, flash, redirect,
                   render_template, request, session, url_for)
from functools import wraps


admin_area_bp = Blueprint('admin_area_bp', __name__)


# ----------------------------------------------------------------
# setup users
# ----------------------------------------------------------------

class User:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return f'<User: {self.username}>'


users = []

for u in config.USERS:
    users.append(
        User(id=u['id'], username=u['username'], password=u['password']))


def login_required_AdminArea(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # check if user is logged in
        if 'user_id' not in session:
            # return to login page if user is not logged in yet
            flash("Not logged in.", "error")
            return redirect(url_for('admin_area_bp.login'))
        # user is logged in, so continue with desired route
        return f(*args, **kwargs)
    return decorated_function


# ----------------------------------------------------------------
# MTurk Helper functions
# ----------------------------------------------------------------

def checkConnection(client_mturk_environment):
    if 'AWS_credentials' in session:

        environments = {
            "production": {
                "endpoint": "https://mturk-requester.us-east-1.amazonaws.com",
                "preview": "https://www.mturk.com/mturk/preview"
            },
            "sandbox": {
                "endpoint": "https://mturk-requester-sandbox.us-east-1.amazonaws.com",
                "preview": "https://workersandbox.mturk.com/mturk/preview"
            },
        }
        mturk_environment = environments[client_mturk_environment]

        client = boto3.client(
            service_name='mturk',
            aws_access_key_id=session['AWS_credentials']['AWS_ACCESS_KEY'],
            aws_secret_access_key=session['AWS_credentials']['AWS_SECRET_ACCESS_KEY'],
            region_name='us-east-1',
            endpoint_url=mturk_environment['endpoint'],
        )

        try:
            connection = True
            account_balance = client.get_account_balance()['AvailableBalance']
        except Exception as e:
            error_message = "Could not set up AWS client! || Error message: " + \
                str(e)
            print(error_message)
            connection = False
            account_balance = None


    else:
        connection = False
        client = False
        account_balance = None
        # AWS_credentials are not stored in session. Login in AWS is necessary, therefore redirect to AWS login page
    return connection, client, account_balance


def getMTurkPreview(client_mturk_environment):

    environments = {
        "production": {
            "endpoint": "https://mturk-requester.us-east-1.amazonaws.com",
            "preview": "https://www.mturk.com/mturk/preview"
        },
        "sandbox": {
            "endpoint": "https://mturk-requester-sandbox.us-east-1.amazonaws.com",
            "preview": "https://workersandbox.mturk.com/mturk/preview"
        },
    }

    return environments[client_mturk_environment]['preview']


def getAllHITs(environment):
    """[summary]

    # we set MaxResults=100 since boto3's 'list_hits' method does not allow a 'MaxResults' value bigger than 100. Default 'MaxResults' value is would be 10.

    Parameters
    ----------
    environment : [type]
        [description]

    Returns
    -------
    [type]
        [description]
    """
    connection, client, account_balance = checkConnection(environment)

    next_token = ''

    allHits = []

    while next_token is not None:
        if next_token == '':
            response = client.list_hits()
        else:
            response = client.list_hits(NextToken=next_token)

        next_token = response.get('NextToken', None)
        current_batch = [r for r in response['HITs']]
        allHits += current_batch

    return allHits


def getAllAssignments(HITId, environment):
    """[summary]

    # we set MaxResults=100 since boto3's 'list_assignments_for_hit' method does not allow a 'MaxResults' value bigger than 100. Default 'MaxResults' value is would be 10.

    Parameters
    ----------
    HITId : [type]
        [description]
    environment : [type]
        [description]

    Returns
    -------
    [type]
        [description]
    """

    connection, client, account_balance = checkConnection(environment)

    next_token = ''

    NumResults = 0
    Assignments = []
    while next_token is not None:
        if next_token == '':
            response = client.list_assignments_for_hit(
                HITId=HITId,
                MaxResults=100,
            )
        else:
            response = client.list_assignments_for_hit(
                HITId=HITId,
                MaxResults=100,
                NextToken=next_token
            )

        next_token = response.get('NextToken', None)
        current_batch = [r for r in response['Assignments']]
        NumResults += response['NumResults']
        Assignments += current_batch

    return {'NumResults': NumResults, 'Assignments': Assignments}


def getAllQualifications(environment):

    connection, client, account_balance = checkConnection(environment)
    next_token = ''

    qualifications = []

    while next_token is not None:

        if next_token == '':
            response = client.list_qualification_types(
                MustBeRequestable=True,
                MustBeOwnedByCaller=True,
                MaxResults=100
            )
        else:
            response = client.list_qualification_types(
                MustBeRequestable=True,
                MustBeOwnedByCaller=True,
                MaxResults=100,
                NextToken=next_token)

        next_token = response.get('NextToken', None)
        qualifications += response['QualificationTypes']


    return qualifications


def getAllWorkersAssociatedWithQualifications(environment, qual_id):
    connection, client, account_balance = checkConnection(environment)
    next_token = ''

    workers = []
    number_of_workers = 0

    while next_token is not None:

        if next_token == '':
            response = client.list_workers_with_qualification_type(
                QualificationTypeId=qual_id,
                MaxResults=100)

        else:
            response = client.list_workers_with_qualification_type(
                QualificationTypeId=qual_id,
                MaxResults=100,
                NextToken=next_token)

        # current_batch = [{'QualificationTypeId': res['QualificationTypeId'], 'WorkerId':res['WorkerId']} for res in response['Qualifications']]
        next_token = response.get('NextToken', None)
        workers += response['Qualifications']
        number_of_workers += response['NumResults']


    return number_of_workers, workers


def getAllBlockedWorkers(environment, client):
    next_token = ''

    workers = []
    number_of_workers = 0

    while next_token is not None:

        if next_token == '':
            response = client.list_worker_blocks(
                MaxResults=100)

        else:
            response = client.list_worker_blocks(
                NextToken=next_token,
                MaxResults=100)

        next_token = response.get('NextToken', None)
        workers += response['WorkerBlocks']
        number_of_workers += response['NumResults']

    return workers, number_of_workers


# ----------------------------------------------------------------
# Flask api routes
# ----------------------------------------------------------------


@admin_area_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)

        username = request.form['username']
        password = request.form['password']

        try:
            # check if username exists
            user = [x for x in users if x.username == username][0]
            if user and user.password == password:
                session['user_id'] = user.id
                flash(f"Login successfull, {user.username}!", "success")
                return redirect(url_for('admin_area_bp.home'))

            flash(f"Wrong password for user '{user.username}'!", "error")

            return redirect(url_for('admin_area_bp.login'))

        except Exception as e:
            error_message = "Username does not exist! <br> Error message: " + \
                str(e)
            print(error_message)
            flash(Markup(error_message), "error")

    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']][0]
        flash(f"Already logged in to Admin Area!", "info")
        return redirect(url_for('admin_area_bp.home'))

    return render_template('admin_area/login.html')


@admin_area_bp.route('/logout')
def logout():
    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']][0]
        flash(
            f"You have been logged out from the Admin Area, {user.username}!", "success")
    else:
        flash("Already logged out from the Admin Area.", "info")

    session.pop('user_id', None)
    return redirect(url_for('admin_area_bp.login'))


@admin_area_bp.route('/login_AWS', methods=['GET', 'POST'])
def login_AWS():
    if request.method == 'POST':
        session.pop('AWS_credentials', None)

        AWS_ACCESS_KEY = request.form['AWS_ACCESS_KEY']
        AWS_SECRET_ACCESS_KEY = request.form['AWS_SECRET_ACCESS_KEY']
        environment = request.form['environment']

        session['AWS_credentials'] = {
            'AWS_ACCESS_KEY': AWS_ACCESS_KEY, 'AWS_SECRET_ACCESS_KEY': AWS_SECRET_ACCESS_KEY}

        connection, client, account_balance = checkConnection(environment)
        if connection is False:
            message = f"Could not set up AWS client for AWS_ACCESS_KEY '{AWS_ACCESS_KEY}'! Please login with your AWS credentials. Visit <a style='color: white;' target='_blank' rel='noopener noreferrer' href='https://blog.mturk.com/tutorial-setting-up-your-aws-account-to-make-use-of-mturks-api-4e405b8fc8cb'>this article</a> for more infos."
            flash(Markup(message), "error")
            session.pop('AWS_credentials', None)
            return redirect(url_for('admin_area_bp.login_AWS'))
        else:
            flash(
                f"AWS login successfull for AWS_ACCESS_KEY '{AWS_ACCESS_KEY}'!", "success")
            return redirect(url_for('admin_area_bp.checkconnection', client_mturk_environment='production'))

    return render_template('admin_area/login_AWS.html')


@admin_area_bp.route('/logout_AWS')
def logout_AWS():
    if 'AWS_credentials' in session:
        flash(f"You have been logged out from AWS!", "success")
    else:
        flash("Already logged out from AWS.", "info")

    session.pop('AWS_credentials', None)
    return redirect(url_for('admin_area_bp.login_AWS'))


@admin_area_bp.route('/')
@login_required_AdminArea
def home():
    return render_template('admin_area/home.html')


@admin_area_bp.route('/mturk_requester_actions/checkconnection/<client_mturk_environment>')
@login_required_AdminArea
def checkconnection(client_mturk_environment):
    connection, client, account_balance = checkConnection(
        client_mturk_environment)

    return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)


@admin_area_bp.route('/mturk_requester_actions/get_account_balance/<client_mturk_environment>')
@login_required_AdminArea
def get_account_balance(client_mturk_environment):

    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        return render_template('admin_area/get_account_balance.html', account_balance=account_balance, environment=client_mturk_environment)



@admin_area_bp.route('/mturk_requester_actions/hits/<client_mturk_environment>')
@login_required_AdminArea
def show_HITs(client_mturk_environment):

    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:

        hits = getAllHITs(client_mturk_environment)

        # get all qualifications
        quals = getAllQualifications(client_mturk_environment)
        # loop trough all qualifications and extend the qual-dicts so that there is an information included how many and which workers are associated with the respective qual
        qual_index = 0
        for qual in quals:
            number_of_associated_workers, associated_workers = getAllWorkersAssociatedWithQualifications(
                client_mturk_environment, qual['QualificationTypeId'])
            quals[qual_index]['number_of_associated_workers'] = number_of_associated_workers
            quals[qual_index]['associated_workers'] = associated_workers
            qual_index += 1

        hit_index = 0
        # now loop through all hits
        for hit in hits:
            hit_title = hit['Title']

            # check if there is any qualification which is associated with this hit
            for qual in quals:
                # if yes, add two key-value-pairs to hit so that hit-table in admin area can display whether there is an associated qual and how many workers are associated with this qual
                if qual['Name'] == hit_title:
                    hits[hit_index]['has_associated_qualification'] = True
                    hits[hit_index]['number_of_associated_workers'] = qual['number_of_associated_workers']
                    hits[hit_index]['associated_workers'] = [
                        ("id=" + str(worker['WorkerId']) + "|status=" + str(worker['Status'])) for worker in qual['associated_workers']]

            # if there is no associated qual for this hit, just fill in 'False' and '0'
            if 'has_associated_qualification' not in hits[hit_index]:
                hits[hit_index]['has_associated_qualification'] = False
                hits[hit_index]['number_of_associated_workers'] = 0
                hits[hit_index]['associated_workers'] = []

            hit_index += 1

        return render_template('admin_area/HITs.html', hits=hits, environment=client_mturk_environment)


@admin_area_bp.route('/mturk_requester_actions/hits/delete_hit')
def delete_hit():

    hit_id = request.args.get('hit_id')

    # we set the environment for the mturk client setup to 'sandbox', since we do not allow to delete hits in the productive mturk environment, even though it would technically be possible
    client_mturk_environment = 'sandbox'

    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        try:
            # Delete the hit
            response = client.delete_hit(HITId=hit_id)
            print("The hit was deleted with the following response:")
            print(response)
            message = "The hit with the ID '<i>" + hit_id + "</i>' was deleted!"
            flash(Markup(message), "success")
        except Exception as e:
            # the hit could not be deleted
            error_message = "The hit with the ID '" + hit_id + \
                "' COULD NOT be DELETED! <br> Error message: " + str(e)
            print(error_message)
            flash(Markup(error_message), "error")

    return "true"


@admin_area_bp.route('/mturk_requester_actions/hits/expire_hit')
def expire_hit():

    hit_id = request.args.get('hit_id')
    environment = request.args.get('environment')

    connection, client, account_balance = checkConnection(
        environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:

        try:
            # Expire the hit immediately
            response = client.update_expiration_for_hit(
                HITId=hit_id,
                ExpireAt=datetime(2015, 1, 1))
            print("")
            print("The hit with the ID '" + hit_id +
                  "' was immediately expired with the following response:")
            print("")
            message = "The hit with the ID '<i>" + hit_id + "</i>' was immediately expired!"
            flash(Markup(message), "success")
            print(response)

        except Exception as e:
            # the hit could not be expired
            error_message = "The hit with the ID '" + hit_id + \
                "' COULD NOT be EXPIRED! <br> Error message: " + str(e)
            print(error_message)
            flash(Markup(error_message), "error")

    return "true"


@admin_area_bp.route('/mturk_requester_actions/hits/associate_participants_with_this_HITs_qualification/<client_mturk_environment>')
def associate_participants_with_this_HITs_qualification(client_mturk_environment):

    hit_id = request.args.get('hit_id')
    hit_title = request.args.get('hit_title')

    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        # get all qualifications
        quals = getAllQualifications(client_mturk_environment)

        for qual in quals:
            # associate worker with qualification indicating they have completed a HIT with this title
            if qual['Name'] == hit_title:

                # get all workers who participated in this HIT
                assignments_for_hit = getAllAssignments(
                    hit_id, client_mturk_environment)

                # associate each of these workers with this HIT's qualification
                for assignment in assignments_for_hit['Assignments']:

                    response = client.associate_qualification_with_worker(
                        QualificationTypeId=qual['QualificationTypeId'],
                        WorkerId=assignment['WorkerId'],
                        IntegerValue=0,
                        SendNotification=False)

                    print("")
                    print("The qual (name=" + qual['Name'] + ") was associated with the worker (id=" +
                          assignment['WorkerId'] + ") with the following response:")
                    print(response)

                flash("All workers who participated in the HIT (Name='" + hit_title +
                      "') were associated with this HIT's qualification.", "success")

    return "true"


@admin_area_bp.route('/mturk_requester_actions/assignments/<client_mturk_environment>/')
@login_required_AdminArea
def show_assignments(client_mturk_environment):

    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:

        hits = client.list_hits(MaxResults=100)['HITs']

        return render_template('admin_area/assignments.html', hits=hits, environment=client_mturk_environment, assignments_for_hit=None)


@admin_area_bp.route('/mturk_requester_actions/assignments/<client_mturk_environment>/getassignments')
def get_assignments(client_mturk_environment):

    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:

        try:
            hit_id = request.args.get('hit_id')
        except:
            hit_id = None

        if hit_id is None:
            assignments_for_hit = None
        else:
            print("get assignment")
            assignments_for_hit = getAllAssignments(
                hit_id, client_mturk_environment)

        return assignments_for_hit


@admin_area_bp.route('/mturk_requester_actions/assignments/approve_assignment')
def approve_assignment():

    assignment_id = request.args.get('assignment_id')
    client_mturk_environment = request.args.get('client_mturk_environment')

    connection, client, account_balance = checkConnection(
        client_mturk_environment)

    # Approve the Assignment (if the assignments has been rejected before this action overrides it!)
    response = client.approve_assignment(
        AssignmentId=assignment_id,
        OverrideRejection=True
    )
    print("The assignment was approved with the following response:")
    print(response)

    return "true"


@admin_area_bp.route('/mturk_requester_actions/assignments/reject_assignment')
def reject_assignment():

    assignment_id = request.args.get('assignment_id')
    client_mturk_environment = request.args.get('client_mturk_environment')
    requester_feedback = request.args.get('requester_feedback')

    connection, client, account_balance = checkConnection(
        client_mturk_environment)

    # Reject the Assignment (if the assignments has been rejected before this action overrides it!)
    response = client.reject_assignment(
        AssignmentId=assignment_id,
        RequesterFeedback=requester_feedback
    )
    print("The assignment was rejected with the following response:")
    print(response)

    return "true"


@admin_area_bp.route('/mturk_requester_actions/assignments/pay_bonus')
def pay_bonus():

    assignment_id = request.args.get('assignment_id')
    worker_id = request.args.get('worker_id')
    bonus_amount = request.args.get('bonus_amount')
    client_mturk_environment = request.args.get('client_mturk_environment')
    requester_feedback = request.args.get('requester_feedback')

    connection, client, account_balance = checkConnection(
        client_mturk_environment)

    # Send a bonus to the worker
    response = client.send_bonus(
        WorkerId=worker_id,
        BonusAmount=bonus_amount,
        AssignmentId=assignment_id,
        Reason=requester_feedback
    )

    print("The bonus was paid with the following response:")
    print(response)

    return "true"



@admin_area_bp.route('/mturk_requester_actions/assignments/<client_mturk_environment>/get_worker_answers')
def get_worker_answers(client_mturk_environment):

    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        print("")
        try:
            hit = request.args.get('hit')
        except:
            print("hit is NONE !")
            hit = None

        if hit is None:
            assignments_for_hit = None
        else:
            print("get assignment")
            assignments_for_hit = getAllAssignments(
                hit, client_mturk_environment)

        return assignments_for_hit


@admin_area_bp.route('/mturk_requester_actions/create_hit_form/<client_mturk_environment>')
@login_required_AdminArea
def create_hit_form(client_mturk_environment):

    if 'hit_specifications' in session:
        hit_specifications = session['hit_specifications']
    else:
        hit_specifications = {}

    paragraphs = {}
    # loop trough all the directories which are in app/data/
    for batch_key, batch_specs in config.batches.items():
        # for each directory loop trough all json-files which where specified
        json_files = {}
        # get list of all json files in new entire_paper_path
        for filename in glob.glob(os.path.join('app', 'data', batch_specs["batch_directory_name"], '*.json')):
            paragraphs_in_json = []
            # extract filename from filepath and append to list for this dictionaries json-files
            with open(filename) as f:
                json_content = json.load(f)

            for paragraph_name, paragraph_specs in json_content["text_to_annotate"].items():
                # loop through all paragraphs within the json file
                paragraphs_in_json.append(
                    [paragraph_name, paragraph_specs["nr_of_words"]])

            json_files[os.path.basename(filename)] = paragraphs_in_json

        paragraphs[batch_key] = json_files



    # loop trough all html-files which are in 'mturk_hit_templates' directory
    html_templates_dir_name = os.path.join(
        'app', 'templates', 'mturk_hit_templates', '*.html')
    html_templates = []
    for html_filename in glob.glob(html_templates_dir_name):
        # extract filename from filepath and append to list for this dictionaries txt-files
        html_templates.append(os.path.basename(html_filename))


    # check if user is logged in to AWS
    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        # get all qualifications
        qualifications = getAllQualifications(client_mturk_environment)
        # for each qualification, get number of workers associated with it
        index = 0
        for qual in qualifications:
            number_of_associated_workers, associated_workers = getAllWorkersAssociatedWithQualifications(
                client_mturk_environment, qual['QualificationTypeId'])
            # update the qualifications-list to include the number of associated workers with each qualification
            qualifications[index]['number_of_associated_workers'] = number_of_associated_workers

            index += 1

        return render_template('admin_area/create_hit.html', environment=client_mturk_environment, batches=config.batches, paragraphs=paragraphs, hit_specifications=hit_specifications, hits=getAllHITs(client_mturk_environment), qualifications=qualifications, html_templates=html_templates)


@admin_area_bp.route('/mturk_requester_actions/create_mturk_hit', methods=['POST'])
def create_mturk_hit():

    client_mturk_environment = request.form['environment']
    # check if user is logged in to AWS
    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        title = request.form['title']
        batchSpecification = request.form['batchSpecification']
        htmlTemplateFilename = request.form['htmlTemplateFilename']
        description = request.form['description']
        timeout = request.form['timeout']
        keywords = request.form['keywords']
        maxAssignments = request.form['maxAssignments']
        duration = request.form['duration']
        paragraphs = ";".join(request.form.getlist('paragraphs'))
        estimatedCompletionTime = request.form['estimatedCompletionTime']
        reward = request.form['rewardPerAssignment']
        masters = request.form['masters']
        location = request.form['location']
        approved = request.form['approved']
        percentAssignmentsApproved = request.form['percentAssignmentsApproved']
        excluded = request.form.getlist('excluded')
        included = request.form.getlist('included')
        questionType = request.form['questionType']
        createNewQualificationType = request.form['createNewQualificationType']

        session['hit_specifications'] = {
            'environment': client_mturk_environment,
            'title': title,
            'batchSpecification': batchSpecification,
            'htmlTemplateFilename': htmlTemplateFilename,
            'description': description,
            'timeout': timeout,
            'keywords': keywords,
            'maxAssignments': maxAssignments,
            'duration': duration,
            'estimatedCompletionTime': estimatedCompletionTime,
            'reward': reward,
            'masters': masters,
            'location': location,
            'approved': approved,
            'percentAssignmentsApproved': percentAssignmentsApproved,
            'excluded': excluded,
            'included': included,
            'questionType': questionType,
            'createNewQualificationType': createNewQualificationType
        }

        if createNewQualificationType == 'yes':
            # create a new custom Qualification which includes the name of this HIT. After HIT has been completed, admin has to associate this qualification with all the workers who participated in this HIT. In future HITs the requester can then choose to exclude all workers who participated in this hit.

            # get all qualifications
            quals = getAllQualifications(client_mturk_environment)
            qual_names = [qual['Name'].lower() for qual in quals]

            # if qualification does not exist yet, create qualifications for all workers who will participate in this HIT
            if (title.lower() not in qual_names):
                # create new qualification if no qualification has been created yet for this Title
                create_response = client.create_qualification_type(
                    Name=title,
                    Description="Completed the HIT named: '"+title+"'",
                    QualificationTypeStatus='Active')


        # Specify qualifications -- modify this directly to implement Qualifications not available through the form
        # check out the following link to see more predefined qualifications: https://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html
        qualificationRequirements = []

        if client_mturk_environment == 'sandbox':
            masters_id = '2ARFPLSP75KLA8M8DH1HTEQVJT3SY6'
        else:
            masters_id = '2F1QJWKUDD8XADTFD2Q0G6UTO95ALH'

        # if requested, add masters qualification: Masters are Workers who have demonstrated superior performance while completing thousands of HITs across the Mechanical Turk marketplace. Masters maintain this high level of performance to keep this distinction. Set the comparator parameter to "Exists" to require that Workers have this Qualification.
        if masters == 'yes':
            print("APPENDING QualificationTypeId MASTERS tho new HIT")
            qualificationRequirements.append({
                'QualificationTypeId': masters_id,
                'Comparator': 'Exists',
                'ActionsGuarded': 'DiscoverPreviewAndAccept'
            })
        elif masters == 'no':
            qualificationRequirements.append({
                'QualificationTypeId': masters_id,
                'Comparator': 'DoesNotExist',
                'ActionsGuarded': 'DiscoverPreviewAndAccept'
            })

        # add qualification to ensure that worker's location is US
        if location == 'yes':
            print("APPENDING QualificationTypeId LOCATION tho new HIT")
            qualificationRequirements.append({
                'QualificationTypeId': '00000000000000000071',
                'Comparator': 'EqualTo',
                'LocaleValues': [
                    {
                        'Country': 'US'
                    }
                ],
                'ActionsGuarded': 'DiscoverPreviewAndAccept'
            })

        # add qualification: Specifies the total number of HITs submitted by a Worker that have been approved. The value is an integer greater than or equal to 0.
        if approved != '':
            print("APPENDING QualificationTypeId APPROVED tho new HIT")
            approved = int(approved)
            qualificationRequirements.append({
                'QualificationTypeId': '00000000000000000040',
                'Comparator': 'GreaterThanOrEqualTo',
                'IntegerValues': [approved],
                'ActionsGuarded': 'DiscoverPreviewAndAccept'
            })

        # add qualification: The percentage of assignments the Worker has submitted that were subsequently approved by the Requester, over all assignments the Worker has submitted. The value is an integer between 0 and 100. Note that a Worker's approval rate is statistically meaningless for small numbers of assignments, since a single rejection can reduce the approval rate by many percentage points. So to ensure that a new Worker's approval rate is unaffected by these statistically meaningless changes, if a Worker has submitted less than 100 assignments, the Worker's approval rate in the system is 100%. To prevent Workers who have less than 100 approved assignments from working on your HIT, set the Worker_​NumberHITsApproved qualification type ID to a value greater than 100.
        if percentAssignmentsApproved != '':
            print("APPENDING QualificationTypeId % APPROVED tho new HIT")
            percentAssignmentsApproved = int(percentAssignmentsApproved)
            qualificationRequirements.append({
                'QualificationTypeId': '000000000000000000L0',
                'Comparator': 'GreaterThanOrEqualTo',
                'IntegerValues': [percentAssignmentsApproved],
                'ActionsGuarded': 'DiscoverPreviewAndAccept'
            })

        # exclude all workers who participated in one of the chosen HITs to exclude
        if excluded:
            print("")
            print("Workers who have one of the following qualifications are excluded from participating (DiscoverPreviewAndAccept):")
            for qual in excluded:
                print("- ", qual)
                qualificationRequirements.append({
                    'QualificationTypeId': qual,
                    'Comparator': 'DoesNotExist',
                    'ActionsGuarded': 'DiscoverPreviewAndAccept'
                })

        # make sure that only those workers who participated in one of the choses HITs can participate in the new HIT
        if included:
            print("")
            print("Only workers who have one of the following qualifications are able to participate (DiscoverPreviewAndAccept):")
            for qual in included:
                print("- ", qual)
                qualificationRequirements.append({
                    'QualificationTypeId': qual,
                    'Comparator': 'Exists',
                    'ActionsGuarded': 'DiscoverPreviewAndAccept'
                })

        # MTurk accepts an XML document containing the HTML that will be displayed to Workers. Here the HTML is loaded and inserted into the XML Document.
        if questionType == 'externalURL':
            # the content of the hit is based on an external URL

            # check if configuration for this batch already exists in the config file
            if batchSpecification not in config.batches:
                raise SystemExit("""
                The batchSpecification is not yet configured in hit_congig.py.
                This is crucial since without a batch configuration in the config file, workers will not be able to see the correct content for this batch.
                Please configure it in the config and try again.""")

            batch_config_hit_type = config.batches[batchSpecification]['hit_type']

            hit_question = '''<?xml version="1.0" encoding="UTF-8"?><ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">
            <ExternalURL>https://''' + config.APP_NAME + '''.herokuapp.com/textannotation/''' + batch_config_hit_type + '''/''' + batchSpecification + '''/''' + paragraphs + '''</ExternalURL>
            <FrameHeight>0</FrameHeight>
            </ExternalQuestion>'''

            requesterAnnotation = "{'created_by':" + config.APP_NAME + \
                ",'batch_specification':" + batchSpecification + "}"

            description += " This task takes approximately " + \
                str(estimatedCompletionTime) + " minutes to complete."

        else:
            # the content of the hit is based on a locally available html template
            hit_question = htmlTemplateFilename
            html_template_filename = os.path.join(
                'app', 'templates', 'mturk_hit_templates', htmlTemplateFilename)


            html_layout = open(file=html_template_filename, mode='r').read()

            QUESTION_XML = """<HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
                    <HTMLContent><![CDATA[{}]]></HTMLContent>
                    <FrameHeight>0</FrameHeight>
                    </HTMLQuestion>"""
            hit_question = QUESTION_XML.format(html_layout)

            requesterAnnotation = "{'created_by':" + config.APP_NAME + "}"


        try:

            response = client.create_hit(
                MaxAssignments=int(maxAssignments),
                # How long the task will be available on the MTurk website (1 hour)
                LifetimeInSeconds=int(duration)*24*60*60,
                # How long Workers have to complete each item (10 minutes)
                AssignmentDurationInSeconds=int(timeout) * 60,
                # The reward you will offer Workers for each response
                Reward=str(reward),
                Title=title,
                Description=description,
                Keywords=keywords,
                Question=hit_question,
                RequesterAnnotation=requesterAnnotation,
                QualificationRequirements=qualificationRequirements
            )

            print("")
            print("The HIT was created with the following response:")
            print(response)
            print("")

            hit_type_id = response['HIT']['HITTypeId']

            message = "The HIT with the ID '" + response['HIT']['HITId'] + "' was created successfully in the MTurk <mark>" + client_mturk_environment + "</mark> environment! You can view the HIT <a target='_blank' rel='noopener noreferrer' href='" + getMTurkPreview(
                client_mturk_environment) + "?groupId=" + hit_type_id + "'>here</a>."
            flash(Markup(message), "success")

            return redirect(url_for('admin_area_bp.create_hit_form', client_mturk_environment=client_mturk_environment))

        except Exception as e:
            error_message = "The HIT could not be created! <br> Error message: " + \
                str(e)
            print(error_message)
            flash(Markup(error_message), "error")
            return redirect(url_for('admin_area_bp.create_hit_form', client_mturk_environment=client_mturk_environment))


@admin_area_bp.route('/mturk_requester_actions/show_blocked_workers/<client_mturk_environment>')
@login_required_AdminArea
def show_blocked_workers(client_mturk_environment):

    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:

        # get all blocked workers
        blocked_workers, number_of_blocked_workers = getAllBlockedWorkers(
            client_mturk_environment, client)

        return render_template('admin_area/blocked_workers.html', environment=client_mturk_environment, blocked_workers=blocked_workers, number_of_blocked_workers=number_of_blocked_workers)


@admin_area_bp.route('/mturk_requester_actions/block_worker', methods=['POST'])
def block_worker():

    client_mturk_environment = request.form['environment']
    # check if user is logged in to AWS
    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        worker_id = request.form['workerid']
        reason = request.form['reason']

        try:
            # block worker on mturk
            response = client.create_worker_block(
                WorkerId=worker_id,
                Reason=reason)

            print("")
            print("The worker with the id '" + worker_id +
                  "' was blocked with the following response:")
            print(response)
            print("")

            message = "The worker with the ID '<i>" + worker_id + \
                "</i>' was blocked successfully in the MTurk <mark>" + \
                client_mturk_environment + "</mark> environment!"
            flash(Markup(message), "success")

            return redirect(url_for('admin_area_bp.show_blocked_workers', client_mturk_environment=client_mturk_environment))

        except Exception as e:
            error_message = "The worker block failed! <br> Error message: " + \
                str(e)
            print(error_message)
            flash(Markup(error_message), "error")
            return redirect(url_for('admin_area_bp.show_blocked_workers', client_mturk_environment=client_mturk_environment))


@admin_area_bp.route('/mturk_requester_actions/delete_worker_block', methods=['POST'])
def delete_worker_block():

    client_mturk_environment = request.form['environment']
    # check if user is logged in to AWS
    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        worker_id = request.form['workerid']
        reason = request.form['reason']

        try:
            # delete the worker block on mturk
            response = client.delete_worker_block(
                WorkerId=worker_id,
                Reason=reason)

            print("")
            print("The block of the worker with the id '" + worker_id +
                  "' was deleted with the following response:")
            print(response)
            print("")

            message = "The block of the worker with the ID '<i>" + worker_id + \
                "</i>' was deleted successfully in the MTurk <mark>" + \
                client_mturk_environment + "</mark> environment!"
            flash(Markup(message), "success")

            return redirect(url_for('admin_area_bp.show_blocked_workers', client_mturk_environment=client_mturk_environment))

        except Exception as e:
            error_message = "The worker block failed! <br> Error message: " + \
                str(e)
            print(error_message)
            flash(Markup(error_message), "error")
            return redirect(url_for('admin_area_bp.show_blocked_workers', client_mturk_environment=client_mturk_environment))


@admin_area_bp.route('/mturk_requester_actions/show_worker_qualifications/<client_mturk_environment>')
@login_required_AdminArea
def show_worker_qualifications(client_mturk_environment):

    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:

        # get all qualifications
        quals = getAllQualifications(client_mturk_environment)
        # loop trough all qualifications and extend the qual-dicts so that there is an information included how many and which workers are associated with the respective qual
        qual_index = 0
        for qual in quals:
            number_of_associated_workers, associated_workers = getAllWorkersAssociatedWithQualifications(
                client_mturk_environment, qual['QualificationTypeId'])

            quals[qual_index]['number_of_associated_workers'] = number_of_associated_workers
            quals[qual_index]['associated_workers'] = associated_workers
            qual_index += 1

        return render_template('admin_area/show_worker_qualifications.html', environment=client_mturk_environment, quals=quals, number_of_qualifications=len(quals))


@admin_area_bp.route('/mturk_requester_actions/associate_qualification_with_worker', methods=['POST'])
def associate_qualification_with_worker():

    client_mturk_environment = request.form['environment']
    # check if user is logged in to AWS
    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        worker_ids = request.form['workerid']
        qualification_id = request.form['qualificationid']
        IntegerValue = request.form['IntegerValue']
        SendNotification = request.form['SendNotification']

        if SendNotification == 'yes':
            SendNotification_bool = True
        else:
            SendNotification_bool = False

        worker_ids_success = []
        worker_ids_failed = []
        # loop through all the given worker_ids
        for worker_id in [id.strip() for id in worker_ids.split(";") if id != ""]:

            try:

                # get qualification name
                qualification_name = client.get_qualification_type(
                    QualificationTypeId=qualification_id)["QualificationType"]["Name"]

                # associate worker with qualification
                if (IntegerValue == ''):
                    response = client.associate_qualification_with_worker(
                        QualificationTypeId=qualification_id,
                        WorkerId=worker_id,
                        SendNotification=SendNotification_bool)
                else:
                    response = client.associate_qualification_with_worker(
                        QualificationTypeId=qualification_id,
                        WorkerId=worker_id,
                        IntegerValue=IntegerValue,
                        SendNotification=SendNotification_bool)

                print("")
                print("The qualification (id=" + str(qualification_id) + " | name=" + str(qualification_name) +
                      ") was successfully associated with the worker(s) (id=" + str(worker_ids) + ") with the following response:")
                print(response)

                worker_ids_success.append(worker_id)

            except Exception as e:
                error_message = "The qualification association failed for the worker with ID=" + worker_id + "!"
                print(error_message)
                flash(Markup(error_message), "error")
                # return redirect(url_for('admin_area_bp.show_worker_qualifications', client_mturk_environment=client_mturk_environment))

        if len(worker_ids_success) > 0:
            # print success message if it worked for at least one of the given IDs
            message_success = "The qualification (id=" + str(qualification_id) + " | name=" + str(qualification_name) + ") was successfully associated with " + str(
                len(worker_ids_success)) + " worker(s) (IDs=" + " / ".join(worker_ids_success) + ") in the MTurk <mark>" + client_mturk_environment + "</mark> environment."
            flash(Markup(message_success), "success")

        return redirect(url_for('admin_area_bp.show_worker_qualifications', client_mturk_environment=client_mturk_environment))


@admin_area_bp.route('/mturk_requester_actions/disassociate_qualification_with_worker', methods=['POST'])
def disassociate_qualification_with_worker():

    client_mturk_environment = request.form['environment']
    # check if user is logged in to AWS
    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        worker_id = request.form['workerid']
        qualification_id = request.form['qualificationid']
        reason = request.form['reason']

        try:

            # get qualification name
            qualification_name = client.get_qualification_type(
                QualificationTypeId=qualification_id)["QualificationType"]["Name"]

            # disassociate worker with qualification

            response = client.disassociate_qualification_from_worker(
                WorkerId=worker_id,
                QualificationTypeId=qualification_id,
                Reason=reason)

            print("")
            print("The qualification (id=" + str(qualification_id) + " | name=" + str(qualification_name) +
                  ") was successfully DISassociated from the worker (id=" + str(worker_id) + ") with the following response:")
            print(response)

            message = "The qualification (id=" + str(qualification_id) + " | name=" + str(qualification_name) + ") was successfully DISassociated with the worker (id=" + str(
                worker_id) + ") in the MTurk <mark>" + client_mturk_environment + "</mark> environment."

            flash(Markup(message), "success")

            return redirect(url_for('admin_area_bp.show_worker_qualifications', client_mturk_environment=client_mturk_environment))

        except Exception as e:
            error_message = "The qualification DISassociation failed! <br> Error message: " + \
                str(e)
            print(error_message)
            flash(Markup(error_message), "error")
            return redirect(url_for('admin_area_bp.show_worker_qualifications', client_mturk_environment=client_mturk_environment))


@admin_area_bp.route('/mturk_requester_actions/create_qualification', methods=['POST'])
def create_qualification():

    client_mturk_environment = request.form['environment']
    # check if user is logged in to AWS
    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        qualificationName = request.form['qualificationName']
        qualificationDescription = request.form['qualificationDescription']
        keywords = request.form['keywords']
        QualificationTypeStatus = request.form['QualificationTypeStatus']

        try:

            # create new qualification
            response = client.create_qualification_type(
                Name=str(qualificationName),
                Description=str(qualificationDescription),
                Keywords=str(keywords),
                QualificationTypeStatus=str(QualificationTypeStatus))

            print("")
            print("The qualification type (name=" + str(qualificationName) + "|status=" +
                  str(QualificationTypeStatus) + ") was successfully created with the following response:")
            print(response)

            message = "The qualification (name=" + str(qualificationName) + "|status=" + str(QualificationTypeStatus) + \
                ") was successfully created in the MTurk <mark>" + \
                client_mturk_environment + "</mark> environment."

            flash(Markup(message), "success")

            return redirect(url_for('admin_area_bp.show_worker_qualifications', client_mturk_environment=client_mturk_environment))

        except Exception as e:
            error_message = "The qualification could not be created! <br> Error message: " + \
                str(e)
            print(error_message)
            flash(Markup(error_message), "error")
            return redirect(url_for('admin_area_bp.show_worker_qualifications', client_mturk_environment=client_mturk_environment))


@admin_area_bp.route('/mturk_requester_actions/delete_qualification')
def delete_qualification():

    qualification_id = request.args.get('qualification_id')
    client_mturk_environment = request.args.get('environment')

    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        try:
            # Delete the qualification
            response = client.delete_qualification_type(
                QualificationTypeId=qualification_id)
            print("The qualification with the ID '" + qualification_id +
                  "' was deleted with the following response:")
            print(response)
            message = "The qualification with the ID '<i>" + \
                qualification_id + "</i>' was deleted!"
            flash(Markup(message), "success")
        except Exception as e:
            # the qualification could not be deleted
            error_message = "The qualification with the ID '" + qualification_id + \
                "' COULD NOT be DELETED! <br> Error message: " + str(e)
            print(error_message)
            flash(Markup(error_message), "error")

    return "true"


@admin_area_bp.route('/mturk_requester_actions/additional_assignments_for_hit/<client_mturk_environment>')
@login_required_AdminArea
def additional_assignments_for_hit(client_mturk_environment):

    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:

        hits = getAllHITs(client_mturk_environment)

        return render_template('admin_area/create_additional_assignments_for_hit.html', environment=client_mturk_environment, hits=hits)


@admin_area_bp.route('/mturk_requester_actions/create_additional_assignments_for_hit', methods=['POST'])
def create_additional_assignments_for_hit():

    client_mturk_environment = request.form['environment']
    # check if user is logged in to AWS
    connection, client, account_balance = checkConnection(
        client_mturk_environment)
    if connection is False:
        return render_template('admin_area/checkconnection.html', connection=connection, environment=client_mturk_environment)
    else:
        hit_id = request.form['hit_id']
        number_of_additional_assignments = int(
            request.form['number_of_additional_assignments'])

        current_max_assignments_of_hit = client.get_hit(
            HITId=hit_id)['HIT']['MaxAssignments']

        if (current_max_assignments_of_hit < 10 and (current_max_assignments_of_hit+number_of_additional_assignments >= 10)):
            # the current maxAssignments of the HIT is less than 10 and adding the number of additional assignments would lead to more than 10 assignments. This is forbidden by MTurk.
            message = "Creating additional assignments for the HIT with the ID '<i>" + hit_id + "</i>' failed! The current maxAssignments [<b>" + str(
                current_max_assignments_of_hit) + "</b>] of the HIT is less than 10 and adding the number of additional assignments [<b>" + str(number_of_additional_assignments) + "</b>] would lead to 10 or more assignments. This is forbidden by MTurk."
            flash(Markup(message), "error")
            return redirect(url_for('admin_area_bp.additional_assignments_for_hit', client_mturk_environment=client_mturk_environment))
        else:
            try:
                # block worker on mturk
                response = client.create_additional_assignments_for_hit(
                    HITId=hit_id,
                    NumberOfAdditionalAssignments=number_of_additional_assignments)


                print("")
                print(str(number_of_additional_assignments) +
                      " new assignments were created for the HIT with the ID '" + hit_id + "' with the following response:")
                print(response)
                print("")

                message = "<mark>" + str(number_of_additional_assignments) + "</mark> new assignments were created for the HIT with the ID '<i>" + \
                    hit_id + "</i>' in the MTurk <mark>" + \
                    client_mturk_environment + "</mark> environment!"
                flash(Markup(message), "success")

                return redirect(url_for('admin_area_bp.additional_assignments_for_hit', client_mturk_environment=client_mturk_environment))

            except Exception as e:
                # the qualification could not be deleted
                error_message = "Creating additional assignments for the HIT with the ID '<i>" + \
                    hit_id + "</i>' failed! <br> Error message: " + str(e)
                print(error_message)
                flash(Markup(error_message), "error")
                return redirect(url_for('admin_area_bp.additional_assignments_for_hit', client_mturk_environment=client_mturk_environment))
