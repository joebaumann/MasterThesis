import pandas as pd
from statsmodels.stats.power import TTestIndPower
from itertools import combinations
from pprint import pprint


def power_analysis(prepare_data_for_pa):

    df_experiment_results = pd.DataFrame(prepare_data_for_pa)

    # MEANS FOR : # data from H1a (f1 per worker per paragraph)
    mean_scores = df_experiment_results.groupby(['group_name'])['total_score'].mean()
    stdev_scores = df_experiment_results.groupby(['group_name'])['total_score'].std()
    
    l = mean_scores.index.values
    groups = list(combinations(l, 2))
    print("groups", groups)
    print("mean_scores:")
    pprint(mean_scores)
    pprint('***')
    print("stdev_scores:")
    pprint(stdev_scores)


    alpha = 0.05
    power = 0.8
    ratio = 1 #N1/N2

    for g in groups:
        print(g[0],' - ',g[1])
        mean_diff, sd_diff = abs(mean_scores[g[0]]-mean_scores[g[1]]),abs(stdev_scores[g[0]]-stdev_scores[g[1]])
        try:
            std_effect_size = mean_diff / sd_diff
            
            ## given power, get sample size
            n = TTestIndPower().solve_power(effect_size=std_effect_size, alpha=alpha, power=power, ratio=ratio, alternative='two-sided')
            print('*Expected sample size in each group for power ',power,': ',n)
            
            ## given sample size, get power
            p = TTestIndPower().solve_power(effect_size=std_effect_size, alpha=alpha, nobs1=5, ratio=ratio, alternative='two-sided')
            print('*Achieved power ',p)
        except:
            print('Effect size is 0')
            p = TTestIndPower().solve_power(effect_size=std_effect_size, alpha=alpha, nobs1=5, ratio=ratio, alternative='two-sided')
            print('*Achieved power ',p)
        
