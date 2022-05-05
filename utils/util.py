from sklearn.preprocessing import StandardScaler
import numpy as np


def cal_news_score(goal, title_cnt, term_cnt):
    return (goal+term_cnt*10)*(title_cnt+1)


def cal_simple_score(df, terms, threshold):
    result = []
    for item in df.iloc():
        goal = 0
        title_cnt = 0
        term_cnt = 0
        for term in terms:
            if term in item.body:
                term_cnt += 1
            goal += item.body.count(term)
            title_cnt += item.title.count(term)
        score = cal_news_score(goal, title_cnt, term_cnt)
        if score > threshold:
            result.append((int(item.id), score))
    result = sorted(result, key=lambda x: (x[1], x[0]))
    return result


def cal_feat_vec(x):
    sc = StandardScaler()
    x_std = sc.fit_transform(x)
    cov_x = np.cov(x_std.T)
    eigen_val, eigen_vec = np.linalg.eig(cov_x)

    pair_x = [(np.abs(eigen_val[i]), eigen_vec[:, i])
              for i in range(len(eigen_val))]
    pair_x.sort(key=lambda k: k[0], reverse=True)
    return pair_x[0][1].reshape(1000)


def renew_terms(terms, sim_word, mode=1):
    if mode == 0:
        return terms
    new_term = []
    for word in terms:
        new_term.append(word)
        if word in sim_word.keys():
            for sim_word in sim_word[word]:
                if sim_word not in new_term:
                    new_term.append(sim_word)
    return new_term
