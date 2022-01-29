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
f1_data = read.csv(file.path("AnswerAggregationAndPerformanceEvaluation", "H1b_scores_relations.csv")) # without aggregation


# scatter plot
ggplot(f1_data, aes(x=nr_of_tries_sum, y=f1_TOTAL)) + geom_point(col="steelblue4", size=2, position=position_jitter(h=0.01,w=0.1), alpha = 0.5) + geom_smooth(method = "lm",col="red",fill=NA) + labs(x="Number of attempts", y="F1 total") + theme_grey()

# scatter plot with threshold suggestion for discussion
ggplot(f1_data, aes(x=nr_of_tries_sum, y=f1_TOTAL)) + geom_point(col="steelblue4", size=2, position=position_jitter(h=0.01,w=0.1), alpha = 0.5) + labs(x="Number of attempts", y="F1 total") + theme_grey() + geom_vline(xintercept = 32, linetype="dashed", color = "green3", size=1)

#regression
myModel1 <- lm(f1_TOTAL ~ nr_of_tries_sum, data = f1_data)

#regression table
stargazer(myModel1,align=TRUE, dep.var.labels = "F1 total", covariate.labels=c("Number of attempts"), type = 'latex',omit.stat=c("LL","ser","f", "rsq", "adj.rsq"))

