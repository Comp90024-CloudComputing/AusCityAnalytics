'''
from scipy import stats
slope, intercept, r_value, p_value, sd_error = stats.linregress(x, y)
'''

import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import json

with open("syd_vulgar_stats.json", "r") as syd_v:
    syd_vulgar = json.load(syd_v)
with open("nsw_income.json", "r") as v3:
    syd_income = json.load(v3)

syd_vulgar = syd_vulgar['rows']
syd_income = syd_income['features']


for i in range(len(syd_vulgar)):
    for j in range(len(syd_income)):
        if syd_vulgar[i]['key'] == syd_income[j]['properties']['sa2_main11']:
            syd_vulgar[i]['income'] = syd_income[j]['properties']['income_2']

print(syd_vulgar)


k = 0
while k < len(syd_vulgar):
    if syd_vulgar[k]['income'] == 0:
       del syd_vulgar[k]
    k += 1

j = 0
while j < len(syd_vulgar):
    if syd_vulgar[j]['income'] == 0 :
       del syd_vulgar[j]
    j += 1




num_vulgar_mel_list = []
income_mel_list = []

for item in syd_vulgar:
    num_vulgar = item['value']
    income_factor = item['income']
    num_vulgar_mel_list.append(num_vulgar)
    income_mel_list.append(income_factor)







income_mel_list_add = sm.add_constant(income_mel_list)  # add intercept
est = sm.OLS(num_vulgar_mel_list, income_mel_list_add)
est2 = est.fit()
print(est2.summary())

# select 10 from smallest to largest equally spaced data
X_prime = np.linspace(20000, 130000, 10)[:,np.newaxis]

X_prime = sm.add_constant(X_prime)

# calculate predict value
y_hat = est2.predict(X_prime)

def runplt() -> object:
    plt.figure()
    plt.title('Correlation of vulgar words used in tweets with income (SYD, updated version)')
    plt.xlabel('Income of each area')
    plt.ylabel('Amount of tweets with vulgar words')

    plt.grid(True)
    return plt
p = runplt()

p.plot(income_mel_list, num_vulgar_mel_list,'k.')
p.plot(X_prime[:, 1], y_hat, 'g', alpha=0.9)

yr = est2.predict(income_mel_list_add)

for i, x in enumerate(income_mel_list):
    p.plot([x, x], [num_vulgar_mel_list[i], yr[i]], 'r-')

p.show()

print("average tweets with vulgar words: ", )
