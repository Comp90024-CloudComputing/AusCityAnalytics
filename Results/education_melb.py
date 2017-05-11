'''
from scipy import stats
slope, intercept, r_value, p_value, sd_error = stats.linregress(x, y)
'''

import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import json

with open("melb_education_stats.json", "r") as mel_e:
    mel_education = json.load(mel_e)
with open("vic_income.json", "r") as v2:
    vic_income = json.load(v2)



mel_education = mel_education['rows']
vic_income = vic_income['features']


for i in range(len(mel_education)):
    for j in range(len(vic_income)):
        if mel_education[i]['key'] == vic_income[j]['properties']['sa2_main11']:
            mel_education[i]['income'] = vic_income[j]['properties']['income_2']

print(mel_education)

#keys = [k for k, v in area_dict.items()]
i = 0
while i < len(mel_education):
    if mel_education[i]['income'] == 0:
       del mel_education[i]
    i += 1


num_edu_mel_list = []
income_mel_list = []

for item in mel_education:
    num_edu = item['value']
    income_factor = item['income']
    num_edu_mel_list.append(num_edu)
    income_mel_list.append(income_factor)

print(num_edu_mel_list)
print(income_mel_list)



income_mel_list_add = sm.add_constant(income_mel_list)  # add intercept
est = sm.OLS(num_edu_mel_list, income_mel_list_add)
est2 = est.fit()
print(est2.summary())

# select 10 from smallest to largest equally spaced data
X_prime = np.linspace(30000, 100000, 10)[:,np.newaxis]

X_prime = sm.add_constant(X_prime)

# calculate predict value
y_hat = est2.predict(X_prime)

def runplt() -> object:
    plt.figure()
    plt.title('Relationship: vulgar words used in tweets with income')
    plt.xlabel('income')
    plt.ylabel('tweets with vulgar words')

    plt.grid(True)
    return plt
p = runplt()

p.plot(income_mel_list, num_edu_mel_list,'k.')
p.plot(X_prime[:, 1], y_hat, 'g', alpha=0.9)

yr = est2.predict(income_mel_list_add)

for i, x in enumerate(income_mel_list):
    p.plot([x, x], [num_edu_mel_list[i], yr[i]], 'r-')

p.show()

