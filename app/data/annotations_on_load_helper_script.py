"""
This is a helper script to retrieve annotated argument components from Lauscher's corpus
These components are printed to the terminal and can then be copied to the file 'annotations_on_load_for_relation_HITs.py'.
In this way, we can make sure that the correct argument components are displayed for each paragraph during the argumentative relation annotation task.
As these argument components need to be displayed in the annotation tool's paragraph as soon as the page is loaded, we call them 'annotations_on_load'.
"""

# %%

# define annotations for 3 paragraphs
annotations = [[], [], []]

# define start and end of paragraphs
#paragraphs = [(5731, 7259), (7260, 8590), (8591, 9974)] # paragraphs 2-4
paragraphs = [(25474, 26860), (26861, 28329), (28330, 29478)] # paragraphs 16-18


with open("/MasterThesis/Lauscher_Corpus/compiled_corpus/A11.ann") as f:
    lines = f.readlines()
    counter = 0
    # filter out relations to only consider argument components
    lines = [line for line in lines if line[0] == 'T']
    for line in lines:
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

        paragraph_counter = 0
        for p_start, p_end in paragraphs:
            #print("")
            #print("p_start: ", p_start)
            #print("p_end: ", p_end)
            #print("")

            if start >= p_start and start <= p_end:
                # start of lauscher annotation lies within this paragraphs boundaries
                if end <= p_end:
                    # end of lauscher annotation lies within this paragraphs boundaries
                    annotation = [-1, -1, type, -1, '', [], start, end]
                else:
                    # end of lauscher annotation lies OUTSIDE od this paragraphs boundaries
                    annotation = [-1, -1, type, -1, '', [], start, p_end]

                
                annotations[paragraph_counter].append(annotation)
            
            paragraph_counter += 1
        
        if counter > 10:
            #break
            pass
        counter += 1

print("--- Annotated components per paragraph:")
for x in annotations:
    print("")
    print("Number of annotated components in this paragraph:", len(x))
    print(x)
    print("")
print("")
print("--- ALL ANNOTATIONS: ---")
print(annotations)

