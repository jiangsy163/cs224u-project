import buildwd
import csv
import numpy as np
from sklearn import linear_model
from sklearn import neighbors

TRAIN_FILE = 'data/training.txt'

GLOVE_MAT = None
GLOVE_VOCAB = None
GLVVEC_LENGTH = 50

GLOVE_CACHE = None

def build(src_filename, delimiter=',', header=True, quoting=csv.QUOTE_MINIMAL):
    reader = csv.reader(file(src_filename), delimiter=delimiter, quoting=quoting)
    colnames = None
    if header:
        colnames = reader.next()
        colnames = colnames[1: ]
    mat = []
    rownames = []
    for line in reader:
        rownames.append(line[0])
        mat.append(np.array(map(float, line[1: ])))
    return (np.array(mat), rownames, colnames)

def glvvec(w):
    """Return the GloVe vector for w."""
    if GLOVE_CACHE != None:
        return GLOVE_CACHE[w]
    if w in GLOVE_VOCAB:
        i = GLOVE_VOCAB.index(w)
        return GLOVE_MAT[i]
    else:
        return np.zeros(GLVVEC_LENGTH)

def buildGloveCache(words):
    global GLOVE_CACHE
    print 'Building GLOVE cache...'
    temp = {}
    for w in words:
        temp[w] = glvvec(w)
    GLOVE_CACHE = temp

def glove_features_mean_unweighted(tweetRow, words):
    result = np.zeros(GLVVEC_LENGTH)
    count = 0.0
    for i, w in enumerate(words):
        if tweetRow[i] == 0.0: continue
        vec = glvvec(w)
        count += 1.0
        result += vec
    return result / count

def glove_features_mean_weighted(tweetRow, words):
    result = np.zeros(GLVVEC_LENGTH)
    count = 0.0
    for i, w in enumerate(words):
        vec = glvvec(w)
        count += tweetRow[i]
        result += tweetRow[i] * vec
    return result / count

# len(tweetRow) == len(words)
def glove_features(tweetRow, words):
    return glove_features_mean_weighted(tweetRow, words)

def buildGloveTrainMat(train_file):
    wd = buildwd.buildWD(train_file)
    mat = wd[0]
    tweetIDs = wd[1]
    words = wd[2]
    labels = wd[3]
    buildGloveCache(words)
    mat = np.transpose(mat)
    print 'Building GLOVE train matrix...'
    trainMat = np.array([glove_features(mat[i,:], words) for i in range(len(tweetIDs))])
    return trainMat

def glove_knn(train_file, trainMat=None):
    if trainMat == None:
        trainMat = buildGloveTrainMat(train_file)

    wd = buildwd.buildWD(train_file)
    labels = wd[3]
    trainVals = np.zeros(len(labels))
    for s in enumerate(labels):
        if s[1] == 'Sports':
            trainVals[s[0]] = 1

    knn = neighbors.KNeighborsClassifier(n_neighbors=5)
    knn.fit(trainMat[0:(trainMat.shape[0]*0.7),:], trainVals[0:(trainMat.shape[0]*0.7)])
    return knn.score(trainMat[(trainMat.shape[0]*0.7):,:], trainVals[(trainMat.shape[0]*0.7):])

def glove_logreg(train_file, trainMat=None):
    if trainMat == None:
        trainMat = buildGloveTrainMat(train_file)

    wd = buildwd.buildWD(train_file)
    labels = wd[3]
    trainVals = np.zeros(len(labels))
    for s in enumerate(labels):
        if s[1] == 'Sports':
            trainVals[s[0]] = 1

    logreg = linear_model.LogisticRegression()
    logreg.fit(trainMat[0:(trainMat.shape[0]*0.7),:], trainVals[0:(trainMat.shape[0]*0.7)])
    return logreg.score(trainMat[(trainMat.shape[0]*0.7):,:], trainVals[(trainMat.shape[0]*0.7):])

if __name__ == "__main__":
    print 'Building GLOVE...'
    GLOVE_MAT, GLOVE_VOCAB, _ = build('data/glove.6B.50d.txt', delimiter=' ',\
                                      header=False, quoting=csv.QUOTE_NONE)
    trainMat = buildGloveTrainMat(TRAIN_FILE)
    score_knn = glove_knn(TRAIN_FILE, trainMat=trainMat)
    print 'KNN: ', score_knn
    score_logreg = glove_logreg(TRAIN_FILE, trainMat=trainMat)
    print 'LogReg: ', score_logreg