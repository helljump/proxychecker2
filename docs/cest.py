# -*- coding: utf-8 -*-

import bcryptor
hasher = bcryptor.Bcrypt()

h = 'JDJhJDEwJGZyRmhTbnI5OUVoSk82VGtqM1hmQU9HOGtsQy5mSlNDLkxDbnBQMmp5dWRpaTNGMkpLNnJt'.decode('base64')
p = 'sdvvuh*^Glksasal@#^vicysa789444476@@@^df86cq)(*&wefg8od6'

print hasher.valid(p, h)
