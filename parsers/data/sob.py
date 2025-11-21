s = "EGEHUB2025" + "2025X"*70 + "YEYEYEYEYEYEYEYE" + "ENDEND"
m = 0
index = 10**9
for l in range(len(s)):
    for r in range(l + m, len(s)):
        c = s[l:r+1]
        if (c.count('2025') == 70) and (c.count('YE') >= 8):
            if len(c) > m:
                m = len(c)
                index = l
        if c.count('2025') > 70:
            break

print(index)


def p(x):
    return x>1 and all(x%i != 0 for i in range(2, int(x**0.5) + 1))

def div(x):
    for i in range(2, int(x**0.5) + 1):
        if x % i == 0:
            if p(i) and p(x//i) and str(i).count('5') == 1 and str(x//i).count('5') == 1:
                return sorted([i, x//i])
            else:
                return []
k = 0
for x in range(1_324_728, 2_000_000):
    if k == 5:
        break
    d = div(x)
    if d:
        print(x, d[1])
        k+=1

list = []
for n in range(1, 300):
    print(n)
    r = bin(n)[2:]
    print(int(r, 2))
    if int(r) % 2 ==0:
        r = '10' + r
    else:
        r = '1' + r + '01'
    r = int(r,2)
    if n <= 12:
        list.append(r)
print(max(list))