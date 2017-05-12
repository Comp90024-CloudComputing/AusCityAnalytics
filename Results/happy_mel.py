import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import json

with open("vic_income.json", "r") as v:
    vic_income = json.load(v)
with open("melb_sentiment_stats.json", "r") as m:
    mel_sentiment = json.load(m)

vic_income = vic_income['features']

mel_sentiment = mel_sentiment['rows']


from collections import defaultdict
area_dict = defaultdict(lambda : defaultdict(int))



for record in mel_sentiment:
    area = record['key'][0]
    sentiment = record['key'][1]
    area_dict[area][sentiment]=record['value']



for item in area_dict.keys():
    for j in range(len(vic_income)):
        if item == vic_income[j]['properties']['sa2_main11']:
           area_dict[item]['income'] = vic_income[j]['properties']['income_2']


keys = [k for k, v in area_dict.items()]
for k in keys:
    if area_dict[k]['income'] == 0:
        del area_dict[k]

print(area_dict)
income_mel_list = []
num_point_list = []

happiness_dict = {}
for item in area_dict.keys():
    num_income = area_dict[item]['income']
    num_point = area_dict[item]['positive'] - area_dict[item]["negative"]
    income_mel_list.append(num_income)
    num_point_list.append(num_point)
    happiness_dict[item] = num_point
'''
import operator
happiness_sorted = sorted(happiness_dict.items(),key=operator.itemgetter(1),reverse=True)
print(happiness_sorted[0:10])



happy = [7298, 2679, 2181, 1404, 1273, 1009, 995, 915, 887, 822]

happyname = ['Melbourne','Southbank','East Melbourne','St Kilda','Richmond(Vic)','Docklands','South Yarra - East','Prahran - Windsor','Fitzroy','Carlton']

y = np.arange(len(happyname))
plt.barh(y,happy,alpha = 0.4)
plt.title('Top 10 happiest areas')
plt.yticks(y,happyname)
plt.xlabel('Happiness points')

plt.show()
'''

'''

#print(nlargest(10, income_mel_list))

income = [90232, 86883, 85152, 79019, 78909, 78897, 77602, 76407, 75184, 75170]


incomename = ['Brighton(Vic)','Toorak','Albert Park','Port Melbourne','Port Melbourne Industrial','Surrey Hills(West)','East Melbourne','Armadale','Sandringham','Hampton']


y = np.arange(len(incomename))
plt.barh(y,income,align = 'center',alpha = 0.4)
plt.title('Top 10 wealthy areas')
plt.yticks(y,incomename)
plt.xlabel('average income')

plt.show()


'''





income_mel_list_add = sm.add_constant(income_mel_list)  # add intercept
est = sm.OLS(num_point_list, income_mel_list_add)
est2 = est.fit()
print(est2.summary())

# select 10 from smallest to largest equally spaced data
X_prime1 = np.linspace(32000, 100000, 10)[:,np.newaxis]

X_prime1 = sm.add_constant(X_prime1)

# calculate predict value
y_hat = est2.predict(X_prime1)

def runplt() -> object:
    plt.figure()
    plt.title('Correlation of income with  happiness (MEL)')
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
