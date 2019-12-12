# coding: utf-8
import urllib
from PIL import Image
from numpy import matrix
from numpy import loadtxt, fromstring
from numpy import array, mat


def prepare_data(image):
    return_string = ''
    x_size, y_size = image.size
    y_size -= 5
    # y from 1 to y_size-5
    # x from 4 to x_size-18
    piece = int((x_size-22) / 8)
    centers = [4+piece*(2*i+1) for i in range(4)]
    for i, center in enumerate(centers):
        img = image.crop((center-(piece+2), 1, center+(piece+2), y_size))
        width, height = img.size
        for h in range(0, height):
            for w in range(0, width):
                pixel = img.getpixel((w, h))
                return_string = return_string + str(pixel) + ' '
        return_string = return_string[:-1] + ';'
    return return_string[:-1]

def sigmoid(z):
    from numpy import exp

    g = 1.0/(1.0+exp(-z))
    return g

def predictOneVsAll(all_theta, X):
    from numpy import dot, hstack, ones, argmax

    m = X.shape[0]

    X = hstack((ones((m, 1)), X))

    real_all_theta = all_theta.transpose()
    all_predict = sigmoid(dot(X, real_all_theta))

    Accuracy = all_predict.max(1)
    p = argmax(all_predict, axis=1)

    return Accuracy, p


def verify(image):
    from PIL import Image
    image = Image.open(image).convert("L")
    prepared_array = prepare_data(image)
    all_theta = matrix(loadtxt('zfcode/theta.dat'))
    X = array(mat(prepared_array), subok=True) / 255.0
    acc, pred = predictOneVsAll(all_theta, X)
    answers = map(chr, map(lambda x: x + 48 if x <= 9 else x + 87 if x <= 23 else x + 88, pred))
    return ''.join(answers)
