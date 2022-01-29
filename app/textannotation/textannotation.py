import glob
import json
import os
import sys

import config
from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from nltk.tokenize import word_tokenize

DEV_ENVIROMENT_BOOLEAN = True
# This allows us to specify whether we are pushing to the sandbox or live site.
if DEV_ENVIROMENT_BOOLEAN:
    AMAZON_HOST = "https://workersandbox.mturk.com/mturk/externalSubmit"
else:
    AMAZON_HOST = "https://www.mturk.com/mturk/externalSubmit"


textannotation_bp = Blueprint('textannotation_bp', __name__)


def importName(modulename, name):
    """ Import a named object from a module in the context of this function.
    This function can be used to import modules whose name is determined at runtime, such as e.g. the annotations for determining the relations of a specific batch.
    """
    try:
        module = __import__(modulename, globals(), locals(), [name])
    except ImportError:
        return None
    return vars(module)[name]


@textannotation_bp.route('/arguments/<batch>/<paragraphs>')
def arguments(batch=None, paragraphs=None):

    # load variables for this specific batch from config file
    batch_config_variables = config.batches[batch]
    # load preferred annotation types from config file
    annotation_types = config.annotation_types[batch_config_variables['annotation_types']]
    # load forbidden tokens from config file
    forbidden_tokens = config.forbidden_tokens[batch_config_variables['forbidden_tokens']]
    # load batch_directory_name for paragraphs from config file
    batch_directory_name = batch_config_variables['batch_directory_name']
    # load textToAnnotate_filename for paragraphs from config file
    textToAnnotate_filename = batch_config_variables['textToAnnotate_filename']

    worker_id = request.args.get("workerId")
    if worker_id is None:
        worker_id = 'test worker id NEW2'

    assignment_id = request.args.get("assignmentId")
    if assignment_id is None:
        assignment_id = 'test assignment id'

    hit_id = request.args.get("hitId")
    if hit_id is None:
        hit_id = 'test hit id'

    # load the Amazon Mechanical Turk URL to which the form must post the result data back to
    turkSubmitTo = request.args.get("turkSubmitTo")
    if turkSubmitTo is None:
        turkSubmitTo = 'https://workersandbox.mturk.com/mturk/externalSubmit'
    else:
        turkSubmitTo += '/mturk/externalSubmit'

    print("WORKING:" + " worker_id='" + worker_id + "' assignment_id='" +
          assignment_id + "' hit_id='" + hit_id + "' turkSubmitTo='" + turkSubmitTo + "'")

    worker_assignment_data = {
        'worker_id': worker_id,
        'assignment_id': assignment_id,
        'hit_id': hit_id,
        'turkSubmitTo': turkSubmitTo,
        'task_type': 'arguments',
        'batch': batch,
        'batch_config_variables': batch_config_variables,
        'paragraphs': paragraphs
    }

    if request.args.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        # Our worker hasn't accepted the HIT (task) yet
        preview_mode = "true"
    else:
        # Our worker accepted the task
        preview_mode = "false"

    text_to_annotate = {}
    paragraph_counter = 0

    filename = os.path.join(
        'app', 'data', batch_directory_name, textToAnnotate_filename)

    with open(filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

    for p_name in paragraphs.split(';'):
        # loop trough all paragraphs which where specified in create batch url
        text_to_annotate[paragraph_counter] = all_paragraphs[p_name]["tokens"]
        paragraph_counter += 1

    return render_template('textannotation/arguments_instructions.html', worker_assignment_data=worker_assignment_data, turkSubmitTo=turkSubmitTo, preview_mode=preview_mode, text_to_annotate=text_to_annotate, forbidden_tokens=forbidden_tokens, annotation_types=annotation_types)


@textannotation_bp.route('/arguments_filterStep1/<batch>/<paragraphs>')
def arguments_filterStep1(batch=None, paragraphs=None):

    # load variables for this specific batch from config file
    batch_config_variables = config.batches[batch]
    # load preferred annotation types from config file
    annotation_types = config.annotation_types[batch_config_variables['annotation_types']]
    # load forbidden tokens from config file
    forbidden_tokens = config.forbidden_tokens[batch_config_variables['forbidden_tokens']]
    # load batch_directory_name for paragraphs from config file
    batch_directory_name = batch_config_variables['batch_directory_name']
    # load textToAnnotate_filename for paragraphs from config file
    textToAnnotate_filename = batch_config_variables['textToAnnotate_filename']

    worker_id = request.args.get("workerId")
    if worker_id is None:
        worker_id = 'test worker id NEW2'

    assignment_id = request.args.get("assignmentId")
    if assignment_id is None:
        assignment_id = 'test assignment id'

    hit_id = request.args.get("hitId")
    if hit_id is None:
        hit_id = 'test hit id'

    # load the Amazon Mechanical Turk URL to which the form must post the result data back to
    turkSubmitTo = request.args.get("turkSubmitTo")
    if turkSubmitTo is None:
        turkSubmitTo = 'https://workersandbox.mturk.com/mturk/externalSubmit'
    else:
        turkSubmitTo += '/mturk/externalSubmit'

    print("WORKING:" + " worker_id='" + worker_id + "' assignment_id='" +
          assignment_id + "' hit_id='" + hit_id + "' turkSubmitTo='" + turkSubmitTo + "'")

    worker_assignment_data = {
        'worker_id': worker_id,
        'assignment_id': assignment_id,
        'hit_id': hit_id,
        'turkSubmitTo': turkSubmitTo,
        'task_type': 'arguments',
        'batch': batch,
        'batch_config_variables': batch_config_variables,
        'paragraphs': paragraphs
    }

    if request.args.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        # Our worker hasn't accepted the HIT (task) yet
        preview_mode = "true"
    else:
        # Our worker accepted the task
        preview_mode = "false"

    text_to_annotate = {}
    paragraph_counter = 0

    filename = os.path.join(
        'app', 'data', batch_directory_name, textToAnnotate_filename)

    with open(filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

    for p_name in paragraphs.split(';'):
        # loop trough all paragraphs which where specified in create batch url
        text_to_annotate[paragraph_counter] = all_paragraphs[p_name]["tokens"]
        paragraph_counter += 1

    with open(os.path.join('app', 'data', "filterStep1.json")) as f:
        filterStep1 = json.load(f)["filterStep1_argument_component"]


    return render_template('textannotation/arguments_instructions_filterStep1.html', worker_assignment_data=worker_assignment_data, turkSubmitTo=turkSubmitTo, preview_mode=preview_mode, text_to_annotate=text_to_annotate, forbidden_tokens=forbidden_tokens, annotation_types=annotation_types, filter_instructions_step1=filterStep1["general_instructions"], worker_IDs_who_passed_step1=filterStep1["worker_IDs_who_passed"], filter_questions_step1=filterStep1["questions"])


@textannotation_bp.route('/arguments_filterStep2/<batch>/<paragraphs>')
def arguments_filterStep2(batch=None, paragraphs=None):

    # load variables for this specific batch from config file
    batch_config_variables = config.batches[batch]
    # load preferred annotation types from config file
    annotation_types = config.annotation_types[batch_config_variables['annotation_types']]
    # load forbidden tokens from config file
    forbidden_tokens = config.forbidden_tokens[batch_config_variables['forbidden_tokens']]
    # load batch_directory_name for paragraphs from config file
    batch_directory_name = batch_config_variables['batch_directory_name']
    # load textToAnnotate_filename for paragraphs from config file
    textToAnnotate_filename = batch_config_variables['textToAnnotate_filename']
    # load filter_attempts_before_revealing_solution from config file
    filter_attempts_before_revealing_solution = batch_config_variables[
        'filter_attempts_before_revealing_solution']

    worker_id = request.args.get("workerId")
    if worker_id is None:
        worker_id = 'test worker id NEW2'

    assignment_id = request.args.get("assignmentId")
    if assignment_id is None:
        assignment_id = 'test assignment id'

    hit_id = request.args.get("hitId")
    if hit_id is None:
        hit_id = 'test hit id'

    # load the Amazon Mechanical Turk URL to which the form must post the result data back to
    turkSubmitTo = request.args.get("turkSubmitTo")
    if turkSubmitTo is None:
        turkSubmitTo = 'https://workersandbox.mturk.com/mturk/externalSubmit'
    else:
        turkSubmitTo += '/mturk/externalSubmit'

    print("WORKING:" + " worker_id='" + worker_id + "' assignment_id='" +
          assignment_id + "' hit_id='" + hit_id + "' turkSubmitTo='" + turkSubmitTo + "'")

    worker_assignment_data = {
        'worker_id': worker_id,
        'assignment_id': assignment_id,
        'hit_id': hit_id,
        'turkSubmitTo': turkSubmitTo,
        'task_type': 'arguments',
        'batch': batch,
        'batch_config_variables': batch_config_variables,
        'paragraphs': paragraphs
    }

    if request.args.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        # Our worker hasn't accepted the HIT (task) yet
        preview_mode = "true"
    else:
        # Our worker accepted the task
        preview_mode = "false"

    text_to_annotate = {}
    paragraph_counter = 0

    filename = os.path.join(
        'app', 'data', batch_directory_name, textToAnnotate_filename)

    with open(filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

    for p_name in paragraphs.split(';'):
        # loop trough all paragraphs which where specified in create batch url
        text_to_annotate[paragraph_counter] = all_paragraphs[p_name]["tokens"]
        paragraph_counter += 1

    with open(os.path.join('app', 'data', "filterStep2.json")) as f:
        filterStep2 = json.load(f)["filterStep2_argument_component"]

    return render_template('textannotation/arguments_instructions_filterStep2.html', worker_assignment_data=worker_assignment_data, turkSubmitTo=turkSubmitTo, preview_mode=preview_mode, text_to_annotate=text_to_annotate, forbidden_tokens=forbidden_tokens, annotation_types=annotation_types, worker_IDs_who_passed_step2=filterStep2["worker_IDs_who_passed"],  filter_questions_step2=filterStep2["questions"], filter_attempts_before_revealing_solution=filter_attempts_before_revealing_solution)


@textannotation_bp.route('/relations/<batch>/<paragraphs>')
def relations(batch=None, paragraphs=None):

    # load variables for this specific batch from config file
    batch_config_variables = config.batches[batch]
    # load preferred relation types from config file
    relation_types = config.relation_types[batch_config_variables['relation_types']]
    # load preferred annotation types from config file
    annotation_types = config.annotation_types[batch_config_variables['annotation_types']]
    # load batch_directory_name for paragraphs from config file
    batch_directory_name = batch_config_variables['batch_directory_name']
    # load textToAnnotate_filename for paragraphs from config file
    textToAnnotate_filename = batch_config_variables['textToAnnotate_filename']
    # load textToAnnotate_filename for paragraphs from config file
    annotations_on_load_listname = batch_config_variables['annotations_on_load']

    worker_id = request.args.get("workerId")
    if worker_id is None:
        worker_id = 'test worker id NEW2'

    assignment_id = request.args.get("assignmentId")
    if assignment_id is None:
        assignment_id = 'test assignment id'

    #amazon_host = request.args.get('amazon_host')
    amazon_host = AMAZON_HOST
    if amazon_host is None:
        amazon_host = 'test amazon amazon_host'

    hit_id = request.args.get("hitId")
    if hit_id is None:
        hit_id = 'test hit id'

    # load the Amazon Mechanical Turk URL to which the form must post the result data back to
    turkSubmitTo = request.args.get("turkSubmitTo")
    if turkSubmitTo is None:
        turkSubmitTo = 'https://workersandbox.mturk.com/mturk/externalSubmit'
    else:
        turkSubmitTo += '/mturk/externalSubmit'

    print("WORKING:" + " worker_id='" + worker_id + "' assignment_id='" +
          assignment_id + "' hit_id='" + hit_id + "' turkSubmitTo='" + turkSubmitTo + "'")

    worker_assignment_data = {
        'worker_id': worker_id,
        'assignment_id': assignment_id,
        'hit_id': hit_id,
        'turkSubmitTo': turkSubmitTo,
        'task_type': 'relations',
        'batch': batch,
        'batch_config_variables': batch_config_variables,
        'paragraphs': paragraphs
    }

    if request.args.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        # Our worker hasn't accepted the HIT (task) yet
        preview_mode = "true"
    else:
        # Our worker accepted the task
        preview_mode = "false"

    text_to_annotate = {}
    paragraph_counter = 0

    filename = os.path.join(
        'app', 'data', batch_directory_name, textToAnnotate_filename)

    with open(filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

    for p_name in paragraphs.split(';'):
        # loop trough all paragraphs which where specified in create batch url
        text_to_annotate[paragraph_counter] = all_paragraphs[p_name]["tokens"]
        paragraph_counter += 1

    # import annotations from dynamic pathname as specified for this specific batch in config file
    annotations_on_load = importName(
        "app.data.annotations_on_load_for_relation_HITs", annotations_on_load_listname)

    annotations_on_load_paragraphs_counter = 0
    for p_annotations in annotations_on_load:
        p_a_counter = 0
        for p_a in p_annotations:
            for a_key, a_value in text_to_annotate[annotations_on_load_paragraphs_counter].items():
                # only check if the start token has not been found yet
                if p_a[0] == -1 and p_a[6] >= a_value["start"] and p_a[6] <= a_value["end"]:
                    # the start index of the annotation_on_load lies whithin the currently looked at token. The key of this token is the start_id for we were looking for.
                    p_a[0] = int(a_key)

                # only check if the end token is found when the start token has already been found
                if p_a[0] != -1 and p_a[7] >= a_value["start"] and p_a[7] <= a_value["end"]:
                    # the end index of the annotation_on_load lies whithin the currently looked at token. The key of this token is the end_id for we were looking for.
                    p_a[1] = int(a_key)

                    break

            p_a_counter += 1
        annotations_on_load_paragraphs_counter += 1

    nr_of_annotations = sum(len(p_annotations)
                            for p_annotations in annotations_on_load)
    nr_of_incomplete_annotations = sum(len(
        [a for a in p_annotations if a[0] == -1 or a[1] == -1]) for p_annotations in annotations_on_load)


    return render_template('relationannotation/relationAnnotation_instructions.html', worker_assignment_data=worker_assignment_data, turkSubmitTo=turkSubmitTo, preview_mode=preview_mode, text_to_annotate=text_to_annotate, annotations=annotations_on_load, annotation_types=annotation_types, relation_types=relation_types)


@textannotation_bp.route('/relations_filterStep1/<batch>/<paragraphs>')
def relations_filterStep1(batch=None, paragraphs=None):

    # load variables for this specific batch from config file
    batch_config_variables = config.batches[batch]
    # load preferred relation types from config file
    relation_types = config.relation_types[batch_config_variables['relation_types']]
    # load preferred annotation types from config file
    annotation_types = config.annotation_types[batch_config_variables['annotation_types']]
    # load batch_directory_name for paragraphs from config file
    batch_directory_name = batch_config_variables['batch_directory_name']
    # load textToAnnotate_filename for paragraphs from config file
    textToAnnotate_filename = batch_config_variables['textToAnnotate_filename']
    # load textToAnnotate_filename for paragraphs from config file
    annotations_on_load_listname = batch_config_variables['annotations_on_load']

    worker_id = request.args.get("workerId")
    if worker_id is None:
        worker_id = 'test worker id NEW2'

    assignment_id = request.args.get("assignmentId")
    if assignment_id is None:
        assignment_id = 'test assignment id'

    #amazon_host = request.args.get('amazon_host')
    amazon_host = AMAZON_HOST
    if amazon_host is None:
        amazon_host = 'test amazon amazon_host'

    hit_id = request.args.get("hitId")
    if hit_id is None:
        hit_id = 'test hit id'

    # load the Amazon Mechanical Turk URL to which the form must post the result data back to
    turkSubmitTo = request.args.get("turkSubmitTo")
    if turkSubmitTo is None:
        turkSubmitTo = 'https://workersandbox.mturk.com/mturk/externalSubmit'
    else:
        turkSubmitTo += '/mturk/externalSubmit'

    print("WORKING:" + " worker_id='" + worker_id + "' assignment_id='" +
          assignment_id + "' hit_id='" + hit_id + "' turkSubmitTo='" + turkSubmitTo + "'")

    worker_assignment_data = {
        'worker_id': worker_id,
        'assignment_id': assignment_id,
        'hit_id': hit_id,
        'turkSubmitTo': turkSubmitTo,
        'task_type': 'relations',
        'batch': batch,
        'batch_config_variables': batch_config_variables,
        'paragraphs': paragraphs
    }

    if request.args.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        # Our worker hasn't accepted the HIT (task) yet
        preview_mode = "true"
    else:
        # Our worker accepted the task
        preview_mode = "false"

    text_to_annotate = {}
    paragraph_counter = 0

    filename = os.path.join(
        'app', 'data', batch_directory_name, textToAnnotate_filename)

    with open(filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

    for p_name in paragraphs.split(';'):
        # loop trough all paragraphs which where specified in create batch url
        text_to_annotate[paragraph_counter] = all_paragraphs[p_name]["tokens"]
        paragraph_counter += 1

    # import annotations from dynamic pathname as specified for this specific batch in config file
    annotations_on_load = importName(
        "app.data.annotations_on_load_for_relation_HITs", annotations_on_load_listname)

    annotations_on_load_paragraphs_counter = 0
    for p_annotations in annotations_on_load:
        p_a_counter = 0
        for p_a in p_annotations:
            for a_key, a_value in text_to_annotate[annotations_on_load_paragraphs_counter].items():
                # only check if the start token has not been found yet
                if p_a[0] == -1 and p_a[6] >= a_value["start"] and p_a[6] <= a_value["end"]:
                    # the start index of the annotation_on_load lies whithin the currently looked at token. The key of this token is the start_id for we were looking for.
                    p_a[0] = int(a_key)

                # only check if the end token is found when the start token has already been found
                if p_a[0] != -1 and p_a[7] >= a_value["start"] and p_a[7] <= a_value["end"]:
                    # the end index of the annotation_on_load lies whithin the currently looked at token. The key of this token is the end_id for we were looking for.
                    p_a[1] = int(a_key)

                    break

            p_a_counter += 1
        annotations_on_load_paragraphs_counter += 1

    nr_of_annotations = sum(len(p_annotations)
                            for p_annotations in annotations_on_load)
    nr_of_incomplete_annotations = sum(len(
        [a for a in p_annotations if a[0] == -1 or a[1] == -1]) for p_annotations in annotations_on_load)


    with open(os.path.join('app', 'data', "filterStep1.json")) as f:
        filterStep1 = json.load(f)["filterStep1_argument_relation"]

    return render_template('relationannotation/relationAnnotation_instructions_filterStep1.html', worker_assignment_data=worker_assignment_data, turkSubmitTo=turkSubmitTo, preview_mode=preview_mode, text_to_annotate=text_to_annotate, annotations=annotations_on_load, annotation_types=annotation_types, relation_types=relation_types, filter_instructions_step1=filterStep1["general_instructions"], worker_IDs_who_passed_step1=filterStep1["worker_IDs_who_passed"], filter_questions_step1=filterStep1["questions"])


@textannotation_bp.route('/relations_filterStep2/<batch>/<paragraphs>')
def relations_filterStep2(batch=None, paragraphs=None):

    # load variables for this specific batch from config file
    batch_config_variables = config.batches[batch]
    # load preferred relation types from config file
    relation_types = config.relation_types[batch_config_variables['relation_types']]
    # load preferred annotation types from config file
    annotation_types = config.annotation_types[batch_config_variables['annotation_types']]
    # load batch_directory_name for paragraphs from config file
    batch_directory_name = batch_config_variables['batch_directory_name']
    # load textToAnnotate_filename for paragraphs from config file
    textToAnnotate_filename = batch_config_variables['textToAnnotate_filename']
    # load textToAnnotate_filename for paragraphs from config file
    annotations_on_load_listname = batch_config_variables['annotations_on_load']
    # load filter_attempts_before_revealing_solution from config file
    filter_attempts_before_revealing_solution = batch_config_variables[
        'filter_attempts_before_revealing_solution']

    worker_id = request.args.get("workerId")
    if worker_id is None:
        worker_id = 'test worker id NEW2'

    assignment_id = request.args.get("assignmentId")
    if assignment_id is None:
        assignment_id = 'test assignment id'

    #amazon_host = request.args.get('amazon_host')
    amazon_host = AMAZON_HOST
    if amazon_host is None:
        amazon_host = 'test amazon amazon_host'

    hit_id = request.args.get("hitId")
    if hit_id is None:
        hit_id = 'test hit id'

    # load the Amazon Mechanical Turk URL to which the form must post the result data back to
    turkSubmitTo = request.args.get("turkSubmitTo")
    if turkSubmitTo is None:
        turkSubmitTo = 'https://workersandbox.mturk.com/mturk/externalSubmit'
    else:
        turkSubmitTo += '/mturk/externalSubmit'

    print("WORKING:" + " worker_id='" + worker_id + "' assignment_id='" +
          assignment_id + "' hit_id='" + hit_id + "' turkSubmitTo='" + turkSubmitTo + "'")

    worker_assignment_data = {
        'worker_id': worker_id,
        'assignment_id': assignment_id,
        'hit_id': hit_id,
        'turkSubmitTo': turkSubmitTo,
        'task_type': 'relations',
        'batch': batch,
        'batch_config_variables': batch_config_variables,
        'paragraphs': paragraphs
    }

    if request.args.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        # Our worker hasn't accepted the HIT (task) yet
        preview_mode = "true"
    else:
        # Our worker accepted the task
        preview_mode = "false"

    text_to_annotate = {}
    paragraph_counter = 0

    filename = os.path.join(
        'app', 'data', batch_directory_name, textToAnnotate_filename)

    with open(filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

    for p_name in paragraphs.split(';'):
        # loop trough all paragraphs which where specified in create batch url
        text_to_annotate[paragraph_counter] = all_paragraphs[p_name]["tokens"]
        paragraph_counter += 1

    # import annotations from dynamic pathname as specified for this specific batch in config file
    annotations_on_load = importName(
        "app.data.annotations_on_load_for_relation_HITs", annotations_on_load_listname)

    annotations_on_load_paragraphs_counter = 0
    for p_annotations in annotations_on_load:
        p_a_counter = 0
        for p_a in p_annotations:
            for a_key, a_value in text_to_annotate[annotations_on_load_paragraphs_counter].items():
                # only check if the start token has not been found yet
                if p_a[0] == -1 and p_a[6] >= a_value["start"] and p_a[6] <= a_value["end"]:
                    # the start index of the annotation_on_load lies whithin the currently looked at token. The key of this token is the start_id for we were looking for.
                    p_a[0] = int(a_key)

                # only check if the end token is found when the start token has already been found
                if p_a[0] != -1 and p_a[7] >= a_value["start"] and p_a[7] <= a_value["end"]:
                    # the end index of the annotation_on_load lies whithin the currently looked at token. The key of this token is the end_id for we were looking for.
                    p_a[1] = int(a_key)

                    break

            p_a_counter += 1
        annotations_on_load_paragraphs_counter += 1

    nr_of_annotations = sum(len(p_annotations)
                            for p_annotations in annotations_on_load)
    nr_of_incomplete_annotations = sum(len(
        [a for a in p_annotations if a[0] == -1 or a[1] == -1]) for p_annotations in annotations_on_load)


    with open(os.path.join('app', 'data', "filterStep2.json")) as f:
        filterStep2 = json.load(f)["filterStep2_argument_relation"]

    return render_template('relationannotation/relationAnnotation_instructions_filterStep2.html', worker_assignment_data=worker_assignment_data, turkSubmitTo=turkSubmitTo, preview_mode=preview_mode, text_to_annotate=text_to_annotate, annotations=annotations_on_load, annotation_types=annotation_types, relation_types=relation_types, worker_IDs_who_passed_step2=filterStep2["worker_IDs_who_passed"],  filter_questions_step2=filterStep2["questions"], filter_attempts_before_revealing_solution=filter_attempts_before_revealing_solution)


@textannotation_bp.route('/arguments_final/<batch>/<paragraphs>')
def arguments_final(batch=None, paragraphs=None):

    # load variables for this specific batch from config file
    batch_config_variables = config.batches[batch]
    # load preferred annotation types from config file
    annotation_types = config.annotation_types[batch_config_variables['annotation_types']]
    # load forbidden tokens from config file
    forbidden_tokens = config.forbidden_tokens[batch_config_variables['forbidden_tokens']]
    # load batch_directory_name for paragraphs from config file
    batch_directory_name = batch_config_variables['batch_directory_name']
    # load textToAnnotate_filename for paragraphs from config file
    textToAnnotate_filename = batch_config_variables['textToAnnotate_filename']
    # load filter_attempts_before_revealing_solution from config file
    filter_attempts_before_revealing_solution = batch_config_variables[
        'filter_attempts_before_revealing_solution']
    # load ability_filter_threshold from config file
    ability_filter_threshold = batch_config_variables['ability_filter_threshold']

    worker_id = request.args.get("workerId")
    if worker_id is None:
        worker_id = 'test worker id NEW2'

    assignment_id = request.args.get("assignmentId")
    if assignment_id is None:
        assignment_id = 'test assignment id'

    hit_id = request.args.get("hitId")
    if hit_id is None:
        hit_id = 'test hit id'

    # load the Amazon Mechanical Turk URL to which the form must post the result data back to
    turkSubmitTo = request.args.get("turkSubmitTo")
    if turkSubmitTo is None:
        turkSubmitTo = 'https://workersandbox.mturk.com/mturk/externalSubmit'
    else:
        turkSubmitTo += '/mturk/externalSubmit'

    print("WORKING:" + " worker_id='" + worker_id + "' assignment_id='" +
          assignment_id + "' hit_id='" + hit_id + "' turkSubmitTo='" + turkSubmitTo + "'")

    worker_assignment_data = {
        'worker_id': worker_id,
        'assignment_id': assignment_id,
        'hit_id': hit_id,
        'turkSubmitTo': turkSubmitTo,
        'task_type': 'arguments',
        'batch': batch,
        'batch_config_variables': batch_config_variables,
        'paragraphs': paragraphs
    }

    if request.args.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        # Our worker hasn't accepted the HIT (task) yet
        preview_mode = "true"
    else:
        # Our worker accepted the task
        preview_mode = "false"

    text_to_annotate = {}
    paragraph_counter = 0

    filename = os.path.join(
        'app', 'data', batch_directory_name, textToAnnotate_filename)

    with open(filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

    for p_name in paragraphs.split(';'):
        # loop trough all paragraphs which where specified in create batch url
        text_to_annotate[paragraph_counter] = all_paragraphs[p_name]["tokens"]
        paragraph_counter += 1

    with open(os.path.join('app', 'data', "filterStep2.json")) as f:
        filterStep2 = json.load(f)["filterStep2_argument_component"]

    return render_template('textannotation/arguments_instructions_final.html', worker_assignment_data=worker_assignment_data, turkSubmitTo=turkSubmitTo, preview_mode=preview_mode, text_to_annotate=text_to_annotate, forbidden_tokens=forbidden_tokens, annotation_types=annotation_types, worker_IDs_who_passed_step2=filterStep2["worker_IDs_who_passed"],  filter_questions_step2=filterStep2["questions"], filter_attempts_before_revealing_solution=filter_attempts_before_revealing_solution, ability_filter_threshold=ability_filter_threshold)


@textannotation_bp.route('/relations_final/<batch>/<paragraphs>')
def relations_final(batch=None, paragraphs=None):

    # load variables for this specific batch from config file
    batch_config_variables = config.batches[batch]
    # load preferred relation types from config file
    relation_types = config.relation_types[batch_config_variables['relation_types']]
    # load preferred annotation types from config file
    annotation_types = config.annotation_types[batch_config_variables['annotation_types']]
    # load batch_directory_name for paragraphs from config file
    batch_directory_name = batch_config_variables['batch_directory_name']
    # load textToAnnotate_filename for paragraphs from config file
    textToAnnotate_filename = batch_config_variables['textToAnnotate_filename']
    # load textToAnnotate_filename for paragraphs from config file
    annotations_on_load_listname = batch_config_variables['annotations_on_load']
    # load filter_attempts_before_revealing_solution from config file
    filter_attempts_before_revealing_solution = batch_config_variables[
        'filter_attempts_before_revealing_solution']
    # load ability_filter_threshold from config file
    ability_filter_threshold = batch_config_variables['ability_filter_threshold']

    worker_id = request.args.get("workerId")
    if worker_id is None:
        worker_id = 'test worker id NEW2'

    assignment_id = request.args.get("assignmentId")
    if assignment_id is None:
        assignment_id = 'test assignment id'

    #amazon_host = request.args.get('amazon_host')
    amazon_host = AMAZON_HOST
    if amazon_host is None:
        amazon_host = 'test amazon amazon_host'

    hit_id = request.args.get("hitId")
    if hit_id is None:
        hit_id = 'test hit id'

    # load the Amazon Mechanical Turk URL to which the form must post the result data back to
    turkSubmitTo = request.args.get("turkSubmitTo")
    if turkSubmitTo is None:
        turkSubmitTo = 'https://workersandbox.mturk.com/mturk/externalSubmit'
    else:
        turkSubmitTo += '/mturk/externalSubmit'

    print("WORKING:" + " worker_id='" + worker_id + "' assignment_id='" +
          assignment_id + "' hit_id='" + hit_id + "' turkSubmitTo='" + turkSubmitTo + "'")

    worker_assignment_data = {
        'worker_id': worker_id,
        'assignment_id': assignment_id,
        'hit_id': hit_id,
        'turkSubmitTo': turkSubmitTo,
        'task_type': 'relations',
        'batch': batch,
        'batch_config_variables': batch_config_variables,
        'paragraphs': paragraphs
    }

    if request.args.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        # Our worker hasn't accepted the HIT (task) yet
        preview_mode = "true"
    else:
        # Our worker accepted the task
        preview_mode = "false"

    text_to_annotate = {}
    paragraph_counter = 0

    filename = os.path.join(
        'app', 'data', batch_directory_name, textToAnnotate_filename)

    with open(filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

    for p_name in paragraphs.split(';'):
        # loop trough all paragraphs which where specified in create batch url
        text_to_annotate[paragraph_counter] = all_paragraphs[p_name]["tokens"]
        paragraph_counter += 1

    # import annotations from dynamic pathname as specified for this specific batch in config file
    annotations_on_load = importName(
        "app.data.annotations_on_load_for_relation_HITs", annotations_on_load_listname)

    annotations_on_load_paragraphs_counter = 0
    for p_annotations in annotations_on_load:
        p_a_counter = 0
        for p_a in p_annotations:
            for a_key, a_value in text_to_annotate[annotations_on_load_paragraphs_counter].items():
                # only check if the start token has not been found yet
                if p_a[0] == -1 and p_a[6] >= a_value["start"] and p_a[6] <= a_value["end"]:
                    # the start index of the annotation_on_load lies whithin the currently looked at token. The key of this token is the start_id for we were looking for.
                    p_a[0] = int(a_key)

                # only check if the end token is found when the start token has already been found
                if p_a[0] != -1 and p_a[7] >= a_value["start"] and p_a[7] <= a_value["end"]:
                    # the end index of the annotation_on_load lies whithin the currently looked at token. The key of this token is the end_id for we were looking for.
                    p_a[1] = int(a_key)

                    break

            p_a_counter += 1
        annotations_on_load_paragraphs_counter += 1

    with open(os.path.join('app', 'data', "filterStep2.json")) as f:
        filterStep2 = json.load(f)["filterStep2_argument_relation"]

    return render_template('relationannotation/relationAnnotation_instructions_final.html', worker_assignment_data=worker_assignment_data, turkSubmitTo=turkSubmitTo, preview_mode=preview_mode, text_to_annotate=text_to_annotate, annotations=annotations_on_load, annotation_types=annotation_types, relation_types=relation_types, worker_IDs_who_passed_step2=filterStep2["worker_IDs_who_passed"],  filter_questions_step2=filterStep2["questions"], filter_attempts_before_revealing_solution=filter_attempts_before_revealing_solution, ability_filter_threshold=ability_filter_threshold)


@textannotation_bp.route('/submit_data', methods=['GET', 'POST'])
def submit_data():

    # This function is called as soon as a worker clicks on the 'Submit HIT' button in a argument component annotation task. It prints all the worker answers as a log to heroku. This makes sure that even if the HIT can not be submitted by the worker on MTurk, we can still see the answers by copying the log-message in heroku. However, this function is not needed that a a worker con submit a HIT.

    message = request.args.get('message')
    timestamp = request.args.get('timestamp')
    annotations = request.args.get('annotations')
    worker_assignment_data = request.args.get('worker_assignment_data')
    feedback = request.args.get('feedback')
    logger = request.args.get('logger')
    try:
        filterData_step1 = request.args.get('filterData_step1')
    except:
        filterData_step1 = ""
    try:
        filterData_step2 = request.args.get('filterData_step2')
    except:
        filterData_step2 = ""

    print("")
    print("---------- NEW " + str(message) + " ! ---------")

    print("timestamp: " + str(timestamp))
    print("argument component annotations : " + str(json.loads(annotations)))
    print("worker_assignment_data: " + str(json.loads(worker_assignment_data)))
    print("feedback: " + str(feedback))
    print("logger: " + str(logger))
    print("filterData_step1: " + str(filterData_step1))
    print("filterData_step2: " + str(filterData_step2))

    print("---------- END " + str(message) + " ! ---------")
    print("")

    sys.stdout.flush()

    return "true"


@textannotation_bp.route('/submit_data_wrongfilter2answer', methods=['GET', 'POST'])
def submit_data_wrongfilter2answer():

    # This function is called as soon as a worker clicks on the 'CHECK' button in filter step 2. It prints the current worker answers as a log to heroku. This makes sure that even if the HIT can not be submitted by the worker on MTurk, we can still see the answers by copying the log-message in heroku. However, this function is not needed that a a worker con submit a HIT.

    print("wronganswer hit/assignment/worker")
    
    try:
        worker_assignment_data = request.args.get('worker_assignment_data')
        print(str(json.loads(worker_assignment_data)["worker_id"]), str(json.loads(worker_assignment_data)["assignment_id"]), str(json.loads(worker_assignment_data)["hit_id"]))
    except:
        pass
    
    try:
        current_filter_step = request.args.get('current_filter_step')
        print("current_filter_step", str(current_filter_step))
    except:
        pass
    
    try:
        nr_of_tries = request.args.get('nr_of_tries')
        print("nr_of_tries", str(nr_of_tries))
    except:
        pass
    
    try:
        last_tried_annotation = request.args.get('last_tried_annotation')
        print("last_tried_annotation", str(json.loads(last_tried_annotation)))
    except:
        pass
    

    return "true"


@textannotation_bp.route('/submit_data_relation', methods=['GET', 'POST'])
def submit_data_relation():

    # This function is called as soon as a worker clicks on the 'Submit HIT' button in a argument relation annotation task. It prints all the worker answers as a log to heroku. This makes sure that even if the HIT can not be submitted by the worker on MTurk, we can still see the answers by copying the log-message in heroku. However, this function is not needed that a a worker con submit a HIT.

    message = request.args.get('message')
    timestamp = request.args.get('timestamp')
    annotations_on_load = request.args.get('annotations_on_load')
    annotations = request.args.get('annotations')
    worker_assignment_data = request.args.get('worker_assignment_data')
    feedback = request.args.get('feedback')
    logger = request.args.get('logger')
    try:
        filterData_step1 = request.args.get('filterData_step1')
    except:
        filterData_step1 = ""
    try:
        filterData_step2 = request.args.get('filterData_step2')
    except:
        filterData_step2 = ""
    

    print("")
    print("---------- NEW " + str(message) + " ! ---------")

    print("timestamp: " + str(timestamp))
    print("annotations_on_load : " + str(json.loads(annotations_on_load)))
    print("argument relation annotations : " + str(json.loads(annotations)))
    print("worker_assignment_data: " + str(json.loads(worker_assignment_data)))
    print("feedback: " + str(feedback))
    print("logger: " + str(logger))
    print("filterData_step1: " + str(filterData_step1))
    print("filterData_step2: " + str(filterData_step2))

    print("---------- END " + str(message) + " ! ---------")
    print("")

    sys.stdout.flush()

    return "true"
