import nltk
import pandas as pd
import pickle

from features import *
from sklearn.linear_model import LogisticRegression

# get training data
with open('trainingdata.pickle', 'r') as infile:
    tagged_data = pickle.load(infile)

df_train = pd.DataFrame([get_features(row[2]) for row in tagged_data])
df_train = df_train.fillna(0)

# train our linear model
# quote tag in training data is our Y value
train_cols = filter(lambda x: x != 'contains_quotes', df_train.columns.values.tolist())
train_x = df_train[train_cols]
train_y = df_train['contains_quotes']
lm = LogisticRegression()
lm = lm.fit(train_x, train_y)

def quotex(text, feature_list=train_cols, model=lm):
    # split into paragraphs on double line breaks
    paras = text.split('\r\n\r\n')
    data = pd.DataFrame([find_features(p, feature_list) for p in paras])
    guesses = model.predict(data)
    return (paras, guesses)

if __name__ == '__main__':
    test_article = """But San Francisco Superior Court Judge Lucy Kelly McCabe seemed to side with the prosecution.

"In my 25 years in court, I've never had a public defender not declare a conflict" in a similar case, McCabe said.

However, McCabe decided to let both sides file briefs on the issue and ordered them to return at 10:30 a.m. Thursday for her ruling and to continue the arraignment of Binh Thai Luc.

Brian Luc, who was in court as well Wednesday, was also arrested Sunday on suspicion of possession of narcotics, being a felon in possession of ammunition and violation of his probation.

The public defender on Wednesday declined to represent Brian Luc, who was assigned a private attorney and ordered to return for arraignment on the unrelated charges on April 3.

Adachi said outside of court that attorneys from his office met with Binh Luc and other family members in the past few days.

One of those attorneys, Deputy Public Defender Steve Olmo, said Luc is "a hard-working man" who works in construction trades.

"The family and friends that we spoke to are shocked that he's in this position," Olmo said.

Adachi also questioned the changing facts in the case since it was uncovered Friday.

"Initially we heard it was a ... murder-suicide, then we heard it was a shooting case and now we're hearing something else," he said. "There's a lot of speculation about what this case really is."
    """
    print quotex(test_article)
