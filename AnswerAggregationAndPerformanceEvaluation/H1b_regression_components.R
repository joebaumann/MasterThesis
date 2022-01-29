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
f1_data = read.csv(file.path("AnswerAggregationAndPerformanceEvaluation", "H1b_scores_components.csv"))

# scatter plot
ggplot(f1_data, aes(x=nr_of_tries_sum, y=f1)) + geom_point(col="steelblue4", size=2, position=position_jitter(h=0.01,w=0.1), alpha = 0.5) + geom_smooth(method = "lm",col="red",fill=NA) + labs(x="Number of attempts", y="F1") + theme_grey() + ylim(0, 1)

# scatter plot with suggested threshold for discussion
ggplot(f1_data, aes(x=nr_of_tries_sum, y=f1)) + geom_point(col="steelblue4", size=2, position=position_jitter(h=0.01,w=0.1), alpha = 0.5) + labs(x="Number of attempts", y="F1") + theme_grey() + ylim(0, 1) + geom_vline(xintercept = 69, linetype="dashed", color = "green3", size=1)

# regression
myModel1 <- lm(f1 ~ nr_of_tries_sum, data = f1_data)

stargazer(myModel1,align=TRUE, dep.var.labels = "F1 Score", covariate.labels=c("Number of attempts"), type = 'text',omit.stat=c("LL","ser","f", "rsq", "adj.rsq"))

