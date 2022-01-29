import json
import os
from itertools import permutations


from mace_runner import aggregate_worker_answers_with_MACE


def getAggregatedAnnotationsForFilepath(filepath, assignment_status_to_include_in_analysis):
    all_annotations = {}
    all_annotations_statistics = {}
    filter_step2_results = {}

    all_workers = []


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

            if assignment_id not in all_workers:
                all_workers.append(assignment_id)

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
                        
                        this_paragraphs_tokens[token_id] = {
                            "paragraph": paragraph,
                            "token_id": token_id,
                            "token_text": token_val['token'],
                            "token_start": token_val['start'],
                            "token_end": token_val['end'],
                            "worker_annotations": []
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
                            #print("~~~ ", worker_annotation_token_id)
                            this_paragraphs_tokens[str(worker_annotation_token_id)]['worker_annotations'][-1] = (AssignmentId, annotation_type)
                    

                paragraph_counter += 1
                all_annotations[paragraph] = this_paragraphs_tokens
                all_annotations_statistics[paragraph] = this_paragraphs_statistics


    return all_annotations, all_annotations_statistics, filter_step2_results, all_workers



print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("~~~~~~~~~ performances of aggregated worker answers (with MACE) per paragraph ~~~~~~~~~")
print(">>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<")
print("")
print("")


def aggregate_component_annotations_with_MACE(filter_step2_results, combined_component_annotations, all_workers):

    # loop trough all answers by all workers
    for paragraph_name, paragraph_value in combined_component_annotations.items():

        # aggregate annotations of all workers
        all_worker_answers = []
        for token_id, token_value in paragraph_value.items():
            this_tokens_worker_answers = []
            # select annotations
            this_tokens_worker_answers = [annotation for assignment_id, annotation in token_value["worker_annotations"]]
            all_worker_answers.append(this_tokens_worker_answers)
        
        # aggregate worker answers with MACE
        aggregated_worker_answers, competences = aggregate_worker_answers_with_MACE(all_worker_answers, workers=all_workers)
        for token_id, token_value in combined_component_annotations[paragraph_name].items():
            token_value['final_annotation'] = aggregated_worker_answers[int(token_id)]

    return combined_component_annotations, competences




component_objects_with_worker_annotated_relations = {}


class Component:
    def __init__(self, paragraph_name, start, end, component_type, component_id, text):
        self.paragraph_name = paragraph_name
        self.start = start
        self.end = end
        self.component_type = component_type
        self.component_id = component_id
        self.text = text

        self.worker_annotation_supports = []
        self.worker_annotation_contradicts = []
        self.worker_annotation_partsofsame = []


    def __str__(self):
        return 'Component(paragraph_name='+self.paragraph_name+', start='+str(self.start)+', end='+str(self.end)+', component_type='+self.component_type+', component_id='+self.component_id+', text='+str(self.text)+', worker_annotation_supports='+str(self.worker_annotation_supports)+', worker_annotation_contradicts='+str(self.worker_annotation_contradicts)+', worker_annotation_partsofsame='+str(self.worker_annotation_partsofsame) + ')'
    

    def add_worker_annotation_relation(self, assignment_id, paragraph_name, component, relation_type):
        global component_objects_with_worker_annotated_relations

        #print("(", self.start, self.end, ")", relation_type, component)

        # depending on which type the relation is, add the component to the list
        if relation_type == 'supports':
            # self-component supports component
            # supports relation is not symmetric
            self.worker_annotation_supports.append({"assignment_id": assignment_id, "component": component})
        elif relation_type == 'contradicts':
            # self-component contradicts component
            self.worker_annotation_contradicts.append({"assignment_id": assignment_id, "component": component})
            # this means that component also supports self-component
            component_objects_with_worker_annotated_relations[paragraph_name][component].add_worker_annotation_symmetric_relation(assignment_id, paragraph_name, (self.start, self.end), relation_type)
        elif relation_type == 'partsofsame':
            # self-component partsofsame component
            self.worker_annotation_partsofsame.append({"assignment_id": assignment_id, "component": component})
            # this means that component also supports self-component
            component_objects_with_worker_annotated_relations[paragraph_name][component].add_worker_annotation_symmetric_relation(assignment_id, paragraph_name, (self.start, self.end), relation_type)
    
    def add_worker_annotation_symmetric_relation(self, assignment_id, paragraph, component, relation_type):
        # depending on which type the relation is, add the component to the list
        if relation_type == 'contradicts':
            self.worker_annotation_contradicts.append({"assignment_id": assignment_id, "component": component})
        elif relation_type == 'partsofsame':
            #self-component partsofsame component
            self.worker_annotation_partsofsame.append({"assignment_id": assignment_id, "component": component})


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
        global component_objects_with_worker_annotated_relations

        # loop through all of this objects parts of same relations
        for parts_of_same_relation in self.worker_annotation_partsofsame:
            

            # get the supports and contradicts relations which are going into or out of the parts-of-same-component and who were made by the same worker
            supports_relations, contradicts_relations = component_objects_with_worker_annotated_relations[paragraph_name][parts_of_same_relation["component"]].get_supports_and_contradicts_worker_annotation_relations(parts_of_same_relation["assignment_id"])
            
            # add the found supports relation also to this component (as it part of the same argumentative statement)
            for relation in supports_relations:
                self.add_worker_annotation_relation(parts_of_same_relation["assignment_id"], paragraph_name, relation["component"], "supports")
                print("x")
            
            # add the found contradicts relation also to this component (as it part of the same argumentative statement)
            for relation in contradicts_relations:
                self.add_worker_annotation_relation(parts_of_same_relation["assignment_id"], paragraph_name, relation["component"], "contradicts")
                print("y")
            
            # now we also have to check for incoming supports relations of the component which is part of the same argumentative statement
            for k,v in component_objects_with_worker_annotated_relations[paragraph_name].items():
                # loop through all supports relations of this component
                for s_rel in v.worker_annotation_supports:
                    # check if this component supports the parts of same component
                    # the annotation must have been done by the same worker
                    if s_rel["component"] == parts_of_same_relation["component"] and s_rel["assignment_id"] == parts_of_same_relation["assignment_id"]:
                        # if yes, make sure that it also supports the other part of the argumentative statement
                        v.add_worker_annotation_relation(s_rel["assignment_id"], paragraph_name, (self.start, self.end), "supports")


def create_component_objects_for_paragraph(paragraph_name, components):
    global component_objects_with_worker_annotated_relations

    component_objects_with_worker_annotated_relations[paragraph_name] = {}

    #print("create objects for: ", paragraph_name)

    for component_id, component_value in components.items():
        start = component_value["start"]
        end = component_value["end"]
        component_type = component_value["type"]
        text = component_value["text"]
        new_component = Component(paragraph_name, start, end, component_type, component_id, text)
        #if paragraph_name == 'paragraph_2':
            #print("adding new component:", new_component)
        component_objects_with_worker_annotated_relations[paragraph_name][(start, end)] = new_component
        


def get_underlying_components(filepath_for_underlying_components):
    with open(filepath_for_underlying_components) as f:
        lines = f.readlines()
        underlying_components = {}
        # filter out components to only consider argumentative relations
        #lines = [line for line in lines if line[0] == 'R']
        for l in lines:
            line = l.strip('\n')
            
            if line[0] == 'T':
                line_elements = line.split("\t")
                #print("--", line_elements)
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
                
                underlying_components[id_lauscher]={
                    'type': component_type,
                    'start': start,
                    'end': end,
                    'text': text_lauscher
                    }


    return underlying_components




def get_all_possible_relations_per_paragraph(preprocessing_json_filename, filepath_for_underlying_components):
    global component_objects_with_worker_annotated_relations

    underlying_components = get_underlying_components(filepath_for_underlying_components)
    
    all_paragraph_boundaries = {}

    # get the boundaries of all paragraphs
    
    with open(preprocessing_json_filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

        for p_name, p in all_paragraphs.items():
            #print("p:")
            #print(type(p))
            #print(p)
            all_paragraph_boundaries[p_name] = (p['start'], p['end'])


    # loop trough all paragraphs and for each paragraph create an object for each component which lies within this paragraph
    for p_name, p_boundaries in all_paragraph_boundaries.items():
        paragraph_start = p_boundaries[0]
        paragraph_end = p_boundaries[1]
        this_paragraphs_components = {key:value for key,value in underlying_components.items() if value["start"] >= paragraph_start and value["end"] <= paragraph_end}
        create_component_objects_for_paragraph(p_name, this_paragraphs_components)
        
        

    return underlying_components
    






def get_all_worker_annotations(filepath, assignment_status_to_include_in_analysis):

    all_worker_annotations = {}

    all_paragraph_boundaries = {}
    filter_step2_results = {}
    all_workers = []

    # get the boundaries of all paragraphs
    preprocessing_json_filename = '/app/data/batch1/A11_ToBeAnnotated.json'
    with open(preprocessing_json_filename) as f:
        all_paragraphs = json.load(f)["text_to_annotate"]

        for p_name, p in all_paragraphs.items():
            #print("p:")
            #print(type(p))
            #print(p)
            all_paragraph_boundaries[p_name] = (p['start'], p['end'])

    # to load the worker answer from the saved txt file, load json in the following way:
    with open(filepath, "r") as f:
        all_answers = json.load(f)
        
        all_answers_included_in_analysis = [(x,y) for (x,y) in all_answers.items() if y["AssignmentStatus"] in assignment_status_to_include_in_analysis]
        
        #for assignment_id, answer in all_answers.items():
        
        for assignment_id, answer in all_answers_included_in_analysis:

            this_workers_annotations = {}

            paragraphs = (json.loads(answer['worker_answer']['submit_worker_assignment_data'])['paragraphs']).split(';')
            #print(paragraphs)
            #print("")

            annotations = json.loads(answer['worker_answer']['submit_annotations'])
            this_workers_filter_step2_results = json.loads(answer['worker_answer']['submit_filter_data_step2'])
            filter_step2_results[assignment_id] = this_workers_filter_step2_results

            if assignment_id not in all_workers:
                all_workers.append(assignment_id)

            paragraph_counter = 0

            for key,p in annotations.items():
                paragraph = paragraphs[paragraph_counter]
                start = all_paragraphs[paragraph]['start']
                end = all_paragraphs[paragraph]['end']
                #print("paragraph", paragraph)
                #print("start", start)
                #print("end", end)

                this_workers_annotations[paragraph] = []

                for key,a in p.items():
                    
                    this_workers_annotations[paragraph].append(a)

                paragraph_counter += 1
                

            all_worker_annotations[assignment_id] = this_workers_annotations
            
    return all_worker_annotations, filter_step2_results, all_workers, paragraphs





def get_data_prepared_for_aggregation(all_worker_annotations):
    global component_objects_with_worker_annotated_relations

    # loop trough all the workers answers and update the global object list accordingly.
    for assignment_id, worker_annotation in all_worker_annotations.items():
        for paragraph, annotations in worker_annotation.items():
            #print("")
            #print("paragraph:", paragraph, "assignment_id:", assignment_id)
            #print("annotations:", annotations)

            # loop through each annotation
            for anno in annotations:

                relation_type = anno[0]['relation_type']
                arg1_start = anno[4][0]
                arg1_end = anno[4][1]
                arg2_start = anno[5][0]
                arg2_end = anno[5][1]

                # add the relation to the source which lies as an object within the global list
                component_objects_with_worker_annotated_relations[paragraph][(arg1_start, arg1_end)].add_worker_annotation_relation(assignment_id, paragraph, (arg2_start, arg2_end), relation_type)




    # adjust for parts of same relations
    # loop through all paragraphs
    for paragraph_name, paragraph_value in component_objects_with_worker_annotated_relations.items():
        # loop through all possible relations
        for relation_nodes, relation in paragraph_value.items():
            # adjust this object for all the containing parts of same relations
            component_objects_with_worker_annotated_relations[paragraph_name][relation_nodes].adjust_object_for_worker_annotation_parts_of_same_relations(paragraph_name)



    data_prepared_for_aggregation = {}

    for paragraph_name, paragraph_value in component_objects_with_worker_annotated_relations.items():
        if paragraph_name in paragraphs:
            data_prepared_for_aggregation[paragraph_name] = {}
            combination_tuples_of_all_components = list(permutations(paragraph_value.keys(), 2))
            data_prepared_for_aggregation[paragraph_name]["permutations"] = combination_tuples_of_all_components
            data_prepared_for_aggregation[paragraph_name]["all_worker_annotations"] = []
            data_prepared_for_aggregation[paragraph_name]["worker_annotations_per_worker"] = {}

            print("  number of components:", len(paragraph_value.keys()))
            print("  number of possible permutations:", len(combination_tuples_of_all_components))
            #print("  permutations:", combination_tuples_of_all_components)


            for (source, target) in combination_tuples_of_all_components:
                
                this_source_target_combination_is_checked_for_the_second_time = combination_tuples_of_all_components.index((source,target)) > combination_tuples_of_all_components.index((target,source))

                # get the worker annotations for this relation and append it to the list
                this_relations_worker_annotations = []
                #loop through the assignment_IDs of all workers who participated in this HIT
                for assignment_id in assignment_IDs_of_all_workers_who_participated_in_this_HIT:
                    # get this workers annotation for the relation between those two components
                    this_workers_annotation = paragraph_value[source].get_worker_annotation_relation(assignment_id, target)
                    
                    #print(assignment_id, "--", this_workers_annotation)
                    
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
                
    return data_prepared_for_aggregation





def aggregate_relation_annotations_with_MACE(filter_step2_results, data_prepared_for_aggregation, all_workers):


    for paragraph_name, paragraph_value in data_prepared_for_aggregation.items():
        # loop trough all answers by all workers


        # select answers from all workers
        all_worker_answers = list(zip(*[paragraph_value["worker_annotations_per_worker"][assignment_id] for assignment_id in all_workers]))

        # aggregate worker answers with MACE
        aggregated_worker_answers, competences = aggregate_worker_answers_with_MACE(all_worker_answers, workers=all_workers)

        # add aggregated solution to dict
        data_prepared_for_aggregation[paragraph_name]["final_annotation"] = aggregated_worker_answers


    return data_prepared_for_aggregation, competences









# Provide the path to the unannotated scientific paper
paper_path = "/MasterThesis/Lauscher_Corpus/compiled_corpus/A11.txt"

# load the entire paper to then be able to get the text of an annotation
with open(paper_path) as paper:
    entire_paper = paper.read()

# Then, define the filenames to include

filename = 'H1b_worker_answers_test.txt' # H1b
# choose which assignment status should be considered for the analysis: 'Submitted'|'Approved'|'Rejected'
assignment_status_to_include_in_analysis = ['Submitted', 'Approved', 'Rejected']
create_hits_in_production = True
if create_hits_in_production:
    environment_name = 'production'
else:
    environment_name = 'sandbox'


###### COMPONENT AGGREGATION ######

# aggregate  component annotations
filepath = os.path.join('MTurk', 'WorkerAnswers',environment_name,'componentAnnotation',filename)
combined_component_annotations, all_annotations_statistics, filter_step2_results, all_workers = getAggregatedAnnotationsForFilepath(filepath, assignment_status_to_include_in_analysis)
aggregated_component_data, component_competences = aggregate_component_annotations_with_MACE(filter_step2_results, combined_component_annotations, all_workers)

print("MACE reported the following competences for the workers who participated in this argument component annotation HIT (assignment_id: competence):", component_competences)


component_id_counter = 1

token_start = None
token_end = None
previous_token_annotation = 'none'

with open(os.path.join('AnswerAggregationAndPerformanceEvaluation', 'annotated_scientific_paper_components.ann'), 'w') as file:
    for paragraph, tokens in aggregated_component_data.items():
        for token_id, token_value in tokens.items():
            if token_value["final_annotation"] != previous_token_annotation:
                # token is different to previous one
                if previous_token_annotation != 'none':
                    # previous token was the end of an annotated span, therefore,write it to file
                    content = entire_paper[token_start:token_end]
                    if previous_token_annotation== 'ownclaim': final_type = 'own_claim'
                    elif previous_token_annotation== 'backgroundclaim': final_type = 'background_claim'
                    else: final_type = 'data'
                    file.write("T"+str(component_id_counter)+"\t"+final_type+" "+str(token_start)+" "+str(token_end)+"\t"+content+"\n")
                    component_id_counter +=1
                
                if token_value["final_annotation"] != 'none':
                    # this is the start of an annotated span
                    token_start = token_value["token_start"]
                previous_token_annotation = token_value["final_annotation"]
                    
            token_end = token_value["token_end"]





###### RELATION AGGREGATION ######

# specify the filename for the underlying components
# Actually, this should be specified as: filepath_for_underlying_components = os.path.join('AnswerAggregationAndPerformanceEvaluation', 'annotated_scientific_paper_components.ann')
# However, for our experiments, we have been using the ground truth components (from Lauscher et al. (2018)) as the underlying argument components for the argumentative relation annotation task. For this reason, also now we have to use these components.
filepath_for_underlying_components = "/MasterThesis/Lauscher_Corpus/compiled_corpus/A11.ann"

preprocessing_json_filename = '/app/data/batch1/A11_ToBeAnnotated.json'

# initialize all components per paragraph and then update components based on relation which lie within the same paragraph
underlying_components = get_all_possible_relations_per_paragraph(preprocessing_json_filename, filepath_for_underlying_components)

filepath = os.path.join('MTurk', 'WorkerAnswers',environment_name,'relationAnnotation',filename)
# loop trough all worker annotations and update components for all annotated paragraphs
all_worker_annotations, filter_step2_results, all_workers, paragraphs = get_all_worker_annotations(filepath, assignment_status_to_include_in_analysis)

assignment_IDs_of_all_workers_who_participated_in_this_HIT = all_worker_annotations.keys()

data_prepared_for_aggregation = get_data_prepared_for_aggregation(all_worker_annotations)



combined_relation_annotations, relation_competences = aggregate_relation_annotations_with_MACE(filter_step2_results, data_prepared_for_aggregation, all_workers)

print("MACE reported the following competences for the workers who participated in this argumentative relation annotation HIT (assignment_id: competence):", relation_competences)



relation_id_counter = 1

with open(os.path.join('AnswerAggregationAndPerformanceEvaluation', 'annotated_scientific_paper_relations.ann'), 'w') as file:
    # go through all the relations and write them to the file
    for paragraph, relations in combined_relation_annotations.items():
        for i, relation_type in enumerate(relations["final_annotation"]):
            if relation_type != 'none':
                source, target = relations["permutations"][i]

                for component_id, component_value in underlying_components.items():
                    if component_value["start"] == source[0] or component_value["end"] == source[1]:
                        source_id = component_id
                    
                    if component_value["start"] == target[0] or component_value["end"] == target[1]:
                        target_id = component_id
                    
                if relation_type== 'partsofsame': final_type = 'parts_of_same'
                else: final_type = relation_type
                file.write("R"+str(relation_id_counter)+"\t"+final_type+" Arg1:" + source_id + " Arg2:" + target_id +"\n")
                

                relation_id_counter +=1
