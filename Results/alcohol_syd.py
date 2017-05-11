import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import json

with open("syd_alcohol_stats.json", "r") as syd_a:
    syd_alcohol = json.load(syd_a)
with open("alcohol_syd.json", "r") as s_health:
    syd_health = json.load(s_health)

for i in range(len(syd_alcohol['rows'])):
    for j in range(len(syd_health['features'])):
        if int(syd_alcohol['rows'][i]['key']) == syd_health['features'][j]['properties']['area_code']:
            syd_alcohol['rows'][i]['alcohol'] = syd_health['features'][j]['properties']['alcohol_cons_1_no_3_11_7_13']

syd_alcohol = syd_alcohol['rows']


k = 0
while k < len(syd_alcohol):
    if syd_alcohol[k]['alcohol'] <= 1:
       del syd_alcohol[k]
    k += 1



num_alcohol_syd_list = []
alcohol_syd_list = []

for item in syd_alcohol:
    num_tweets = item['value']
    alcohol_factor = item['alcohol']
    num_alcohol_syd_list.append(num_tweets)
    alcohol_syd_list.append(alcohol_factor)




alcohol_syd_list_add = sm.add_constant(alcohol_syd_list)  # add intercept
est = sm.OLS(num_alcohol_syd_list, alcohol_syd_list_add)
est2 = est.fit()
print(est2.summary())

# select 10 from smallest to largest equally spaced data
X_prime = np.linspace(100, 1300, 10)[:,np.newaxis]

X_prime = sm.add_constant(X_prime)

# calculate predict value
y_hat = est2.predict(X_prime)

def runplt() -> object:
    plt.figure()
    plt.title('Correlation of alcohol related tweets with health risk factor (SYD)')
    plt.xlabel('Alcohol consumption persons - Count')
    plt.ylabel('Amount of alcohol related tweets')

    plt.grid(True)
    return plt
p = runplt()

p.plot(alcohol_syd_list, num_alcohol_syd_list,'k.')
p.plot(X_prime[:, 1], y_hat, 'g', alpha=0.9)

yr = est2.predict(alcohol_syd_list_add)

for i, x in enumerate(alcohol_syd_list):
    p.plot([x, x], [num_alcohol_syd_list[i], yr[i]], 'r-')

p.show()


