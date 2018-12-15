from math import log


def boh(n):
    # 0 4, 1 5, 2 6, 3 7-->                 0, 8, +4
    # 0 2, 1 3 | 4 6, 5 7 -->         0, 4, +2 |            4, 8, +2
    # 0 1 || 2 3 || 4 5 || 6 7 --> 0, 2, +1 | 2, 4, +1 || 4, 6, +1 | 6, 8, +1
    bla3(0, n, int(n / 2), 1)


#start included, end excluded
def bla(start, end, swap_step):
    print("Start: {0}, end: {1}, swap_step: {2}".format(start, end, swap_step))
    if (swap_step == 0):
        print("End recursion")
        return
    for i in range(start, end - swap_step):
        print("***Cswapping {0} w/ {1}".format(i, i + swap_step))
    bla(start, int(end / 2), int(swap_step / 2))
    bla(int(end / 2) + 1, end, int(swap_step / 2))


def bla2(n):
    depth = log(n, 2)
    step = n / 2
    nn = n
    step = 1
    for i in range(depth):
        for j in range(0, nn / 2, step):
            print("***Cswapping {0} w/ {1}".format(j, j + swap_step))
        nn = nn / 2


def bla3(start, end, swap_step, counter):
    # print("{3} Start: {0}, end: {1}, swap_step: {2}".format(
    #     start, end, swap_step, ">" * counter))
    if (swap_step == 0 or start >= end):
        # print("End recursion")
        return
    for i in range(start, int((start + end) / 2)):
        print("***** Cswapping {0} w/ {1}".format(i, i + swap_step))
    bla3(start, int((start + end) / 2), int(swap_step / 2), counter + 1)
    bla3(int((start + end) / 2), end, int(swap_step / 2), counter + 1)


# > 0, 8, 4 --- for(0, 1, 2, 3): swap(04,15,26,37) --- bla(0, 4, 2)
# >> 0, 4, 2 --- for(0, 1): swap(02, 13) --1-- bla(0, 2, 1)
# >>> 0, 2, 1 --- for (0): swap(01) --1-- bla(0, 1, 0)
# >>>> return
# >>>                               --2-- bla(1, 1, 0)
# >>>> return
# >>> return
# >>                                     --2-- bla(2, 4, 1)
# >>> 2, 4, 1 --- for(2, 3): swap(23, )


def main():
    n = 8
    boh(n)


if __name__ == "__main__":
    main()
