library(ggplot2)        # plotting & data
library(dplyr)          # data manipulation
library(tidyr)          # data re-shaping
library(magrittr)       # pipe operator
library(gridExtra)      # provides side-by-side plotting
library(ggpubr)
library(tinytex)
library(geometry)
library(dummies)
library(zoo)
library(reader)
library(MASS)
library(ISLR)
library(stargazer)
library(robustbase)
library(sandwich)
library(lmtest)
library(latexpdf)


# load data

f1_data = read.csv(file.path("AnswerAggregationAndPerformanceEvaluation", "H1a_scores_components.csv"))
#f1_data = read.csv(file.path("AnswerAggregationAndPerformanceEvaluation", "H1a_scores_components_without_considering_type.csv")) # do not consider type
f1_data = read.csv(file.path("AnswerAggregationAndPerformanceEvaluation", "H1a_scores_relations.csv"))


# make boxplot
ggplot(f1_data, aes(group, f1)) + geom_boxplot() + ylab("F1 Score")

# perform normal 2-sample t test
t.test(f1 ~ group, data = f1_data)
