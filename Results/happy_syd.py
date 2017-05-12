import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import json

with open("nsw_income.json", "r") as n:
    nsw_income = json.load(n)
with open("syd_sentiment_stats.json", "r") as m:
    syd_sentiment = json.load(m)

nsw_income = nsw_income['features']

syd_sentiment = syd_sentiment['rows']


from collections import defaultdict
nsw_area_dict = defaultdict(lambda : defaultdict(int))



for record in syd_sentiment:
    area = record['key'][0]
    sentiment = record['key'][1]
    nsw_area_dict[area][sentiment]=record['value']



for item in nsw_area_dict.keys():
    for j in range(len(nsw_income)):
        if item == nsw_income[j]['properties']['sa2_main11']:
            nsw_area_dict[item]['income'] = nsw_income[j]['properties']['income_2']
print(nsw_area_dict)

keys = [k for k, v in nsw_area_dict.items()]
for k in keys:
    if (nsw_area_dict[k]['income']==0 or nsw_area_dict[k]['positive'] >40000):
        del nsw_area_dict[k]


income_mel_list = []
num_point_list = []

for item in nsw_area_dict.keys():
    num_income = nsw_area_dict[item]['income']
    num_point = nsw_area_dict[item]['positive'] - nsw_area_dict[item]["negative"]
    income_mel_list.append(num_income)
    num_point_list.append(num_point)

print(income_mel_list)
print(num_point_list)



income_mel_list_add = sm.add_constant(income_mel_list)  # add intercept
est = sm.OLS(num_point_list, income_mel_list_add)
est2 = est.fit()
print(est2.summary())

# select 10 from smallest to largest equally spaced data
X_prime1 = np.linspace(20000, 130000, 10)[:,np.newaxis]

X_prime1 = sm.add_constant(X_prime1)

# calculate predict value
y_hat = est2.predict(X_prime1)

def runplt() -> object:
    plt.figure()
    plt.title('Correlation of income with  happiness (SYD)')
    plt.xlabel('Income of each area')
    plt.ylabel('Happiness points')

    plt.grid(True)
    return plt
p = runplt()

p.plot(income_mel_list,num_point_list,'k.')
p.plot(X_prime1[:, 1], y_hat, 'g', alpha=0.9)

yr = est2.predict(income_mel_list_add)

for i, x in enumerate(income_mel_list):
    p.plot([x, x], [num_point_list[i], yr[i]], 'r-')

p.show()
