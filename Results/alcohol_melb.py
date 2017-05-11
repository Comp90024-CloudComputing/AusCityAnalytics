'''
from scipy import stats
slope, intercept, r_value, p_value, sd_error = stats.linregress(x, y)
'''

import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import json

with open("melb_alcohol_stats.json", "r") as mel_a:
    mel_alcohol = json.load(mel_a)
with open("mel_health.json", "r") as m_health:
    mel_health = json.load(m_health)

for i in range(len(mel_alcohol['rows'])):
    for j in range(len(mel_health['features'])):
        if int(mel_alcohol['rows'][i]['key']) == mel_health['features'][j]['properties']['area_code']:
            mel_alcohol['rows'][i]['alcohol'] = mel_health['features'][j]['properties']['alcohol_cons_1_no_3_11_7_13']

mel_alcohol = mel_alcohol['rows']
k = 0
while k < len(mel_alcohol):
    if mel_alcohol[k]['alcohol'] <= 5:
       del mel_alcohol[k]
    k += 1
num_alcohol_mel_list = []
alcohol_mel_list = []

for item in mel_alcohol:
    num_tweets = item['value']
    alcohol_factor = item['alcohol']
    num_alcohol_mel_list.append(num_tweets)
    alcohol_mel_list.append(alcohol_factor)


print(num_alcohol_mel_list)
print(alcohol_mel_list)

alcohol_mel_list_add = sm.add_constant(alcohol_mel_list)  # add intercept
est = sm.OLS(num_alcohol_mel_list, alcohol_mel_list_add)
est2 = est.fit()
print(est2.summary())

# select 10 from smallest to largest equally spaced data
X_prime = np.linspace(50, 1000, 10)[:,np.newaxis]

X_prime = sm.add_constant(X_prime)

# calculate predict value
y_hat = est2.predict(X_prime)

def runplt() -> object:
    plt.figure()
    plt.title('Correlation of alcohol related tweets with health risk factor (MEL)')
    plt.xlabel('Alcohol consumption persons - Count ')
    plt.ylabel('Amount of alcohol related tweets')

    plt.grid(True)
    return plt
p = runplt()

p.plot(alcohol_mel_list, num_alcohol_mel_list,'k.')
p.plot(X_prime[:, 1], y_hat, 'g', alpha=0.9)

yr = est2.predict(alcohol_mel_list_add)

for i, x in enumerate(alcohol_mel_list):
    p.plot([x, x], [num_alcohol_mel_list[i], yr[i]], 'r-')

p.show()


