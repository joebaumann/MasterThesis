"""config file"""

# This is the app name as specified on Heroku.
# It is needed so that a newly created HIT can successfully access the annotation task on Heroku.
APP_NAME = 'masterthesisjb'

# At least one user is needed to be able to log in to the admin area.
# Pay attention, this is the admin area login, not the MTurk login.
# The MTurk login is not deployed to Heroku. Please login with your AWS access key directly in the admin area to make use of all admin area functionalities.
USERS = [
    {'id': 1, 'username': 'admin', 'password': 'd)m¡8%3/0bMG%}M(hB*C'},
]

# Define all those tokens which cannot be annotated to help annotators to annotate the text conforming to the instructions.
# Forbidden tokens are timmed in case they are at the beginning or the end of a selection.
# Hence, it is not possible to select just one forbidden tokens.
# Keep in mind that even if these forbidden tokens help, but they are not sufficient to prevent crowdworkers from annotating nonsense.
forbidden_tokens = {
    'my_forbidden_tokens': ['.', ',', ':', ';', "'", "’", '`', '(', ')', '{', '}', '[', ']', '<', '>', '/', '^', '-', '–']
}

# Specify list of annotation buttons for annotation tasks: [<className>, <displayName>, <color>]
# The "arguments" are used for the argument component annotation task as well as for the argumentative relation annotation task.
annotation_types = {
    "arguments": [['ownclaim', 'Own Claim', 'rgb(255, 51, 51)'], ['backgroundclaim', 'Background Claim', 'rgb(32, 156, 238)'], ['data', 'Data', 'rgb(51, 51, 51)']],
    "hypothesis": [['hypothesis', 'Hypothesis', 'rgb(85, 111, 191)']],
}

# Specify list of annotation buttons for relation tasks: [<className>, <displayName>, <color>]
relation_types = {
    "relations_1": [['supports', 'Supports', 'rgb(244, 177, 131, 0.7)'], ['contradicts', 'Contradicts', 'rgb(255, 217, 102, 0.7)'], ['partsofsame', 'Parts of Same', 'rgb(169, 209, 142, 0.7)']],

}

# define all specification of a batch
# currently available hit_types: 'arguments' , 'relations'
batches = {
    'batch1_argumentComponents': {
        'hit_type': 'arguments',
        'batch_directory_name': 'batch1',
        'textToAnnotate_filename': 'A11_ToBeAnnotated.json',
        'forbidden_tokens': 'my_forbidden_tokens',
        'annotation_types': 'arguments',
    },
    'batch1_argumentRelations': {
        'hit_type': 'relations',
        'batch_directory_name': 'batch1',
        'textToAnnotate_filename': 'A11_ToBeAnnotated.json',
        'annotations_on_load': 'lauscher_annotations_paragraphs_2_4',
        'annotation_types': 'arguments',
        'relation_types': 'relations_1',
    },
    'batch1_argumentRelations_16_18': {
        'hit_type': 'relations',
        'batch_directory_name': 'batch1',
        'textToAnnotate_filename': 'A11_ToBeAnnotated.json',
        'annotations_on_load': 'lauscher_annotations_paragraphs_16_18',
        'annotation_types': 'arguments',
        'relation_types': 'relations_1',
    },
    'batch2_argumentComponents_filterStep1': {
        'hit_type': 'arguments_filterStep1',
        'batch_directory_name': 'batch1',
        'textToAnnotate_filename': 'A11_ToBeAnnotated.json',
        'forbidden_tokens': 'my_forbidden_tokens',
        'annotation_types': 'arguments',
    },
    'batch2_argumentRelations_filterStep1': {
        'hit_type': 'relations_filterStep1',
        'batch_directory_name': 'batch1',
        'textToAnnotate_filename': 'A11_ToBeAnnotated.json',
        'annotations_on_load': 'lauscher_annotations_paragraphs_2_4',
        'annotation_types': 'arguments',
        'relation_types': 'relations_1',
    },
    'batch3_argumentComponents_filterStep2': {
        'hit_type': 'arguments_filterStep2',
        'batch_directory_name': 'batch1',
        'textToAnnotate_filename': 'A11_ToBeAnnotated.json',
        'forbidden_tokens': 'my_forbidden_tokens',
        'annotation_types': 'arguments',
        'filter_attempts_before_revealing_solution': 10,
    },
    'batch3_argumentRelations_filterStep2': {
        'hit_type': 'relations_filterStep2',
        'batch_directory_name': 'batch1',
        'textToAnnotate_filename': 'A11_ToBeAnnotated.json',
        'annotations_on_load': 'lauscher_annotations_paragraphs_2_4',
        'annotation_types': 'arguments',
        'relation_types': 'relations_1',
        'filter_attempts_before_revealing_solution': 8,
    },

    'batch0_argumentComponents_final': {
        'hit_type': 'arguments_final',
        'batch_directory_name': 'batch1',
        'textToAnnotate_filename': 'A11_ToBeAnnotated.json',
        'forbidden_tokens': 'my_forbidden_tokens',
        'annotation_types': 'arguments',
        'filter_attempts_before_revealing_solution': 10,
        'ability_filter_threshold': 69,
    },
    'batch0_argumentRelations_final': {
        'hit_type': 'relations_final',
        'batch_directory_name': 'batch1',
        'textToAnnotate_filename': 'A11_ToBeAnnotated.json',
        'annotations_on_load': 'lauscher_annotations_paragraphs_2_4',
        'annotation_types': 'arguments',
        'relation_types': 'relations_1',
        'filter_attempts_before_revealing_solution': 8,
        'ability_filter_threshold': 32,
    }
}
