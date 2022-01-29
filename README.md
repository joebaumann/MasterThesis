# Hello and welcome to my beautiful master's thesis :)

If any questions arise, feel free to write me an email at <joachim.baumann@uzh.ch>.

## Running Flask App Locally

```
git clone https://github.com/joebaumann/MasterThesis.git
cd MasterThesis
conda create -n env-masterthesis-joebaumann python=3.8.2
conda activate env-masterthesis-joebaumann
pip install -r requirements.txt
FLASK_APP=app FLASK_ENV=development
flask run
```


Now that the Flask app is running locally, 


- Admin area: http://localhost:5000/admin_area


- Argument component annotation HIT template (various versions for all experiments):
    - Final version: http://localhost:5000/textannotation/arguments_final/batch0_argumentComponents_final/paragraph_2;paragraph_3;paragraph_4?assignmentId=ComponentsFinal1&workerId=workercomponent0
    - Final version (as a worker who has already passed the _ability filter_ previously): http://localhost:5000/textannotation/arguments_final/batch0_argumentComponents_final/paragraph_2;paragraph_3;paragraph_4?assignmentId=ComponentsFinal2&workerId=workercomponent1-passedfilter
    - Version used for experiment H1b: http://localhost:5000/textannotation/arguments_filterStep2/batch3_argumentComponents_filterStep2/paragraph_2;paragraph_3;paragraph_4?assignmentId=ComponentsH1b
    - Version used for experiment H1a: http://localhost:5000/textannotation/arguments_filterStep1/batch2_argumentComponents_filterStep1/paragraph_2;paragraph_3;paragraph_4?assignmentId=ComponentsH1a
    - Version used for experiment pilot 2 (paragraphs 16-18): http://localhost:5000/textannotation/arguments/batch1_argumentComponents/paragraph_16;paragraph_17;paragraph_18?assignmentId=ComponentsPilot2
    - Version used for experiment pilot 1 (paragraphs 2-4): http://localhost:5000/textannotation/arguments/batch1_argumentComponents/paragraph_2;paragraph_3;paragraph_4?assignmentId=ComponentsPilot1
- Argumentative relation annotation HIT template (various versions for all experiments):
    - Final version: http://localhost:5000/textannotation/relations_final/batch0_argumentRelations_final/paragraph_2;paragraph_3;paragraph_4?assignmentId=TestRelations_final&workerId=workerrelation1
    - Final version (as a worker who has already passed the _ability filter_ previously): http://localhost:5000/textannotation/relations_final/batch0_argumentRelations_final/paragraph_2;paragraph_3;paragraph_4?assignmentId=TestRelations_final&workerrelation1-passedfilter
    - Version used for experiment H1b: http://localhost:5000/textannotation/relations_filterStep2/batch3_argumentRelations_filterStep2/paragraph_2;paragraph_3;paragraph_4?assignmentId=RelationsH1b
    - Version used for experiment H1a: http://localhost:5000/textannotation/relations_filterStep1/batch2_argumentRelations_filterStep1/paragraph_2;paragraph_3;paragraph_4?assignmentId=RelationsH1a
    - Version used for experiment pilot 2 (paragraphs 16-18): http://localhost:5000/textannotation/relations/batch1_argumentRelations_16_18/paragraph_16;paragraph_17;paragraph_18?assignmentId=RelationsPilot2P1618
    - Version used for experiment pilot 2 (paragraphs 2-4): http://localhost:5000/textannotation/relations/batch1_argumentRelations/paragraph_2;paragraph_3;paragraph_4?assignmentId=RelationsPilot2P24


All HIT templates outlined above can also be accessed online by replacing `http://localhost:5000` with `https://masterthesisjb.herokuapp.com` or with the URL to your own Heroku app once the deployment, which is described next, is complete.


## Deployment to Heroku

Make sure Heroku is installed.
Otherwise, install it following the instructions at: https://devcenter.heroku.com/articles/heroku-cli.


Then, run the following commands to deploy the Flask app to Heroku:

```
    $ git clone https://github.com/joebaumann/MasterThesis.git
    $ cd MasterThesis
    $ heroku create
    $ git push heroku master
```

After the deployment is complete you can open the flask app using the `heroku open` command. This brings you to the welcome page. With the URLs outlined above, you can then access either the admin area or one of the various HIT templates.
Further, you can see your newly created Heroku app in the Heroku dashboard\footnote{https://dashboard.heroku.com/apps}} from where you can manage the app (for example change the app name).


Important additional information:
- Make sure that the name of the Heroku app corresponds with the `APP_NAME` variable in the config file\footnote{https://github.com/joebaumann/MasterThesis/blob/master/config.py}}.
- Make sure to always push the repository to Heroku (using `git push heroku master`) after a new batch configuration has been added to the config file).
- As the aggregation of worker answers is done with Multi-Annotator Competence Estimation (MACE)\footnote{MACE is a Java-based implementation which is available for download at:~https://www.isi.edu/publications/licensed-sw/mace}.}, make sure to download it and place in the root of the repository.
- Used Python version: 3.8.2

