import os

for i in os.walk("C://"):
    for j in i[2]:
        if ".astralback" in j.lower():
            print(j, i)
