'''
from scipy import stats
slope, intercept, r_value, p_value, sd_error = stats.linregress(x, y)
'''

import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import json

with open("melb_vulgar_stats.json", "r") as mel_v:
    mel_vulgar = json.load(mel_v)
with open("vic_income.json", "r") as v1:
    vic_income = json.load(v1)

mel_vulgar = mel_vulgar['rows']
vic_income = vic_income['features']


for i in range(len(mel_vulgar)):
    for j in range(len(vic_income)):
        if mel_vulgar[i]['key'] == vic_income[j]['properties']['sa2_main11']:
            mel_vulgar[i]['income'] = vic_income[j]['properties']['income_2']

print(mel_vulgar)

#keys = [k for k, v in area_dict.items()]
i = 0
while i < len(mel_vulgar):
    if mel_vulgar[i]['income'] == 0:
       del mel_vulgar[i]
    i += 1


num_vulgar_mel_list = []
income_mel_list = []

for item in mel_vulgar:
    num_vulgar = item['value']
    income_factor = item['income']
    num_vulgar_mel_list.append(num_vulgar)
    income_mel_list.append(income_factor)
'''

from heapq import nlargest
from heapq import nsmallest



vulgar = [145, 75, 69, 58, 47, 42, 41, 35, 35, 34]
vname =['Melbourne','St Kilda','Skye-Sandhurst','Doncaster East','South Morang','Thomastown','Southbank','Brunswick','Carrum Downs','East Melbourne']

y = np.arange(len(vname))
plt.barh(y,vulgar,alpha = 0.4)
plt.title('Top 10 areas with largest amount of tweets with vulgar words')
plt.yticks(y,vname)
plt.xlabel('Amount of tweets with vulgar words')

plt.show()




poor = [36879, 37588, 37602, 38418, 38683, 39520, 39762, 39822, 39865, 39882]
pname = ['Springvale','Doveton','Broadmeadows','Campbellfield-Coolaroo','Meadow Heights','Clayton','Noble Park North','Noble Park','St Albans','Dandenong North']


y = np.arange(len(pname))
plt.barh(y,poor,alpha = 0.4)
plt.title('Top 10 areas with lowest average income')
plt.yticks(y,pname)
plt.xlabel('Average income')

plt.show()

'''
income_mel_list_add = sm.add_constant(income_mel_list)  # add intercept
est = sm.OLS(num_vulgar_mel_list, income_mel_list_add)
est2 = est.fit()
print(est2.summary())

# select 10 from smallest to largest equally spaced data
X_prime = np.linspace(30000, 100000, 10)[:,np.newaxis]

X_prime = sm.add_constant(X_prime)

# calculate predict value
y_hat = est2.predict(X_prime)

def runplt() -> object:
    plt.figure()
    plt.title('Correlation of vulgar words used in tweets with Income (MEL)')
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


