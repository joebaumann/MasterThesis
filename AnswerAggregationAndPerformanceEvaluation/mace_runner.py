import os
from subprocess import Popen, PIPE, STDOUT
import csv

def aggregate_worker_answers_with_MACE(all_worker_answers, workers=None):
    aggregated_worker_answers = []


    # create csv file for worker answer data
    with open('worker_answers_to_be_aggregated.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(all_worker_answers)


    # run MACE with the created csv files
    p = Popen(['java', '-jar', 'MACE/MACE.jar', 'worker_answers_to_be_aggregated.csv'], stdout=PIPE, stderr=STDOUT)
    mace_terminal_output = p.communicate()[0] # wait until finished and catch all output
    with open('prediction', newline='') as f:
        reader = csv.reader(f)
        aggregated_worker_answers = [x[0] for x in list(reader)]
    
    if workers is not None:
        competences = []
        with open('competence', newline='') as f:
            data = csv.reader(f, delimiter = '\t')
            #print(list(data)[0])
            competences = dict(zip(workers, list(data)[0]))
    
    # delete all files which were created for aggregation with MACE
    os.remove("worker_answers_to_be_aggregated.csv")
    os.remove("prediction")
    os.remove("competence")

    if workers is None:
        return aggregated_worker_answers
    else:
        return aggregated_worker_answers, competences
