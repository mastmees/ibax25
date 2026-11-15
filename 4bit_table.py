# 0 17  34  51  68   85  102   119   136   153   170   187   204   221   238   255
#  9  26  43  60  77   94   111   128   145   162   179   196   213   230   247

for i in range(256):
  if i<9:
    x=0
  elif i<26:
    x=1
  elif i<43:
    x=2
  elif i<60:
    x=3
  elif i<77:
    x=4
  elif i<94:
    x=5
  elif i<111:
    x=6
  elif i<128:
    x=7
  elif i<145:
    x=8
  elif i<162:
    x=9
  elif i<179:
    x=10
  elif i<196:
    x=11
  elif i<213:
    x=12
  elif i<230:
    x=13
  elif i<247:
    x=14
  else:
    x=15

  print(x*17)
