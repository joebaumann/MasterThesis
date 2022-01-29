import json
import os
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix, classification_report
from collections import Counter
from pprint import pprint
from statistics import mean, stdev
import pandas as pd
import numpy as np
from subprocess import Popen, PIPE, STDOUT
from itertools import combinations
import csv
from mace_runner import aggregate_worker_answers_with_MACE
from power_analysis import power_analysis


# define the filenames to include
#filenames_components = ['H1a_worker_answers_withoutEmptyAnswers.txt'] # H1a
filenames_components = ['H1a_worker_answers.txt'] # H1a


# choose which asignment status should be considered for the analysis: 'Submitted'|'Approved'|'Rejected'
assignment_status_to_include_in_analysis = ['Submitted', 'Approved', 'Rejected']

create_hits_in_production = True


do_not_consider_type = True

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
    filter_step1_results = {}


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
            this_workers_filter_step1_results = json.loads(answer['worker_answer']['submit_filter_data_step1'])

            filter_step1_results[AssignmentId] = this_workers_filter_step1_results

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


    return all_annotations, all_annotations_statistics, filter_step1_results



if create_hits_in_production:
    environment_name = 'production'
else:
    environment_name = 'sandbox'

ground_truth_data = getGroundTruthData_components()


# aggregate annotations for HIT 1
print("Let's aggregate the answers from the following file:",filenames_components)
print("")
filepath = os.path.join('MTurk', 'WorkerAnswers',environment_name,'componentAnnotation',filenames_components)
aggregated_annotations, all_annotations_statistics, filter_step1_results = getAggregatedAnnotationsForFilepath(filepath, assignment_status_to_include_in_analysis, ground_truth_data)


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
    for assignment_id, assignment_value in filter_step1_results.items():
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
        
        if do_not_consider_type:
            f1_score_micro = f1_score([0 if x == 'none' else 1 for x in ground_truth], [0 if x == 'none' else 1 for x in this_workers_annotations],average='micro') # ignore type


        print("f1_score_micro/accuracy [IGNORE TYPE]:", f1_score_micro)
        print("#######-end")
        print("")

        f1_per_paragraph[paragraph_name].append({"filter_passed":filter_passed, "f1":f1_score_micro})

        ground_truth_OVERALL_completed_paragraphs.append(paragraph_name)


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
    filter_passed = filter_step1_results[assignment_id]["filterPassed"]
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



print("")
print("")
print("")
print("")
print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("~~~~~~~~~ GROUP performances of workers OVERALL ~~~~~~~~~")
print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("")
print("")
f1_OVERALL_filter_passed = [i for i in f1_OVERALL if i["filter_passed"] is True]
f1_OVERALL_filter_failed = [i for i in f1_OVERALL if i["filter_passed"] is False]
print("f1_OVERALL_filter_passed:", f1_OVERALL_filter_passed)
print("f1_OVERALL_filter_failed:", f1_OVERALL_filter_failed)
print("# filter passed:", len(f1_OVERALL_filter_passed))
print("# filter failed:", len(f1_OVERALL_filter_failed))
print("filter passed f1 mean:", mean([i["f1"] for i in f1_OVERALL_filter_passed]))
print("filter failed f1 mean:", mean([i["f1"] for i in f1_OVERALL_filter_failed]))
#print("filter passed f1 stdev:", stdev([i["f1"] for i in f1_OVERALL_filter_passed]))
print("filter failed f1 stdev:", stdev([i["f1"] for i in f1_OVERALL_filter_failed]))


print("")
print("")
print("")
print("")
print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("~~~~~~~~~ GROUP performances of workers PER PARAGRAPH ~~~~~~~~~")
print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("")
print("")

all_f1_filter_passed = []
all_f1_filter_failed = []

for paragraph_name, paragraph_value in f1_per_paragraph.items():

    print("")
    print("~~~~~~~~~~~~~~~~~~~~~")
    print(paragraph_name)

    f1_paragraph_filter_passed = [i for i in paragraph_value if i["filter_passed"] is True]
    f1_paragraph_filter_failed = [i for i in paragraph_value if i["filter_passed"] is False]

    all_f1_filter_passed.extend(f1_paragraph_filter_passed)
    all_f1_filter_failed.extend(f1_paragraph_filter_failed)
    
    print("    f1_paragraph_filter_passed:", f1_paragraph_filter_passed)
    print("    f1_paragraph_filter_failed:", f1_paragraph_filter_failed)
    print("    # filter passed:", len(f1_paragraph_filter_passed))
    print("    # filter failed:", len(f1_paragraph_filter_failed))
    print("    filter passed f1 mean:", mean([i["f1"] for i in f1_paragraph_filter_passed]))
    print("    filter failed f1 mean:", mean([i["f1"] for i in f1_paragraph_filter_failed]))
    #print("    filter passed f1 stdev:", stdev([i["f1"] for i in f1_paragraph_filter_passed]))
    print("    filter failed f1 stdev:", stdev([i["f1"] for i in f1_paragraph_filter_failed]))


nr_of_workers_who_passed_filter = len({k:v for (k,v) in filter_step1_results.items() if v["filterPassed"] == True})
nr_of_workers_who_failed_filter = len({k:v for (k,v) in filter_step1_results.items() if v["filterPassed"] == False})

print("")
print("all_f1_filter_passed:")
print(nr_of_workers_who_passed_filter,"workers passed the filter. So we have data from", len(all_f1_filter_passed), "paragraphs which come from", nr_of_workers_who_passed_filter,"different workers.")
print(all_f1_filter_passed)
print("")
print("all_f1_filter_failed:")
print(nr_of_workers_who_failed_filter,"workers failed the filter. So we have data from", len(all_f1_filter_failed), "paragraphs which come from", nr_of_workers_who_failed_filter,"different workers.")
print(all_f1_filter_failed)
print("")
print("filter passed f1 mean:", mean([i["f1"] for i in all_f1_filter_passed]))
print("filter failed f1 mean:", mean([i["f1"] for i in all_f1_filter_failed]))
print("")
print("filter passed f1 stdev:", stdev([i["f1"] for i in all_f1_filter_passed]))
print("filter failed f1 stdev:", stdev([i["f1"] for i in all_f1_filter_failed]))




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
workers_who_passed_filter = list({k:v for (k,v) in filter_step1_results.items() if v["filterPassed"] == True}.keys())
workers_who_failed_filter = list({k:v for (k,v) in filter_step1_results.items() if v["filterPassed"] == False}.keys())

# filter is passed if at least 2 answers are correct
#workers_who_passed_filter = list({k:v for (k,v) in filter_step1_results.items() if len(v["correct_answers"]) >= 2}.keys())
#workers_who_failed_filter = list({k:v for (k,v) in filter_step1_results.items() if len(v["correct_answers"]) < 2}.keys())

f1_scores_of_mace_aggregated_datapoints_by_paragraph = {"filter_passed": {}, "filter_failed": {}}

# loop trough all answers by all workers
for paragraph_name, paragraph_value in aggregated_annotations.items():
    print("para:", paragraph_name)
    this_paragraphs_ground_truth = []
    for token_id, token_value in paragraph_value.items():
        # and now loop trough every token in this paragraph
        # get ground truth annotation for this token
        gt_annotation = token_value["ground_truth_annotation"]
        this_paragraphs_ground_truth.append(gt_annotation)

    combination_size = 3

    # calculate f1 scores for aggregation combinations of those workers who PASSED filter
    worker_combinations = get_worker_answer_aggregation_combinations(workers_who_passed_filter, combination_size)
    for combination in worker_combinations:
        print("passed:", combination)
        all_worker_answers = []
        for token_id, token_value in paragraph_value.items():
            this_tokens_worker_answers = []
            # select answers from those worker answers who are present in the current combination
            this_tokens_worker_answers = [annotation for assignment_id, annotation in token_value["worker_annotations"] if assignment_id in combination]
            all_worker_answers.append(this_tokens_worker_answers)
        # aggregate worker answers with MACE
        aggregated_worker_answers = aggregate_worker_answers_with_MACE(all_worker_answers)
        # calculate f1 score micro (true: ground_truth, pred: worker answers aggregated with MACE)
        f1_score_micro = f1_score(this_paragraphs_ground_truth, aggregated_worker_answers,average='micro')
        if paragraph_name not in f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_passed"].keys():
            f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_passed"][paragraph_name] = []
        # add calculated f1_score to list
        f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_passed"][paragraph_name].append(f1_score_micro)

    # calculate f1 scores for aggregation combinations of those workers who FAILED filter
    worker_combinations = get_worker_answer_aggregation_combinations(workers_who_failed_filter, combination_size)
    for combination in worker_combinations:
        print("failed:", combination)
        all_worker_answers = []
        for token_id, token_value in paragraph_value.items():
            this_tokens_worker_answers = []
            # select answers from those worker answers who are present in the current combination
            this_tokens_worker_answers = [annotation for assignment_id, annotation in token_value["worker_annotations"] if assignment_id in combination]
            all_worker_answers.append(this_tokens_worker_answers)
        # aggregate worker answers with MACE
        aggregated_worker_answers = aggregate_worker_answers_with_MACE(all_worker_answers)
        # calculate f1 score micro (true: ground_truth, pred: worker answers aggregated with MACE)
        f1_score_micro = f1_score(this_paragraphs_ground_truth, aggregated_worker_answers,average='micro')
        if paragraph_name not in f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_failed"].keys():
            f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_failed"][paragraph_name] = []
        # add calculated f1_score to list
        f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_failed"][paragraph_name].append(f1_score_micro)

    
print("")
print(f1_scores_of_mace_aggregated_datapoints_by_paragraph)
print("")
print("")

print("Create CSV file for 2 sample t-test in R")

if do_not_consider_type:
    csv_filename = 'H1a_scores_components_without_considering_type.csv'
else:
    csv_filename = 'H1a_scores_components.csv'

with open(os.path.join('AnswerAggregationAndPerformanceEvaluation', csv_filename), 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["group","f1"])
    for paragraph_name, f1_scores in f1_scores_of_mace_aggregated_datapoints_by_paragraph['filter_passed'].items():
        for score in f1_scores:
            writer.writerow(["passed",score])
    for paragraph_name, f1_scores in f1_scores_of_mace_aggregated_datapoints_by_paragraph['filter_failed'].items():
        for score in f1_scores:
            writer.writerow(["failed",score])


print("POWER ANALYSIS:")
print("")

prepare_data_for_pa = {'group_name':[], 'total_score':[]}

count_passed = 0
for paragraph_name, f1_scores in f1_scores_of_mace_aggregated_datapoints_by_paragraph['filter_passed'].items():
    for score in f1_scores:
        prepare_data_for_pa['group_name'].append('passed')
        prepare_data_for_pa['total_score'].append(score)
        count_passed += 1
print("We have", count_passed, "data points for workers who PASSED the filter.")
    
count_failed = 0
for paragraph_name, f1_scores in f1_scores_of_mace_aggregated_datapoints_by_paragraph['filter_failed'].items():
    for score in f1_scores:
        prepare_data_for_pa['group_name'].append('failed')
        prepare_data_for_pa['total_score'].append(score)
        count_failed += 1
print("We have", count_failed, "data points for workers who FAILED the filter.")
    

# data from H1a (f1 per worker per paragraph): 10 total workers, (7 failed, 3 passed filter)

# perform power analysis
power_analysis(prepare_data_for_pa)

print("DONE...")


print("")
print("")
print("------- Bonus payment suggestions -------")
print("")
print("I suggest to pay the following bonus payments [based on a workers average f1 across all paragraphs]:")
print("")

max_bonus = 3.6

total_bonus_payments = 0
for assignment_id, filter_result, f1 in bonus_payment_info:
    # do not pay the ones who failed the filter for going trough the instructions
    deserved_percentage = f1 * max_bonus
    total_bonus_payments += deserved_percentage
    print(assignment_id, "[", filter_result, "] ", ":  pay", round(deserved_percentage, 2), "$ (", round(f1, 15), "% of the max bonus which would be $" + str(max_bonus) + ". )")
print("Expenses for all bonus payments will be:", round(total_bonus_payments, 2), "$")
print("")

print("done.")


