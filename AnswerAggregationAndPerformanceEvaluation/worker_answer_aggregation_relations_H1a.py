import csv
import json
import os
from collections import Counter
from itertools import combinations, permutations
from statistics import mean

from sklearn.metrics import f1_score

from mace_runner import aggregate_worker_answers_with_MACE
from power_analysis import power_analysis



# define the filenames to include
filenames = 'H1a_worker_answers.txt' # H1a: for power analysis


# choose which asignment status should be considered for the analysis: 'Submitted'|'Approved'|'Rejected'
assignment_status_to_include_in_analysis = ['Submitted', 'Approved', 'Rejected']



component_objects_with_ground_truth_and_worker_annotated_relations = {}


class Component:
    def __init__(self, paragraph_name, start, end, component_type, component_id, text):
        self.paragraph_name = paragraph_name
        self.start = start
        self.end = end
        self.component_type = component_type
        self.component_id = component_id
        self.text = text

        self.ground_truth_supports = []
        self.ground_truth_contradicts = []
        self.ground_truth_partsofsame = []

        self.worker_annotation_supports = []
        self.worker_annotation_contradicts = []
        self.worker_annotation_partsofsame = []


    def __str__(self):
        return 'Component(paragraph_name='+self.paragraph_name+', start='+str(self.start)+', end='+str(self.end)+', component_type='+self.component_type+', component_id='+self.component_id+', text='+str(self.text)+', ground_truth_supports='+str(self.ground_truth_supports)+', ground_truth_contradicts='+str(self.ground_truth_contradicts)+', ground_truth_partsofsame='+str(self.ground_truth_partsofsame)+', worker_annotation_supports='+str(self.worker_annotation_supports)+', worker_annotation_contradicts='+str(self.worker_annotation_contradicts)+', worker_annotation_partsofsame='+str(self.worker_annotation_partsofsame) + ')'
    
    def add_ground_truth_relation(self, paragraph_name, component, relation_type):
        global component_objects_with_ground_truth_and_worker_annotated_relations


        # depending on which type the relation is, add the component to the list
        if relation_type == 'supports':
            # self-component supports component
            # supports relation is not symmetric
            self.ground_truth_supports.append(component)
        elif relation_type == 'contradicts':
            # self-component contradicts component
            self.ground_truth_contradicts.append(component)
            # this means that component also supports self-component
            component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name][component].add_ground_truth_symmetric_relation(paragraph_name, (self.start, self.end), relation_type)
        elif relation_type == 'partsofsame':
            # self-component partsofsame component
            self.ground_truth_partsofsame.append(component)
            # this means that component also supports self-component
            component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name][component].add_ground_truth_symmetric_relation(paragraph_name, (self.start, self.end), relation_type)
    
    def add_ground_truth_symmetric_relation(self, paragraph, component, relation_type):
        # depending on which type the relation is, add the component to the list
        if relation_type == 'contradicts':
            self.ground_truth_contradicts.append(component)
        elif relation_type == 'partsofsame':
            #self-component partsofsame component
            self.ground_truth_partsofsame.append(component)



    def add_worker_annotation_relation(self, assignment_id, paragraph_name, component, relation_type):
        global component_objects_with_ground_truth_and_worker_annotated_relations


        # depending on which type the relation is, add the component to the list
        if relation_type == 'supports':
            # self-component supports component
            # supports relation is not symmetric
            self.worker_annotation_supports.append({"assignment_id": assignment_id, "component": component})
        elif relation_type == 'contradicts':
            # self-component contradicts component
            self.worker_annotation_contradicts.append({"assignment_id": assignment_id, "component": component})
            # this means that component also supports self-component
            component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name][component].add_worker_annotation_symmetric_relation(assignment_id, paragraph_name, (self.start, self.end), relation_type)
        elif relation_type == 'partsofsame':
            # self-component partsofsame component
            self.worker_annotation_partsofsame.append({"assignment_id": assignment_id, "component": component})
            # this means that component also supports self-component
            component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name][component].add_worker_annotation_symmetric_relation(assignment_id, paragraph_name, (self.start, self.end), relation_type)
    
    def add_worker_annotation_symmetric_relation(self, assignment_id, paragraph, component, relation_type):
        # depending on which type the relation is, add the component to the list
        if relation_type == 'contradicts':
            self.worker_annotation_contradicts.append({"assignment_id": assignment_id, "component": component})
        elif relation_type == 'partsofsame':
            #self-component partsofsame component
            self.worker_annotation_partsofsame.append({"assignment_id": assignment_id, "component": component})


    def get_ground_truth_relation(self, target):
        if target in self.ground_truth_supports:
            return "supports"
        elif target in self.ground_truth_contradicts:
            return "contradicts"
        elif target in self.ground_truth_partsofsame:
            return "partsofsame"
        else:
            return "none"

    def get_worker_annotation_relation(self, assignment_id, target):
        # check if there is any annotation from this assignment_id
        if {"assignment_id": assignment_id, "component": target} in self.worker_annotation_supports:
            return "supports"
        elif {"assignment_id": assignment_id, "component": target} in self.worker_annotation_contradicts:
            return "contradicts"
        elif {"assignment_id": assignment_id, "component": target} in self.worker_annotation_partsofsame:
            return "partsofsame"
        else:
            # this worker did not annotate this source-target relation
            return "none"
    
    def get_supports_and_contradicts_worker_annotation_relations(self, assignment_id):
        return [x for x in self.worker_annotation_supports if x["assignment_id"] == assignment_id], [x for x in self.worker_annotation_contradicts if x["assignment_id"] == assignment_id]
    
    def adjust_object_for_worker_annotation_parts_of_same_relations(self, paragraph_name):
        global component_objects_with_ground_truth_and_worker_annotated_relations

        # loop through all of this objects parts of same relations
        for parts_of_same_relation in self.worker_annotation_partsofsame:
            

            # get the supports and contradicts relations which are going into or out of the parts-of-same-component and who were made by the same worker
            supports_relations, contradicts_relations = component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name][parts_of_same_relation["component"]].get_supports_and_contradicts_worker_annotation_relations(parts_of_same_relation["assignment_id"])
            
            # add the found supports relation also to this component (as it part of the same argumentative statement)
            for relation in supports_relations:
                self.add_worker_annotation_relation(parts_of_same_relation["assignment_id"], paragraph_name, relation["component"], "supports")
            
            # add the found contradicts relation also to this component (as it part of the same argumentative statement)
            for relation in contradicts_relations:
                self.add_worker_annotation_relation(parts_of_same_relation["assignment_id"], paragraph_name, relation["component"], "contradicts")
            
            # now we also have to check for incoming supports relations of the component which is part of the same argumentative statement
            for k,v in component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name].items():
                # loop through all supports relations of this component
                for s_rel in v.worker_annotation_supports:
                    # check if this component supports the parts of same component
                    # the annotation must have been done by the same worker
                    if s_rel["component"] == parts_of_same_relation["component"] and s_rel["assignment_id"] == parts_of_same_relation["assignment_id"]:
                        # if yes, make sure that it also supports the other part of the argumentative statement
                        v.add_worker_annotation_relation(s_rel["assignment_id"], paragraph_name, (self.start, self.end), "supports")

    
    def get_supports_and_contradicts_ground_truth_relations(self):
        return self.ground_truth_supports, self.ground_truth_contradicts
    
    def adjust_object_for_ground_truth_parts_of_same_relations(self, paragraph_name):
        global component_objects_with_ground_truth_and_worker_annotated_relations

        # loop through all of this objects parts of same relations
        for parts_of_same_relation in self.ground_truth_partsofsame:
            

            # get the ground truth supports and contradicts relations which are going into or out of the parts-of-same-component
            supports_relations, contradicts_relations = component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name][parts_of_same_relation].get_supports_and_contradicts_ground_truth_relations()
            
            # add the found supports relation also to this component (as it part of the same argumentative statement)
            for relation in supports_relations:
                self.add_ground_truth_relation(paragraph_name, relation, "supports")
            
            # add the found contradicts relation also to this component (as it part of the same argumentative statement)
            for relation in contradicts_relations:
                self.add_ground_truth_relation(paragraph_name, relation, "contradicts")
            
            # now we also have to check for incoming supports relations of the component which is part of the same argumentative statement
            for k,v in component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name].items():
                # loop through all supports relations of this component
                for s_rel in v.ground_truth_supports:
                    # check if this component supports the parts of same component
                    if s_rel == parts_of_same_relation:
                        # if yes, make sure that it also supports the other part of the argumentative statement
                        v.add_ground_truth_relation(paragraph_name, (self.start, self.end), "supports")




def create_component_objects_for_paragraph(paragraph_name, components):
    global component_objects_with_ground_truth_and_worker_annotated_relations

    component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name] = {}


    for component_id, component_value in components.items():
        start = component_value["start"]
        end = component_value["end"]
        component_type = component_value["type"]
        text = component_value["text"]
        new_component = Component(paragraph_name, start, end, component_type, component_id, text)
        component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name][(start, end)] = new_component
        


def get_ground_truth_data():
    with open("/MasterThesis/Lauscher_Corpus/compiled_corpus/A11.ann") as f:
    #with open("/MasterThesis/Lauscher_Corpus/A11_edited.ann") as f:
        lines = f.readlines()
        ground_truth_components = {}
        ground_truth_relations = {}
        # filter out components to only consider argumentative relations
        #lines = [line for line in lines if line[0] == 'R']
        for l in lines:
            line = l.strip('\n')
            
            if line[0] == 'T':
                line_elements = line.split("\t")
                id_lauscher = line_elements[0]
                text_lauscher = line_elements[2]
                type_lauscher = line_elements[1].split(" ")[0]
                if type_lauscher == 'background_claim':
                    component_type = 'backgroundclaim'
                elif type_lauscher == 'own_claim':
                    component_type = 'ownclaim'
                elif type_lauscher == 'data':
                    component_type = 'data'
                start = int(line_elements[1].split(" ")[1])
                end = int(line_elements[1].split(" ")[2])
                
                ground_truth_components[id_lauscher]={
                    'type': component_type,
                    'start': start,
                    'end': end,
                    'text': text_lauscher
                    }

            elif line[0] == 'R':
                line_elements = line.split("\t")
                id_lauscher = line_elements[0]
                relation_type = line_elements[1].split(" ")[0]
                if relation_type == 'parts_of_same':
                    relation_type = 'partsofsame'
                
                arg1 = line_elements[1].split(" ")[1].split(":")[1]
                arg2 = line_elements[1].split(" ")[2].split(":")[1]
            
                ground_truth_relations[id_lauscher]={
                    'type': relation_type,
                    'arg1': ground_truth_components[arg1],
                    'arg2': ground_truth_components[arg2]
                    }

    return ground_truth_components, ground_truth_relations




def ground_truth_get_all_possible_relations_per_paragraph():
    global component_objects_with_ground_truth_and_worker_annotated_relations

    ground_truth_components, ground_truth_relations = get_ground_truth_data()
    
    all_paragraph_boundaries = {}

    # get the boundaries of all paragraphs
    preprocessing_json_filename = '/app/data/batch1/A11_ToBeAnnotated.json'
    with open(preprocessing_json_filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

        for p_name, p in all_paragraphs.items():
            all_paragraph_boundaries[p_name] = (p['start'], p['end'])


    # loop trough all paragraphs and for each paragraph create an object for each component which lies within this paragraph
    for p_name, p_boundaries in all_paragraph_boundaries.items():
        paragraph_start = p_boundaries[0]
        paragraph_end = p_boundaries[1]
        this_paragraphs_components = {key:value for key,value in ground_truth_components.items() if value["start"] >= paragraph_start and value["end"] <= paragraph_end}
        create_component_objects_for_paragraph(p_name, this_paragraphs_components)
        
        
        #this_paragraphs_relations = [ground_truth_relations]
    
        # now that an object exists for each component which lies within this paragraph, loop trough all relations which lie within this paragraph and update the objects so that they contain the ground truth relation data
        this_paragraphs_relations = {key:value for key,value in ground_truth_relations.items() if value["arg1"]["start"] >= paragraph_start and value["arg1"]["end"] <= paragraph_end and value["arg2"]["start"] >= paragraph_start and value["arg2"]["end"] <= paragraph_end}

        for relation_id, relation_value in this_paragraphs_relations.items():
            arg1 = (relation_value["arg1"]["start"], relation_value["arg1"]["end"])
            arg2 = (relation_value["arg2"]["start"], relation_value["arg2"]["end"])
            relation_type = relation_value["type"]
            #if p_name == 'paragraph_2':
            component_objects_with_ground_truth_and_worker_annotated_relations[p_name][arg1].add_ground_truth_relation(p_name, arg2, relation_type)





def get_all_worker_annotations(filepath, assignment_status_to_include_in_analysis):

    all_worker_annotations = {}

    all_paragraph_boundaries = {}
    filter_step1_results = {}

    # get the boundaries of all paragraphs
    preprocessing_json_filename = '/app/data/batch1/A11_ToBeAnnotated.json'
    with open(preprocessing_json_filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

        for p_name, p in all_paragraphs.items():
            all_paragraph_boundaries[p_name] = (p['start'], p['end'])

    # to load the worker answer from the saved txt file, load json in the following way:
    with open(filepath, "r") as f:
        all_answers = json.load(f)
        
        all_answers_included_in_analysis = [(x,y) for (x,y) in all_answers.items() if y["AssignmentStatus"] in assignment_status_to_include_in_analysis]
        
        #for assignment_id, answer in all_answers.items():
        
        for assignment_id, answer in all_answers_included_in_analysis:

            this_workers_annotations = {}

            paragraphs = (json.loads(answer['worker_answer']['submit_worker_assignment_data'])['paragraphs']).split(';')

            annotations = json.loads(answer['worker_answer']['submit_annotations'])
            this_workers_filter_step1_results = json.loads(answer['worker_answer']['submit_filter_data_step1'])
            filter_step1_results[assignment_id] = this_workers_filter_step1_results


            paragraph_counter = 0

            for key,p in annotations.items():
                paragraph = paragraphs[paragraph_counter]
                start = all_paragraphs[paragraph]['start']
                end = all_paragraphs[paragraph]['end']

                this_workers_annotations[paragraph] = []

                for key,a in p.items():
                    
                    this_workers_annotations[paragraph].append(a)

                paragraph_counter += 1
                

            all_worker_annotations[assignment_id] = this_workers_annotations
            
    return all_worker_annotations, filter_step1_results




create_hits_in_production = True

if create_hits_in_production:
    environment_name = 'production'
else:
    environment_name = 'sandbox'

# initialize all components per paragraph and then update components based on relation which lie within the same paragraph
ground_truth_get_all_possible_relations_per_paragraph()

filepath = os.path.join('MTurk', 'WorkerAnswers',environment_name,'relationAnnotation',filenames[0])
# loop trough all worker annotations and update components for all annotated paragraphs
all_worker_annotations, filter_step1_results = get_all_worker_annotations(filepath, assignment_status_to_include_in_analysis)

assignment_IDs_of_all_workers_who_participated_in_this_HIT = all_worker_annotations.keys()


# loop trough all the workers answers and update the global object list accordingly.
for assignment_id, worker_annotation in all_worker_annotations.items():
    for paragraph, annotations in worker_annotation.items():

        # loop through each annotation
        for anno in annotations:

            relation_type = anno[0]['relation_type']
            arg1_start = anno[4][0]
            arg1_end = anno[4][1]
            arg2_start = anno[5][0]
            arg2_end = anno[5][1]

            # add the relation to the source which lies as an object within the global list
            component_objects_with_ground_truth_and_worker_annotated_relations[paragraph][(arg1_start, arg1_end)].add_worker_annotation_relation(assignment_id, paragraph, (arg2_start, arg2_end), relation_type)


# adjust for parts of same relations
# loop through all paragraphs
for paragraph_name, paragraph_value in component_objects_with_ground_truth_and_worker_annotated_relations.items():
    # loop through all possible relations
    for relation_nodes, relation in paragraph_value.items():
        # adjust this object for all the containing parts of same relations
        component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name][relation_nodes].adjust_object_for_worker_annotation_parts_of_same_relations(paragraph_name)
        component_objects_with_ground_truth_and_worker_annotated_relations[paragraph_name][relation_nodes].adjust_object_for_ground_truth_parts_of_same_relations(paragraph_name)




data_prepared_for_aggregation = {}

annotated_paragraphs = ["paragraph_2", "paragraph_3", "paragraph_4"]
for paragraph_name, paragraph_value in component_objects_with_ground_truth_and_worker_annotated_relations.items():
    if paragraph_name in annotated_paragraphs:
        data_prepared_for_aggregation[paragraph_name] = {}
        combination_tuples_of_all_components = list(permutations(paragraph_value.keys(), 2))
        data_prepared_for_aggregation[paragraph_name]["permutations"] = combination_tuples_of_all_components
        data_prepared_for_aggregation[paragraph_name]["ground_truth"] = []
        data_prepared_for_aggregation[paragraph_name]["all_worker_annotations"] = []
        data_prepared_for_aggregation[paragraph_name]["worker_annotations_per_worker"] = {}



        for (source, target) in combination_tuples_of_all_components:
            

            # get the ground truth for this relation and append it to the list
            this_relations_ground_truth = paragraph_value[source].get_ground_truth_relation(target)
            this_source_target_combination_is_checked_for_the_second_time = combination_tuples_of_all_components.index((source,target)) > combination_tuples_of_all_components.index((target,source))
            
            # first, check if this is a symmetric relation which has already been added to the list before [i.e. the same relation but with the opposite direction].
            if this_relations_ground_truth in ["contradicts", "partsofsame"] and this_source_target_combination_is_checked_for_the_second_time:
                # If yes, add 'none' to make sure that symmetric relations are no counted twice.
                this_relations_ground_truth = "none"
            
            # second, check if this is a relation which has already been counted by a component which is part of the same argumentative statement
            for comp, comp_value in paragraph_value.items():
                if source in comp_value.ground_truth_partsofsame and comp != target:
                    # the source of this relation is part of same component as comp
                    if combination_tuples_of_all_components.index((source,target)) > combination_tuples_of_all_components.index((comp,target)):
                        # this relation has already been counted when the other part of the same component's was checked
                        this_relations_ground_truth = "none"
                if target in comp_value.ground_truth_partsofsame and comp != source:
                    # the target of this relation is part of same component as comp
                    if combination_tuples_of_all_components.index((source,target)) > combination_tuples_of_all_components.index((source,comp)):
                        # this relation has already been counted when the other part of the same component's was checked
                        this_relations_ground_truth = "none"

            data_prepared_for_aggregation[paragraph_name]["ground_truth"].append(this_relations_ground_truth)

            # get the worker annotations for this relation and append it to the list
            this_relations_worker_annotations = []
            #loop through the assignment_IDs of all workers who participated in this HIT
            for assignment_id in assignment_IDs_of_all_workers_who_participated_in_this_HIT:
                # get this workers annotation for the relation between those two components
                this_workers_annotation = paragraph_value[source].get_worker_annotation_relation(assignment_id, target)
                
                
                # first, check if this is a symmetric relation which has already been added to the list before [i.e. the same relation but with the opposite direction].
                if this_workers_annotation in ["contradicts", "partsofsame"] and this_source_target_combination_is_checked_for_the_second_time:
                    # If yes, add 'none' to make sure that symmetric relations are no counted twice.
                    this_workers_annotation = "none"

                # second, check if this is a relation which has already been counted by a component which is part of the same argumentative statement
                for comp, comp_value in paragraph_value.items():
                    if {'assignment_id': assignment_id, 'component': source} in comp_value.worker_annotation_partsofsame and comp != target:
                        # the source of this relation is part of same component as comp
                        if combination_tuples_of_all_components.index((source,target)) > combination_tuples_of_all_components.index((comp,target)):
                            # this relation has already been counted when the other part of the same component's was checked
                            this_workers_annotation = "none"
                    if {'assignment_id': assignment_id, 'component': target} in comp_value.worker_annotation_partsofsame and comp != source:
                        # the target of this relation is part of same component as comp
                        if combination_tuples_of_all_components.index((source,target)) > combination_tuples_of_all_components.index((source,comp)):
                            # this relation has already been counted when the other part of the same component's was checked
                            this_workers_annotation = "none"


                this_relations_worker_annotations.append(this_workers_annotation)

                if assignment_id not in data_prepared_for_aggregation[paragraph_name]["worker_annotations_per_worker"]:
                    data_prepared_for_aggregation[paragraph_name]["worker_annotations_per_worker"][assignment_id] = []

                data_prepared_for_aggregation[paragraph_name]["worker_annotations_per_worker"][assignment_id].append(this_workers_annotation)

            # now append the annotations of all workers for this relation to the list
            data_prepared_for_aggregation[paragraph_name]["all_worker_annotations"].append(this_relations_worker_annotations)
            



def get_list_for_f1_calculation(permutations, ground_truth, annotations):

    ground_truth_shortened = []
    worker_annotations_shortened = []


    for i in range(len(ground_truth)):
        # check if either ground truth of any of the worker annotations is not 'none'
        if ground_truth[i] != 'none' or annotations[i] != 'none':
            ground_truth_shortened.append(ground_truth[i])
            worker_annotations_shortened.append(annotations[i])


    # for f1_nodes we do not need to shorten the lists because in the binary case true negatives are not considered anyway
    ground_truth_without_type = []


    for i, gt_relation_type in enumerate(ground_truth):
        source, target = permutations[i]

        # check if the reverse of this relation is 'none'
        index_of_reverse_relation = permutations.index((target, source))
        reverse_of_gt_relation_type = ground_truth[index_of_reverse_relation]

        # only if relation is really 'none' in both directions, add 0
        if gt_relation_type == 'none' and reverse_of_gt_relation_type == 'none':
            ground_truth_without_type.append(0)
        else:
            ground_truth_without_type.append(1)

    worker_annotation_without_type = []

    for i, worker_relation_type in enumerate(annotations):
        source, target = permutations[i]

        # check if the reverse of this relation is 'none'
        index_of_reverse_relation = permutations.index((target, source))
        reverse_of_worker_relation_type = annotations[index_of_reverse_relation]

        # only if relation is really 'none' in both directions, add 0
        if worker_relation_type == 'none' and reverse_of_worker_relation_type == 'none':
            worker_annotation_without_type.append(0)
        else:
            worker_annotation_without_type.append(1)

    return ground_truth_shortened, worker_annotations_shortened, ground_truth_without_type, worker_annotation_without_type


def calculate_weighted_f1(gt_shortened, worker_shortened, gt_without_type, worker_without_type):
    f1_nodes_and_types = f1_score(gt_shortened, worker_shortened,average='micro')
    f1_nodes = f1_score(gt_without_type, worker_without_type) # we only care about nodes, not about annotation types
    f1_TOTAL = (f1_nodes + 2 * f1_nodes_and_types) / 3 # the weighted f1 score

    return f1_nodes_and_types, f1_nodes, f1_TOTAL



def get_worker_answer_aggregation_combinations(workers, combination_size):
    if len(workers) < combination_size:
        return [tuple(workers)]
    else:
        return list(combinations(workers, combination_size))



def performance_analysis_H1a(filter_step1_results, data_prepared_for_aggregation):

    # filter is passed only if all 3 answers are correct
    workers_who_passed_filter = list({k:v for (k,v) in filter_step1_results.items() if v["filterPassed"] == True}.keys())
    workers_who_failed_filter = list({k:v for (k,v) in filter_step1_results.items() if v["filterPassed"] == False}.keys())

    # filter is passed if at least 2 answers are correct
    #workers_who_passed_filter = list({k:v for (k,v) in filter_step1_results.items() if len(v["correct_answers"]) >= 2}.keys())
    #workers_who_failed_filter = list({k:v for (k,v) in filter_step1_results.items() if len(v["correct_answers"]) < 2}.keys())

    f1_scores_of_mace_aggregated_datapoints_by_paragraph = {"filter_passed": {}, "filter_failed": {}}

    for paragraph_name, paragraph_value in data_prepared_for_aggregation.items():
        # loop trough all answers by all workers
        ground_truth = paragraph_value["ground_truth"]

        combination_size = 3

        # calculate f1 scores for aggregation combinations of those workers who PASSED filter
        worker_combinations = get_worker_answer_aggregation_combinations(workers_who_passed_filter, combination_size)

        for combination in worker_combinations:
            
            # select answers from those worker answers who are present in the current combination
            all_worker_answers = list(zip(*[paragraph_value["worker_annotations_per_worker"][assignment_id] for assignment_id in combination]))

            # aggregate worker answers with MACE
            aggregated_worker_answers = aggregate_worker_answers_with_MACE(all_worker_answers)


            # prepare the data do have in the correct format to calculate weighted f1
            # namely, two lists: '...shortend' in which TN were filtered out and: '...without_type' where we only consider node but not type of relation
            ground_truth_shortened, worker_annotations_shortened, ground_truth_without_type, worker_annotation_without_type = get_list_for_f1_calculation(paragraph_value['permutations'], ground_truth, aggregated_worker_answers)
            
            # calculate f1 scores micro (true: ground_truth, pred: worker answers aggregated with MACE)
            f1_nodes_and_types, f1_nodes, f1_TOTAL = calculate_weighted_f1(ground_truth_shortened, worker_annotations_shortened, ground_truth_without_type, worker_annotation_without_type)


            if paragraph_name not in f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_passed"].keys():
                f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_passed"][paragraph_name] = []
            # add calculated f1_score to list
            f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_passed"][paragraph_name].append(f1_TOTAL)



        # calculate f1 scores for aggregation combinations of those workers who FAILED filter
        worker_combinations = get_worker_answer_aggregation_combinations(workers_who_failed_filter, combination_size)


        for combination in worker_combinations:
            
            # select answers from those worker answers who are present in the current combination
            all_worker_answers = list(zip(*[paragraph_value["worker_annotations_per_worker"][assignment_id] for assignment_id in combination]))

            # aggregate worker answers with MACE
            aggregated_worker_answers = aggregate_worker_answers_with_MACE(all_worker_answers)


            # prepare the data do have in the correct format to calculate weighted f1
            # namely, two lists: '...shortend' in which TN were filtered out and: '...without_type' where we only consider node but not type of relation
            ground_truth_shortened, worker_annotations_shortened, ground_truth_without_type, worker_annotation_without_type = get_list_for_f1_calculation(paragraph_value['permutations'], ground_truth, aggregated_worker_answers)
            
            # calculate f1 scores micro (true: ground_truth, pred: worker answers aggregated with MACE)
            f1_nodes_and_types, f1_nodes, f1_TOTAL = calculate_weighted_f1(ground_truth_shortened, worker_annotations_shortened, ground_truth_without_type, worker_annotation_without_type)


            if paragraph_name not in f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_failed"].keys():
                f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_failed"][paragraph_name] = []
            # add calculated f1_score to list
            f1_scores_of_mace_aggregated_datapoints_by_paragraph["filter_failed"][paragraph_name].append(f1_TOTAL)

    
    print("Create CSV file for 2 sample t-test in R")

    csv_filename = 'H1a_scores_relations.csv'

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


performance_analysis_H1a(filter_step1_results, data_prepared_for_aggregation)
