import random
n = 9
def twoKeyGenerator():
    num1 = random.randint(1,100) #7 num1%n = num2%n
    num2 = random.randint(1,10)*n + num1%n # 13*9 + 7 = 130+7 = 137
    return num1, num2
def checkKeys(x,y):
    if x%n == y%n:
        return True
    else:
        return False

