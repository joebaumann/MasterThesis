import json
import os
from sklearn.metrics import f1_score, confusion_matrix, classification_report
from collections import Counter
from statistics import mean, stdev, median
import pandas as pd
import numpy as np
from itertools import combinations
import csv
from mace_runner import aggregate_worker_answers_with_MACE


# define the filenames to include
#filenames_components = 'H1a_worker_answers.txt' # H1a
filenames_components = 'H1b_worker_answers.txt' # H1b


# choose which asignment status should be considered for the analysis: 'Submitted'|'Approved'|'Rejected'
assignment_status_to_include_in_analysis = ['Submitted', 'Approved', 'Rejected']

create_hits_in_production = True


do_not_consider_type = False

def getGroundTruthData_components():

    # get amount of characters in paper
    with open("/app/data/batch1/entire_paper/A11.txt") as f:
        entire_paper_nr_of_character = len(f.read())
        print("entire_paper_nr_of_character: ", entire_paper_nr_of_character)

    # initialize lauscher list with 'none' annotations (for comparison with worker annotations)
    lauscher_annotation_list = []

    for i in range(entire_paper_nr_of_character):
        lauscher_annotation_list.append('none')

    with open("/MasterThesis/Lauscher_Corpus/compiled_corpus/A11.ann") as f:
        lines = f.readlines()
        # filter out relations to only consider argument components
        lines = [line for line in lines if line[0] == 'T']
        for l in lines:
            line = l.strip('\n')
            line_elements = line.split("\t")
            type_lauscher = line_elements[1].split(" ")[0]
            if type_lauscher == 'background_claim':
                type = 'backgroundclaim'
            elif type_lauscher == 'own_claim':
                type = 'ownclaim'
            elif type_lauscher == 'data':
                type = 'data'
            start = int(line_elements[1].split(" ")[1])
            end = int(line_elements[1].split(" ")[2])
            for i in range(start, end):
                lauscher_annotation_list[i] = type
    
    return lauscher_annotation_list


# The next code section creates a json file containing only the annotations for all argument component and relation annotation tasks.

def getAggregatedAnnotationsForFilepath(filepath, assignment_status_to_include_in_analysis, ground_truth_data_on_character_level):
    all_annotations = {}
    all_annotations_statistics = {}
    filter_step2_results = {}


    # load the entire paper to then be able to get the text of an annotation
    with open("/app/data/batch1/entire_paper/A11.txt") as paper:
        entire_paper = paper.read()

    # load the json file to then be able to get a token which was annotated as a keyword based on the token id
    with open("/app/data/batch1/A11_ToBeAnnotated.json") as json_file:
        entire_json_file = json.load(json_file)

    # to load the worker answer from the saved txt file, load json in the following way:
    with open(filepath, "r") as f:
        all_answers = json.load(f)
        
        all_answers_included_in_analysis = [(x,y) for (x,y) in all_answers.items() if y["AssignmentStatus"] in assignment_status_to_include_in_analysis]
        
        #for assignment_id, answer in all_answers.items():
        
        for assignment_id, answer in all_answers_included_in_analysis:

            HITId = answer['HITId']
            WorkerId = answer['WorkerId']
            AssignmentId = answer['AssignmentId']
            annotations = json.loads(answer['worker_answer']['submit_annotations'])
            this_workers_filter_step2_results = json.loads(answer['worker_answer']['submit_filter_data_step2'])

            filter_step2_results[AssignmentId] = this_workers_filter_step2_results

            paragraphs = (json.loads(answer['worker_answer']['submit_worker_assignment_data'])['paragraphs']).split(';')
            print("We are now looking at the assignment (ID =", AssignmentId, ") from worker (ID =", WorkerId, "), who annotated the following paragraphs: ", paragraphs)

            paragraph_counter = 0

            if annotations == []:
                # worker did not do any annotation
                # add an empty list for each paragraph the worker should have annotated so that 'none' annotations can be initialized
                for x in paragraphs:
                    annotations.append([])
            
            for p in annotations:
                # 'annotations' are all worker annotations. It contains one list per annotated paragraph.

                paragraph = paragraphs[paragraph_counter]
                # check if it is the first time that this paragraph is being checked
                if paragraph in all_annotations:
                    this_paragraphs_tokens = all_annotations[paragraph]
                    this_paragraphs_statistics = all_annotations_statistics[paragraph]
                
                else:
                    # initialize tokens list for this paragraph
                    
                    this_paragraphs_tokens = {}
                    this_paragraphs_statistics = {"annotation_counter_for_this_paragraph":0}

                    for token_id, token_val in entire_json_file['text_to_annotate'][paragraph]['tokens'].items():
                        ground_truth_annotations_for_this_token = []
                        for i in range(token_val['start'], token_val['end']):
                            ground_truth_annotations_for_this_token.append(ground_truth_data_on_character_level[i])
                            
                        if len(set(ground_truth_annotations_for_this_token)) > 1:
                            nr_of_occurences_of_type_annotation_for_this_token = []
                            #loop trough all annotation types which were found in ground truth within this token, except 'none'
                            for anno_type in [x for x in set(ground_truth_annotations_for_this_token) if x != 'none']:
                                nr_of_occurences_of_type_annotation_for_this_token.append((anno_type, ground_truth_annotations_for_this_token.count(anno_type)))
                            # find the annotation type which was annotated for the most of the characters of this token
                            # if the annotation type was used for the same amount of characters, take any one
                            chosen_annotation_type = ("", 0)
                            for anno_type in nr_of_occurences_of_type_annotation_for_this_token:
                                if anno_type[1] > chosen_annotation_type[1]:
                                    chosen_annotation_type = anno_type
                            ground_truth_annotation = chosen_annotation_type[0]
                            if len(nr_of_occurences_of_type_annotation_for_this_token) > 0:
                                pass
                                #raise Exception("Different annotation types in one token!")
                        else:
                            # all characters of the token were annotated with the same annotation type
                            ground_truth_annotation = ground_truth_annotations_for_this_token[0]

                        this_paragraphs_tokens[token_id] = {
                            "paragraph": paragraph,
                            "token_id": token_id,
                            "token_text": token_val['token'],
                            "token_start": token_val['start'],
                            "token_end": token_val['end'],
                            "worker_annotations": [],
                            "ground_truth_annotation": ground_truth_annotation,
                        }

                # append a new value 'none' to the worker_annotation_list of each token.
                # Afterwards we will change the value 'none' to backgroundclaim/ownclaim/date for every token a worker annotated.
                for token_id, token_val in this_paragraphs_tokens.items():
                    token_val["worker_annotations"].append((AssignmentId, "none"))

                # update the tokens list based on workers annotations, if worker did at least one annotation in this paragraph
                if p is not None:
                    for a in p:
                        # 'a' is one annotation that a worker did in paragraph 'p'

                        this_paragraphs_statistics["annotation_counter_for_this_paragraph"] += 1
                        
                        worker_annotation_START_token_id = a[0]
                        worker_annotation_END_token_id = a[1]
                        annotation_type = a[2]
                        certainty = a[3]
                        explanation = a[4]
                        selected_keyword_IDs = a[5]
                        char_index_start = a[6]
                        char_index_end = a[7]
                        annotation_text = entire_paper[char_index_start:char_index_end]
                            
                        # loop through all the tokens of this worker_annotation
                        for worker_annotation_token_id in range(worker_annotation_START_token_id, worker_annotation_END_token_id+1):
                            this_paragraphs_tokens[str(worker_annotation_token_id)]['worker_annotations'][-1] = (AssignmentId, annotation_type)
                    

                paragraph_counter += 1
                all_annotations[paragraph] = this_paragraphs_tokens
                all_annotations_statistics[paragraph] = this_paragraphs_statistics


    return all_annotations, all_annotations_statistics, filter_step2_results


if create_hits_in_production:
    environment_name = 'production'
else:
    environment_name = 'sandbox'

ground_truth_data = getGroundTruthData_components()


# aggregate annotations for HIT 1
print("Let's aggregate the answers from the following file:",filenames_components)
filepath = os.path.join('MTurk', 'WorkerAnswers',environment_name,'componentAnnotation',filenames_components)
aggregated_annotations, all_annotations_statistics, filter_step2_results = getAggregatedAnnotationsForFilepath(filepath, assignment_status_to_include_in_analysis, ground_truth_data)


"""
"""

if do_not_consider_type:
    # If do_not_consider_type is set to True, this block is executed.
    # This block makes sure that the entire analysis is done without considering the type of the component annotation.
    for paragraph_name, paragraph_value in aggregated_annotations.items():
        # loop through all paragraphs
        for token_id, token_value in paragraph_value.items():
            # loop through all tokens
            if token_value["ground_truth_annotation"] != "none":
                # ground truth is not 'none'
                aggregated_annotations[paragraph_name][token_id]["ground_truth_annotation"] = "NotNone"
            for i, (assignment_id, annotation) in enumerate(token_value["worker_annotations"]):
                # loop through all worker annotations for this token
                if annotation != "none":
                    aggregated_annotations[paragraph_name][token_id]["worker_annotations"][i] = (assignment_id, "NotNone")





print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("~~~~~~~~~ performances of workers per paragraph ~~~~~~~~~")
print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("")
print("")

ground_truth_OVERALL = []
ground_truth_OVERALL_per_paragraph = {}
worker_answers_OVERALL = {}
f1_per_paragraph = {}
f1_OVERALL = []

ground_truth_OVERALL_completed_paragraphs = []

# get f1 PER PARAGRAPH for each worker
for paragraph_name, paragraph_value in aggregated_annotations.items():
    # loop trough every paragraph
    print("")
    print("------ paragraph_name:", paragraph_name, "------")
    print("")
    for assignment_id, assignment_value in filter_step2_results.items():
        # now loop trough every assignment (i.e. every worker who completed this task)
        filter_passed = assignment_value["filterPassed"]
        if paragraph_name not in f1_per_paragraph:
            f1_per_paragraph[paragraph_name] = []
        # check if there is already a list for this assignment in the worker_answers_OVERALL dict
        if assignment_id not in worker_answers_OVERALL:
            worker_answers_OVERALL[assignment_id] = []
        print("")
        print("#######-start")
        print("Performance of", assignment_id, " [filter_passed =", filter_passed, "] in", paragraph_name, ":")
        ground_truth = []
        this_workers_annotations = []
        for token_id, token_value in paragraph_value.items():
            # and now loop trough every token in this paragraph
            # get ground truth annotation for this token
            gt_annotation = token_value["ground_truth_annotation"]

            # this if condition filters out true 'none' annotation
            #if gt_annotation != 'none':


            ground_truth.append(gt_annotation)
            # the first time we go trough all tokens of all paragraphs, we want to add the ground truth annotation to the list.
            if paragraph_name not in ground_truth_OVERALL_per_paragraph:
                ground_truth_OVERALL_per_paragraph[paragraph_name] = []
            if paragraph_name not in ground_truth_OVERALL_completed_paragraphs:
                ground_truth_OVERALL.append(gt_annotation)
                ground_truth_OVERALL_per_paragraph[paragraph_name].append(gt_annotation)
            # get worker annotation for this token
            worker_annotation = [a[1] for a in token_value["worker_annotations"] if a[0] == assignment_id][0]
            this_workers_annotations.append(worker_annotation)
            worker_answers_OVERALL[assignment_id].append(worker_annotation)
        
        
        unique_label = np.unique(["ownclaim", "backgroundclaim", "data", "none"])
        cmtx = pd.DataFrame(
            confusion_matrix(ground_truth, this_workers_annotations, labels=unique_label), 
            index=['true:{:}'.format(x) for x in unique_label], 
            columns=['pred:{:}'.format(x) for x in unique_label]
        )

        # and now print the confusion matrix including the row- and comlumn-names
        print(cmtx)

        print("")
        print(confusion_matrix(ground_truth, this_workers_annotations))
        print("")
        print(classification_report(ground_truth, this_workers_annotations, digits=3))
        print("")

        f1_score_micro = f1_score(ground_truth, this_workers_annotations,average='micro') # consider type
        print("f1_score_micro/accuracy:", f1_score_micro)
        #f1_score_micro = f1_score([0 if x == 'none' else 1 for x in ground_truth], [0 if x == 'none' else 1 for x in this_workers_annotations],average='micro') # ignore type


        print("f1_score_micro/accuracy [IGNORE TYPE]:", f1_score_micro)
        print("#######-end")
        print("")

        f1_per_paragraph[paragraph_name].append({"filter_passed":filter_passed, "f1":f1_score_micro})

        ground_truth_OVERALL_completed_paragraphs.append(paragraph_name)


print("")
print("")
print("")
print("")
print("")
print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("~~~~~~~~~ performances of workers for entire task (so not for each paragraph) ~~~~~~~~~")
print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("")
print("")

bonus_payment_info = []

# now get f1 for each worker
for assignment_id, worker_annotation in worker_answers_OVERALL.items():
    filter_passed = filter_step2_results[assignment_id]["filterPassed"]
    print("")
    print("#######-start")
    print("Performance of", assignment_id, " [filter_passed =", filter_passed, "]:")
    print("")


    unique_label = np.unique(["ownclaim", "backgroundclaim", "data", "none"])
    cmtx = pd.DataFrame(
        confusion_matrix(ground_truth_OVERALL, worker_annotation, labels=unique_label), 
        index=['true:{:}'.format(x) for x in unique_label], 
        columns=['pred:{:}'.format(x) for x in unique_label]
    )

    # and now print the confusion matrix including the row- and comlumn-names
    print(cmtx)

    print("")
    print(confusion_matrix(ground_truth_OVERALL, worker_annotation))
    print("")
    print(classification_report(ground_truth_OVERALL, worker_annotation, digits=3))
    print("")
    f1_score_micro = f1_score(ground_truth_OVERALL, worker_annotation,average='micro')
    print("f1_score_micro/accuracy:", f1_score_micro)
    print("#######-end")
    print("")
    f1_OVERALL.append({"filter_passed":filter_passed, "f1":f1_score_micro})
    bonus_payment_info.append((assignment_id,'p' if filter_passed == True else 'f',f1_score_micro))




print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("~~~~~~~~~ performances of aggregated worker answers (with MACE) per paragraph ~~~~~~~~~")
print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("")
print("")

def get_worker_answer_aggregation_combinations(workers, combination_size):
    if len(workers) < combination_size:
        return [tuple(workers)]
    else:
        return list(combinations(workers, combination_size))


# filter is passed only if all 3 answers are correct
all_workers = list(filter_step2_results.keys())

h1b_data = []


# loop trough all answers by all workers
for paragraph_name, paragraph_value in aggregated_annotations.items():
    print("paragraph:", paragraph_name)
    this_paragraphs_ground_truth = []
    for token_id, token_value in paragraph_value.items():
        # and now loop trough every token in this paragraph
        # get ground truth annotation for this token
        gt_annotation = token_value["ground_truth_annotation"]
        this_paragraphs_ground_truth.append(gt_annotation)

    combination_size = 3

    # calculate f1 scores for aggregation combinations of all workers
    worker_combinations = get_worker_answer_aggregation_combinations(all_workers, combination_size)
    for combination in worker_combinations:
        all_worker_answers = []
        for token_id, token_value in paragraph_value.items():
            this_tokens_worker_answers = []
            # select answers from those worker answers who are present in the current combination
            this_tokens_worker_answers = [annotation for assignment_id, annotation in token_value["worker_annotations"] if assignment_id in combination]
            all_worker_answers.append(this_tokens_worker_answers)
        
        

        nr_of_tries_sum_combined = 0
        nr_of_tries_stdev_combined = 0
        nr_of_tries_median_combined = 0
        total_nr_of_empty_and_wrong_answers_combined = 0

        for assignment_id in combination:
            # loop through the ids of contained in this combination to combine these worker's attempts in the filter step 2




            nr_of_tries = []
            total_nr_of_solution_revealed = 0
            total_nr_of_empty_and_wrong_answers = 0

            for filter_question_id, filter_question_value in filter_step2_results[assignment_id]["tried_parts"].items():
                nr_of_tries.append(filter_question_value["nr_of_tries"])
                if filter_question_value["solution_revealed"] == True:
                    total_nr_of_solution_revealed += 1
                for tried_annnotation in filter_question_value["annotations"]:
                    if filter_question_id not in ["4", "6"] and tried_annnotation == []:
                        # The correct answer for questions "4" and "6" is to not annotate anything. Therefore, do not count these empty answers since they are not wrong.
                        total_nr_of_empty_and_wrong_answers += 1
            

            nr_of_tries_sum_combined += sum(nr_of_tries)
            nr_of_tries_stdev_combined += stdev(nr_of_tries)
            nr_of_tries_median_combined += median(nr_of_tries)
            all_answers_all_tries = {k:v["annotations"] for (k,v) in filter_step2_results[assignment_id]["tried_parts"].items()}
                        
            total_nr_of_empty_and_wrong_answers_combined += total_nr_of_empty_and_wrong_answers


        # compute the average for the workers attempts for filter step 2
        nr_of_tries_sum_combined_AVG = nr_of_tries_sum_combined / len(combination)
        nr_of_tries_median_combined_AVG = nr_of_tries_median_combined / len(combination)
        total_nr_of_empty_and_wrong_answers_combined_AVG = total_nr_of_empty_and_wrong_answers_combined / len(combination)

        
        
        
        # aggregate worker answers with MACE
        aggregated_worker_answers = aggregate_worker_answers_with_MACE(all_worker_answers)
        # calculate f1 score micro (true: ground_truth, pred: worker answers aggregated with MACE)
        f1_score_micro = f1_score(this_paragraphs_ground_truth, aggregated_worker_answers,average='micro')

        # calculate f1 score micro but ignore if component type is correct or not
        f1_score_IGNORE_TYPE = f1_score(['none' if x == 'none' else 'NotNone' for x in this_paragraphs_ground_truth], ['none' if x == 'none' else 'NotNone' for x in aggregated_worker_answers],average='micro')

        h1b_data.append([nr_of_tries_median_combined_AVG,nr_of_tries_sum_combined_AVG,total_nr_of_empty_and_wrong_answers_combined_AVG,f1_score_micro,f1_score_IGNORE_TYPE])





# initialize csv file to save results from H1b worker answers
csv_filename = 'H1b_scores_components.csv'

with open(os.path.join('AnswerAggregationAndPerformanceEvaluation', csv_filename), 'w', newline='') as file:
    writer = csv.writer(file)
    
    # write header
    writer.writerow(["nr_of_tries_median","nr_of_tries_sum","total_nr_of_empty_and_wrong_answers","f1","f1_score_IGNORE_TYPE"])

    writer.writerows(h1b_data)