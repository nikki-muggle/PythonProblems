# Automated tester for the problems in the collection
# "109 Python Problems for CCPS 109" by Ilkka Kokkarinen.
# Ilkka Kokkarinen, ilkka.kokkarinen@gmail.com

from hashlib import sha256
from time import time
import itertools as it
import random
import gzip
import os.path

version = "July 13, 2020"

# Fixed seed used to generate pseudorandom numbers.
seed = 12345

# How many test cases to record in the file for each function.
testcase_cutoff = 300

# Name of the file that contains the expected correct answers.
recordfile = 'record'

# Whether to use the recorded test results when they exist. This
# needs to be set to false only when editing the test case
# generator for a new or an existing problem. Once you have
# added the new problem, set this to True and delete the record
# file, and then run this tester to generate the record file.
use_record = True

# Name of the module that contains the student solutions.
studentfile = 'labs109'

# Convert a dictionary or set result to a list sorted by keys to
# guarantee that such results are identical in all environments.

def canonize(result):
    if isinstance(result, dict):
        result = [(key, result[key]) for key in result]
        result.sort()
    elif isinstance(result, set):
        result = [key for key in result]
        result.sort()
    return result

# When reporting an error, make sure not to flood the user console.

def emit_args(args, cutoff=100):
    for (i, a) in enumerate(args):
        if i > 0:
            print(", ", end='')
        if type(a) == list or type(a) == tuple:
            if len(a) < cutoff:
                print(a, end='')
            else:
                left = ", ".join([str(x) for x in a[:5]])
                right = ", ".join([str(x) for x in a[-5:]])
                print(f"[{left}, [{len(a)-10} omitted...], {right}]", end='')
        else:
             print(repr(a) if len(repr(a)) < 100 else '[...]', end='')
    print()

# Given teacher and student implementations of the same function, run
# the test cases for both of them and output the first or the shortest
# test case for which these two implementations disagree.

def discrepancy(teacher, student, testcases, stop_at_first = False):
    shortest, d1, d2, disc = None, None, None, 0
    for n, elem in enumerate(testcases):
        elem2 = elem[:]  # In case student function messes up elem...
        try:
            r1 = canonize(teacher(*elem))
        except Exception as e:
            r1 = f"CRASH! {e}"
        try:
            r2 = canonize(student(*elem))
        except Exception as e:
            r2 = f"CRASH! {e}"
        if r1 != r2:
            disc += 1
            if stop_at_first or shortest == None or len(str(elem2)) < len(shortest):
                shortest, d1, d2 = elem2, r1, r2
            if stop_at_first:
                break
    if shortest == None:
        print("Both functions returned the same answers.")
        return True
    else:
        if stop_at_first:
            print("First discrepancy found.")
        else:
            print(f"For {n} test cases, found {disc} discrepancies.")
            print("Shortest discrepancy input was:")
        print(shortest)
        print(f"Model  : {repr(d1)}")
        print(f"Student: {repr(d2)}")
        return False


# Runs the function f for its test cases, calculating SHA256 checksum
# of the results. If the checksum matches the expected, return the
# running time, otherwise return -1. If expected == None, print out
# the computed checksum instead. If recorder != None, print out the
# arguments and expected result into the recorder.

def test_one_function(f, testcases, expected = None, recorder = None, known = None):
    fname = f.__name__
    print(f"{fname}: ", end="", flush = True)
    if recorder:
        print(f"****{fname}", file = recorder)
    if known:
        recorded = known.get(fname, None)
    chk, starttime, crashed = sha256(), time(), False
    for (count, test) in enumerate(testcases):
        try:
            result = f(*test)
        except Exception as e: # catch any exception
            crashed = True
            print(f"CRASH! {e}")
            break
        # If the result is a set or dictionary, turn it into sorted list first.
        result = canonize(result)
        # Update the checksum.
        sr = str(result)
        chk.update(sr.encode('utf-8'))
        if recorder:
            print(sr.strip()[:300], file = recorder)
            if count >= testcase_cutoff:
                break
        if use_record and known and count < testcase_cutoff and recorded:
            should_be = recorded[count]
            if len(should_be) < 295:
                ok = (sr.strip() == should_be)
            else:
                ok = sr.strip().startswith(should_be)
            if not ok:
                crashed = True
                print(f"DISCREPANCY AT TEST CASE #{count}: ")
                print("TEST CASE: ", end ="")
                emit_args(test)
                print(f"EXPECTED: {should_be} {'...' if len(should_be) == 300 else ''}")
                print(f"RETURNED: {sr}")
                break
    if not recorder:
        totaltime = time() - starttime
        digest = chk.hexdigest()
        if not crashed and not expected:
            print(digest[:50])
            return totaltime
        elif not crashed and digest[:len(expected)] == expected:
            print(f"Success in {totaltime:.3f} seconds.")
            return totaltime
        elif crashed:
            return -1
        else:
            print("Failed the test with checksum mismatch.".upper())
            return -1
    else:
        return 0

# Sort the suite of test cases according to the order in which
# they appear in the student source code.

def sort_by_source(suite):
    funcs = dict()
    with open(f'{studentfile}.py', 'r', encoding='utf-8') as source:
        for (lineno, line) in enumerate(source):
            if line.startswith("def "):
                fname = line[4:line.find('(')].strip()
                if fname in funcs:
                    print(f"Warning: multiple definition for {fname}")
                funcs[fname] = lineno
        suite.sort(key=lambda x: funcs.get(x[0], 9999999))
    return suite


# Runs the tests for all functions in the suite, returning the
# count of how many of those were implemented and passed the test.

def test_all_functions(module, suite, recorder = None, known = None):
    if recorder:
        print("RECORDING THE RESULTS OF THE IMPLEMENTED FUNCTIONS.")
        print("IF YOU ARE A STUDENT, YOU SHOULD NOT BE SEEING THIS")
        print(f"MESSAGE! MAKE SURE THAT THE FILE {recordfile} FROM THE")
        print("PLACE WHERE YOU DOWNLOADED THIS AUTOMATED TESTER IS")
        print("PROPERLY DOWNLOADED INTO THIS WORKING DIRECTORY!")
    count, total = 0, 0
    for (fname, testcases, expected) in sort_by_source(suite):
        try:
            f = module.__dict__[fname]
        except KeyError:
            continue
        total += 1
        result = test_one_function(f, testcases, expected, recorder, known)
        if result >= 0:
            count += 1
    if recorder:
        print(f"\nRecording complete.")
    else:
        print(f"{count} out of {total} functions (of {len(suite)} possible) work.")
    return count

# Some utility functions to help writing test generators.

# Produce an infinite sequence of exponentially increasing integers.
# The parameters scale and skip determine how quickly the sequence grows.
def scale_random(seed, scale, skip):
    # The seed value determines the future random sequence.
    rng = random.Random(seed)
    curr, count, orig = 1, 0, scale
    while True:
        curr += rng.randint(1, scale)
        yield curr
        count += 1
        if count == skip:
            scale = scale * orig
            count = 0

# This function replaced warandpeace.txt as the source of textual data.
# Since none of the problems that used that file were linguistic in nature,
# there was no point using real text to test them, losing a few megs of
# deadweight from this project folder.

def random_text_generator(seed, n = 70):
    rng = random.Random(seed)
    alpha = "abcdefghijklmnopqrstuvwxyz"
    alpha += alpha.upper()
    punct = '.,!?'
    for i in range(10000):
        line = ""
        while len(line) < n:
            word = "".join([rng.choice(alpha) for _ in range(rng.randint(1, 20))])
            line += " " if len(line) > 0 else ""
            line += word
            if rng.randint(0, 99) < 20:
                line += rng.choice(punct)
        yield (line, )

# Create a random n-character string from the given alphabet.
def random_string(alphabet, n, rng):
    result = ''
    for i in range(n):
        result += rng.choice(alphabet)
    return result

# The test case generators for the individual functions.

def ryerson_letter_grade_generator():
    for i in range(0, 150):
        yield (i,)

def is_ascending_generator(seed):
    rng = random.Random(seed)
    for i in range(500):
        for j in range(10):
            items = [rng.randint(-(i+2), i+2)]
            for k in range(i + 1):
                items.append(items[-1] + rng.randint(1, 20))
            yield (items,)
            if i > 2:
                for k in range(rng.randint(0, 5)):
                    idx = rng.randint(1, len(items)-1)
                    items[idx-1], items[idx] = items[idx], items[idx-1]
                    yield (items,)

def safe_squares_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        n = rng.randint(2, 20)
        pn = rng.randint(0, n * n - 3)
        pieces = []
        while len(pieces) < pn:
            px = rng.randint(0, n-1)
            py = rng.randint(0, n-1)
            if (px, py) not in pieces:
                pieces.append((px, py))
        yield (n, pieces)

def rooks_with_friends_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        n = rng.randint(2, 20)
        pn = rng.randint(0, 2 * n)
        pieces = []
        while len(pieces) < pn:
            px = rng.randint(0, n-1)
            py = rng.randint(0, n-1)
            if (px, py) not in pieces:
                pieces.append((px, py))
        fn = rng.randint(0, n)
        yield (n, pieces[:fn], pieces[fn:])
        yield (n, pieces[fn:], pieces[:fn])

def double_until_all_digits_generator():
    for i in range(3000):
        yield (i,)

def first_preceded_by_smaller_generator(seed):
    rng = random.Random(seed)
    for i in range(500):
        for j in range(10):
            n = rng.randint(1, 10 * (i+2))
            items = []
            for jj in range(n):
                items.append(rng.randint(0, 3 * i + 1))
            currk = 1
            for k in range(1, 5):
                yield (items[:], currk)
                currk += rng.randint(1, 3)

def maximum_difference_sublist_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        len_ = rng.randint(1, 100)
        items = [rng.randint(0, 10000) for j in range(len_)]
        for k in range(1, len_ + 1):
            yield (items[:], k)

def count_and_say_generator(seed):
    rng = random.Random(seed)
    for i in range(10000):
        bursts = rng.randint(1, 50)
        digits = ''
        for i in range(bursts):
            n = rng.randint(1, 20)
            digits += rng.choice('0123456789') * n
        yield (digits,)

def group_equal_generator(seed):
    rng = random.Random(seed)
    for i in range(50):
        for j in range(10):
            items = []
            bursts = rng.randint(1, 2 + i // 5)
            for k in range(bursts):
                n = rng.randint(1, 2 + i // 5)
                v = rng.randint(0, 10 + i // 20)
                items.extend([v] * n)
            yield (items,)

def longest_palindrome_generator(seed):
    lets = 'abcdefghijklmnopqrstuvxyz'
    rng = random.Random(seed)
    for i in range(1000):
        p1 = rng.randint(0, i + 3)
        p2 = rng.randint(2, i + 3)
        p3 = rng.randint(0, i + 3)
        left = random_string(lets, p1, rng)
        middle = random_string(lets, p2, rng)
        if rng.randint(0, 1) == 1:
            middle += middle[::-1]
        else:
            middle += middle[:len(middle)-1:-1]
        right = random_string(lets, p3, rng)
        yield (left + middle + right,)

def reverse_ascending_sublists_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        for j in range(5):
            curr = []
            for k in range(i + 1):
                curr.append(rng.randint(0, 2 * i))
            yield (curr, )

def give_change_generator(seed):
    rng = random.Random(seed)
    coins = [1]
    for i in range(10):
        coins.append(coins[-1] + rng.randint(1, 1 + coins[-1]))
    for i in range(1000):
        for j in range(1, 10):
            use = rng.sample(coins, j)
            use.sort(reverse=True)
            if use[-1] > 1:
                use.append(1)
            amount = 1
            while amount < 5 * use[0]:
                yield (amount, use)
                amount += rng.randint(1, 2 + 2 * amount // 3)


suits = ['clubs', 'diamonds', 'hearts', 'spades']
ranks = {'two' : 2, 'three' : 3 , 'four' : 4, 'five' : 5,
         'six' : 6, 'seven' : 7, 'eight' : 8, 'nine' : 9,
         'ten' : 10, 'jack' : 11, 'queen' : 12, 'king' : 13,
         'ace' : 14 }

deck = [ (rank, suit) for suit in suits for rank in ranks.keys() ]

def hand_is_badugi_generator(seed):
    rng = random.Random(seed)
    for i in range(100000):
        yield (rng.sample(deck, 4),)

def bridge_hand_shape_generator(seed):
    rng = random.Random(seed)
    for i in range(20000):
        yield (rng.sample(deck, 13),)

def winning_card_generator(seed):
    rng = random.Random(seed)
    for i in range(10000):
        hand = rng.sample(deck, 4)
        for trump in ["spades", "hearts", "diamonds", "clubs", None]:
            yield (hand[:], trump)

def hand_shape_distribution_generator(seed):
    rng = random.Random(seed)
    hands = [rng.sample(deck, 13) for i in range(10000)]
    yield [hands]

def milton_work_point_count_generator(seed):
    rng = random.Random(seed)
    strains = suits + ['notrump']
    for i in range(10000):
        hand = rng.sample(deck, 13)
        for strain in strains:
            yield (hand, strain)

def sort_by_typing_handedness_generator():
    f = open('words_sorted.txt', 'r', encoding='utf-8')
    words = [x.strip() for x in f]
    f.close()
    yield [words]

def possible_words_generator(seed):
    f = open('words_sorted.txt', 'r', encoding='utf-8')
    words = [x.strip() for x in f]
    f.close()
    rng = random.Random(seed)
    letters = 'abcdefghijklmnopqrstuvwxyz'
    for i in range(100):
        k = rng.randint(1, 10)
        guessed = set(rng.sample(letters, k))
        patword = rng.choice(words)
        pat = ''
        for ch in patword:
            pat += ch if ch in guessed else '*'
        yield (words, pat)

def postfix_evaluate_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        exp = []
        count = 0
        while len(exp) < 5 or count != 1:
            if count > 1 and (count > 10 or rng.randint(0, 99) < 50):
                exp.append(rng.choice(['+', '-', '*', '/']))
                count -= 1
            else:
                exp.append(rng.randint(1, 10))
                count += 1
        yield (exp, )

def __create_list(d, rng):
    if d < 1:
        return rng.randint(1, 100)
    else:
        n = rng.randint(0, 10 - d)
        return [__create_list(d - rng.randint(1, 3), rng) for i in range(n)]

def reverse_reversed_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        items = __create_list(1 + (i % 8), rng)
        yield (items, )


def scrabble_value_generator(seed):
    rng = random.Random(seed)
    f = open('words_sorted.txt', 'r', encoding='utf-8')
    words = [x.strip() for x in f]
    f.close()
    for word in words:
        multipliers = [rng.randint(1, 3) for i in range(len(word))]
        yield (word, multipliers if rng.randint(0, 99) < 50 else None)

def expand_intervals_generator(seed):
    rng = random.Random(seed)
    for j in range(1000):
        curr = 0
        result = ''
        first = True
        n = rng.randint(1, 20)
        for i in range(n):
            if not first:
                result += ','
            first = False
            if rng.randint(0, 99) < 20:
                result += str(curr)
                curr += rng.randint(1, 10)
            else:
                end = curr + rng.randint(1, 30)
                result += str(curr) + '-' + str(end)
                curr = end + rng.randint(1, 10)
        yield (result,)

def collapse_intervals_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        items = []
        curr = 1
        n = rng.randint(1, i + 3)
        for j in range(n):
            m = rng.randint(1, 5)
            for k in range(m):
                items.append(curr)
                curr += 1
            curr += rng.randint(1, 10)
        yield (items,)

def recaman_generator():
    yield (1000000,)

def __no_repeated_digits(n, allowed):
    n = str(n)
    for i in range(4):
        if n[i] not in allowed:
            return False
        for j in range(i+1, 4):
            if n[i] == n[j]:
                return False
    return True

def bulls_and_cows_generator(seed):
    rng = random.Random(seed)
    for i in range(100):
        result = []
        n = rng.randint(1, 4)
        allowed = rng.sample('123456789', 6)
        while len(result) < n:
            guess = rng.randint(1000, 9999)
            if __no_repeated_digits(guess, allowed):
                bulls = rng.randint(0, 3)
                cows = rng.randint(0, 3)
                cows = min(cows, 4 - bulls)
                if not(bulls == 3 and cows == 1):
                    result.append( (guess, bulls, cows) )
        yield (result,)

def contains_bingo_generator(seed):
    rng = random.Random(seed)
    nums = range(1, 99)
    for i in range(10000):
        card = rng.sample(nums, 25)
        card = [card[i:i+5] for i in range(0, 25, 5)]
        m = rng.randint(20, 80)
        numbers = rng.sample(nums, m)
        numbers.sort()
        centerfree = [True, False][rng.randint(0,1)]
        yield (card, numbers, centerfree)

def can_balance_generator(seed):
    rng = random.Random(seed)
    for i in range(500):
        for j in range(10):
            left, lm = [], 0
            right = [rng.randint(1, i + 2)]
            rm = right[0]
            while lm != rm and lm + rm < 20 * (i+3):
                v = rng.randint(1, i + 5)
                s = rng.randint(0, 1)
                if len(left) + len(right) > i + j + 3:
                    if lm < rm:
                        s, v = 0, (rm - lm) // (len(left) + 1)
                    else:
                        s, v = 1, (lm - rm) // (len(right) + 1)
                v = max(v, 1)
                if s == 0:
                    left.append(v)
                    lm += v * len(left)
                else:
                    right.append(v)
                    rm += v * len(right)
            yield (left[::-1] + [rng.randint(1, i+2)] + right,)


def calkin_wilf_generator():
    for v in [10, 42, 255, 987, 7654, 12356]:
        yield (v,)

def fibonacci_sum_generator(seed):
    for v in it.islice(scale_random(seed, 2, 4), 1500):
        yield (v,)

def create_zigzag_generator(seed):
    rng = random.Random(seed)
    for i in range(10000):
        rows = rng.randint(1, 20)
        cols = rng.randint(1, 20)
        start = rng.randint(1, 100)
        yield (rows, cols, start)

def fibonacci_word_generator(seed):
    for v in it.islice(scale_random(seed, 3, 6), 2000):
        yield (v,)

def all_cyclic_shifts_generator():
    f = open('words_sorted.txt', 'r', encoding='utf-8')
    words = [x.strip() for x in f]
    f.close()
    for word in words:
        yield (word,)

def aliquot_sequence_generator():
    for i in range(1, 100):
        yield (i, 10)
        yield (i, 100)

def josephus_generator():
    for n in range(2, 100):
        for k in range(1, n):
            yield (n, k)

def balanced_ternary_generator(seed):
    for v in it.islice(scale_random(seed, 3, 10), 2000):
        yield (v,)
        yield (-v,)

__names = ["brad", "ben", "britain", "donald", "bill", "ronald",
             "george", "laura", "barbara",
             "barack", "angelina", "jennifer", "ross", "rachel",
             "monica", "phoebe", "joey", "chandler",
             "hillary", "michelle", "melania", "nancy", "homer",
             "marge", "bart", "lisa", "maggie", "waylon", "montgomery",
             "california", "canada", "germany", "sheldon", "leonard",
             "rajesh", "howard", "penny", "amy", "bernadette"]

def brangelina_generator():
    for n1 in __names:
        for n2 in __names:
            yield (n1, n2)

def frequency_sort_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        n = 2 * i
        elems = [rng.randint(1, 2 + n // 2) for x in range(n)]
        yield (elems,)

def count_consecutive_summers_generator():
    for i in range(1, 1000):
        yield (i,)

def detab_generator(seed):
    rng = random.Random(seed)
    for (line,) in random_text_generator(seed):
        line = line.replace(' ', '\t')
        n = rng.randint(1, 7)
        yield (line, n, ' ')

def running_median_of_three_generator(seed):
    rng = random.Random(seed)
    yield ([],)
    yield ([42],)
    for i in range(500):
        n = i + 2
        items = [rng.randint(1, n) for x in range(n)]
        yield (items,)

def iterated_remove_pairs_generator(seed):
    rng = random.Random(seed)
    for k in range(1000):
        n = rng.randint(0, 100)
        vals = [rng.randint(1, 10000) for i in range(7)]
        items = [vals[rng.randint(0, 6)] for i in range(n)]
        yield (items,)

def is_perfect_power_generator(seed):
    rng = random.Random(seed)
    for k in range(500):
        base = rng.randint(2, 3 + k // 20)
        exp = rng.randint(2, 3 + k // 20)
        off = rng.randint(-1, 1)
        yield (base ** exp - off, )

def sort_by_digit_count_generator(seed):
    rng = random.Random(seed)
    for k in range(1000):
        n = k + 2
        yield ([rng.randint(1, n * n * n * n) for i in range(n)],)

def count_divisibles_in_range_generator(seed):
    prev = 0
    vals = it.islice(scale_random(seed, 2, 6), 1000)
    divs = it.islice(scale_random(seed, 2, 20), 1000)
    for (v, k) in zip(vals, divs):
        yield (prev, v, k)
        prev = v

__players = ['anita', 'suzanne', 'suzy', 'tom', 'steve', 'ilkka', 'rajesh',
             'amy', 'penny', 'sheldon', 'leonard', 'bernadette', 'howard']

def highest_n_scores_generator(seed):
    rng = random.Random(seed)
    for i in range(10000):
        scores = [(name, rng.randint(1, 100)) for name in __players\
                  for k in range(rng.randint(0, 20))]
        n = rng.randint(1, 10)
        yield (scores, n)

def bridge_hand_shorthand_generator(seed):
    rng = random.Random(seed)
    for i in range(10000):
        yield (rng.sample(deck, 13),)

def losing_trick_count_generator(seed):
    rng = random.Random(seed)
    for i in range(10000):
        yield (rng.sample(deck, 13),)

def prime_factors_generator(seed):
    for v in it.islice(scale_random(seed, 2, 30), 500):
        yield (v,)

def factoring_factorial_generator(seed):
    for v in it.islice(scale_random(seed, 2, 10), 100):
        yield (v,)

def riffle_generator(seed):
    for i in range(100):
        n = 1 + i
        items = list(range(2 * n))
        yield (items[:], True)
        yield (items, False)

def words_with_given_shape_generator(seed):
    rng = random.Random(seed)
    f = open('words_sorted.txt', 'r', encoding='utf-8')
    words = [x.strip() for x in f]
    f.close()
    for i in range(100):
        n = rng.randint(5, 10)
        pattern = [rng.randint(-1, 1) for j in range(n)]
        yield (words, pattern)

def squares_intersect_generator(seed):
    rng = random.Random(seed)
    for i in range(100000):
        x1 = rng.randint(1, 10)
        y1 = rng.randint(1, 10)
        d1 = rng.randint(1, 10)
        x2 = rng.randint(1, 10)
        y2 = rng.randint(1, 10)
        d2 = rng.randint(1, 10)
        s = 10 ** rng.randint(1, 2 + i // 10000)
        yield ((s*x1, s*y1, s*d1), (s*x2, s*y2, s*d2))

def only_odd_digits_generator(seed):
    rng = random.Random(seed)
    for i in range(3000):
        n = rng.randint(0, 9)
        p = 1
        stop = False
        for j in range(1 + i // 10):
            yield (n,)
            yield (n+p, )
            p = p * 10
            if stop:
                break
            if rng.randint(0, 99) < 95:
                n = 10 * n + rng.choice([1, 3, 5, 7, 9])
            else:
                n = 10 * n + rng.choice([0, 2, 4, 6, 8])
                stop = True

def pancake_scramble_generator(seed):
    rng = random.Random(seed)
    f = open('words_sorted.txt', 'r', encoding='utf-8')
    words = [x.strip() for x in f]
    f.close()
    for i in range(10000):
        word = rng.choice(words)
        yield (word,)

def lattice_paths_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        x = rng.randint(2, 3 + i // 40)
        y = rng.randint(2, 3 + i // 40)
        tabu = []
        n = rng.randint(1, max(1, x*y // 10))
        while len(tabu) < n:
            xx = rng.randint(0, x)
            yy = rng.randint(0, y)
            if (xx, yy) not in tabu:
                tabu.append((xx, yy))
        yield (x, y, tabu)

def count_carries_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        b1 = rng.randint(2, 3 + i // 500)
        e1 = rng.randint(2, i + 3)
        b2 = rng.randint(2, 3 + i // 500)
        e2 = rng.randint(2, i + 3)
        yield (b1**e1, b2**e2)

def count_squares_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        pts = set()
        w = rng.randint(3, 4 + i // 50)
        h = rng.randint(3, 4 + i // 50)
        n = rng.randint(1, (w * h) // 3)
        while len(pts) < n:
            x = rng.randint(0, w)
            y = rng.randint(0, h)
            pts.add((x, y))
        yield(list(pts), )

def kempner_generator():
    for i in range(1, 1000, 10):
        yield (i,)

def tribonacci_generator():
    for i in range(1000):
        yield (i, (1, 1, 1))
        yield (i, (1, 0, 1))
        yield (i, (1, 2, 3))

def is_permutation_generator(seed):
    rng = random.Random(seed)
    for n in range(1, 1000):
        items = rng.sample([i for i in range(1, n + 1)], n)
        yield (items, n)
        m = rng.randint(1, 5)
        for i in range(m):
            j = rng.randint(0, n - 1)
            v = items[j]
            if rng.randint(0, 99) < 50:
                k = rng.randint(0, n - 1)
                items[j] = items[k]
            else:
                items[j] = n + 1
            yield (items[:], n)
            items[j] = v

def three_summers_generator(seed):
    rng = random.Random(seed)
    for i in range(100):
        n = rng.randint(3, 20)
        items = [rng.randint(1, 10)]
        for i in range(1, n):
            items.append(items[-1] + rng.randint(1, 20))
        for goal in range(1, sum(items)):
            yield (items[:], goal)

def first_missing_positive_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        n = rng.randint(10, 1000)
        items = [rng.randint(1, 2*n) for i in range(n)]
        rng.shuffle(items)
        yield (items,)

def ztalloc_generator(seed):
    rng = random.Random(seed)
    for i in range(50000):
        if rng.randint(0, 99) < 50:
            c = rng.randint(1, 2 + 10 * i)
            pat = []
            while c > 1:
                if c % 2 == 0:
                    c = c // 2
                    pat.append('d')
                else:
                    c = 3 * c + 1
                    pat.append('u')
        else:
            len_ = rng.randint(1, 100)
            pat = [('u' if (rng.randint(0, 99) < 50) else 'd') for j in range(len_)]
            pat.extend(['d', 'd', 'd', 'd'])
        yield (''.join(pat), )

def sum_of_two_squares_generator(seed):
    for v in it.islice(scale_random(seed, 2, 5), 150):
        yield (v,)

def sum_of_distinct_cubes_generator(seed):
    for v in it.islice(scale_random(seed, 2, 5), 200):
        yield (v,)

def count_distinct_sums_and_products_generator(seed):
    rng = random.Random(seed)
    for n in range(200):
        items = [rng.randint(1, 10)]
        for i in range(n):
            items.append(items[-1] + rng.randint(1, 10))
        yield (items, )

def seven_zero_generator():
    for n in range(2, 501):
        yield (n,)

def remove_after_kth_generator(seed):
    rng = random.Random(seed)
    for i in range(200):
        items = []
        nn = rng.randint(0, i + 3)
        for k in range(nn):
            n = rng.randint(1, 2 + i // 10)
            m = rng.randint(1, 30)
            items.extend([n] * m)
        rng.shuffle(items)
        for k in range(1, 20):
            yield(items[:], k)

def __key_dist():
    top = { c:(0,i) for (i, c) in enumerate("qwertyuiop") }
    mid = { c:(1,i) for (i, c) in enumerate("asdfghjkl") }
    bot = { c:(2,i) for (i, c) in enumerate("zxcvbnm")}
    keys = dict(top, **mid, **bot)
    dist = dict()
    for cc1 in "abcdefghijklmnopqrstuvwxyz":
        for cc2 in "abcdefghijklmnopqrstuvwxyz":
            (r1, c1) = keys[cc1]
            (r2, c2) = keys[cc2]
            dist[(cc1, cc2)] = (abs(r2 - r1) + abs(c2 - c1))
    return dist

def autocorrect_word_generator(seed):
    f = open('words_sorted.txt', 'r', encoding='utf-8')
    words = [x.strip() for x in f]
    f.close()
    dist = __key_dist()
    df = lambda c1, c2: dist[(c1, c2)]
    rng = random.Random(seed)
    for i in range(30):
        word = rng.choice(words)
        for k in range(3):
            p = rng.randint(0, len(word) - 1)
            c = word[p]
            neighbours = [nc for nc in "abcdefghijklmnopqrstuvwxyz" if df(c, nc) == 1]
            word = word[:p] + rng.choice(neighbours) + word[p+1:]
            yield (word, words, df)

def pyramid_blocks_generator(seed):
    n = 300
    ns = it.islice(scale_random(seed, 3, 10), n)
    ms = it.islice(scale_random(seed + 1, 3, 10), n)
    hs = it.islice(scale_random(seed + 2, 2, 15), n)
    yield from zip(ns, ms, hs)

def is_cyclops_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        d = rng.randint(1, i + 3)
        m = d // 2
        n = 0
        for j in range(d):
            n = 10 * n
            if j == m:
                if rng.randint(0, 99) < 20:
                    n += rng.randint(1, 9)
            elif rng.randint(0, 99) < 99:
                n += rng.randint(1, 9)
        yield (n,)

def words_with_letters_generator(seed):
    rng = random.Random(seed)
    f = open('words_sorted.txt', 'r', encoding='utf-8')
    words = [x.strip() for x in f]
    f.close()
    count = 0
    while count < 30:
        word = rng.choice(words)
        if len(word) > 7:
            n = len(word) - 3
            pos = rng.sample(range(len(word)), n)
            pos.sort()
            letters = ''.join([word[i] for i in pos])
            yield (words, letters)
            count += 1

def extract_increasing_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        n = rng.randint(i, i + 10)
        digits = "".join([rng.choice("0123456789") for j in range(n)])
        yield (digits,)

def square_follows_generator(seed):
    def emit():
        rng = random.Random(seed)
        curr = 1
        step = 3
        for i in range(10**6):
            yield curr
            curr += rng.randint(2, step)
            step += 1
    yield (emit(),)

def line_with_most_points_generator(seed):
    rng = random.Random(seed)
    for n in range(2, 100):
        pts = set()
        while len(pts) < n:
            sx = rng.randint(1, n)
            sy = rng.randint(1, n)
            dx = rng.randint(-10, 10)
            dy = rng.randint(-10, 10)
            for i in range(rng.randint(1, 10)):
                pts.add((sx, sy))
                step = rng.randint(1, 10)
                sx, sy = sx + step * dx, sy + step * dy
        pts = list(pts)
        pts.sort()
        yield (pts,)

def count_maximal_layers_generator(seed):
    rng = random.Random(seed)
    for i in range(300):
        n = 3 + i
        points = set()
        while len(points) < n:
            x = rng.randint(1, 3 + n)
            y = rng.randint(1, 3 + n)
            points.add((x, y))
        points = list(points)
        points.sort()
        yield (points,)

def taxi_zum_zum_generator(seed):
    rng = random.Random(seed)
    poss = ['L', 'R', 'F']
    for i in range(1000):
        moves = []
        for j in range(i + 1):
            moves.append(rng.choice(poss))
        yield (''.join(moves),)

def count_growlers_generator(seed):
    rng = random.Random(seed)
    poss = ["cat", "tac", "dog", "god"]
    for i in range(1000):
        animals = []
        for j in range(i + 1):
            animals.append(rng.choice(poss))
        yield (animals,)

def tukeys_ninthers_generator(seed):
    rng = random.Random(seed)
    for i in range(200):
        items = [x for x in range(3**(1 + i % 9))]
        rng.shuffle(items)
        yield (items,)

def minimize_sum_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        n = 1 + i % 20
        s = ''
        for i in range(n):
            s += rng.choice("0123456789")
        for k in range(1, n + 1):
            yield (s, k)

def bridge_score_generator():
    for suit in ['clubs', 'hearts', 'spades', 'notrump']:
        for level in range(1, 8):
            for vul in [False, True]:
                for dbl in ['', 'X', 'XX']:
                    for made in range(level, 8):
                        yield (suit, level, vul, dbl, made)

def max_checkers_capture_generator(seed):
    rng = random.Random(seed)
    for i in range(20):
        n = 3 + i
        pieces = set()
        for j in range(1, (n * n) // 3):
            while len(pieces) < j:
                px = rng.randint(0, n-1)
                py = rng.randint(0, n-1)
                pieces.add((px, py))
            for x in range(n):
                for y in range(n):
                    if (x, y) not in pieces:
                        yield (n, x, y, pieces)

def collatzy_distance_generator():
    for i in range(1, 101):
        for j in range(1, 101):
            yield (i, j)

def nearest_smaller_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        items = []
        for j in range(i):
            items.append(rng.randint(1, 2 * i))
        yield (items,)

def double_trouble_generator(seed):
    items = ['joe', 'bob', 42, 99]
    rng = random.Random(seed)
    curr, step = 1, 1
    for i in range(200):
        yield (items[:], curr)
        curr += rng.randint(1, step)
        step = step * 2
        items.append(items[-1] + 1)

def domino_cycle_generator(seed):
    rng = random.Random(seed)
    for i in range(10000):
        tiles = []
        cycle = rng.randint(0, 99) < 50
        for j in range(10):
            yield (tiles[:],)
            if cycle or rng.randint(0, 99) < 90:
                if len(tiles) > 0:
                    a = tiles[-1][-1]
                else:
                    a = rng.randint(1, 6)
            else:
                a = rng.randint(1, 6)
            tiles.append((a, rng.randint(1, 6)))

def van_eck_generator():
    curr = 1
    for i in range(23):
        yield (curr,)
        curr = 2 * curr

def suppressed_digit_sum_generator(seed):
    rng = random.Random(seed)
    curr = 1
    for i in range(500):
        yield (curr,)
        curr = 10 * curr + rng.randint(0, 9)

def unscramble_generator(seed):
    rng = random.Random(seed)
    f = open('words_sorted.txt', 'r', encoding='utf-8')
    words = [x.strip() for x in f]
    f.close()
    count = 0
    while count < 500:
        w = rng.choice(words)
        if len(w) > 2 and len(w) < 9:
            first, mid, last = w[0], list(w[1:-1]), w[-1]
            rng.shuffle(mid)
            yield (words, first + "".join(mid) + last)
            count += 1

def crag_score_generator():
    for d1 in range(1, 7):
        for d2 in range(1, 7):
            for d3 in range(1, 7):
                yield ([d1, d2, d3], )

def midnight_generator(seed):
    rng = random.Random(seed)
    for i in range(200):
        dice = []
        for j in range(6):
            rolls = []
            for k in range(6):
                if rng.randint(1, 100) < 90:
                    rolls.append(rng.choice((2,2,2,3,3,5,6)))
                else:
                    rolls.append(rng.choice((1,4)))
            dice.append(rolls)
        yield (dice,)

from math import sqrt

ups = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def substitution_words_generator(seed):
    rng = random.Random(seed)
    f = open('words_sorted.txt', 'r', encoding='utf-8')
    words = [x.strip() for x in f]
    f.close()
    yield ('ABCD', words)
    for i in range(100):
        pat = ''
        ll = int(sqrt(rng.randint(3*3, 10*10)))
        n = rng.randint(1, ll)
        for j in range(ll):
            pat += ups[rng.randint(0, n - 1)]
        yield (pat, words)

def forbidden_substrings_generator(seed):
    rng = random.Random(seed)
    for i in range(100):
        tabu = []
        n = rng.randint(3, 7)
        nn = rng.randint(2, n)
        for j in range(rng.randint(1, n)):
            pat = ''
            for k in range(rng.randint(2, n)):
                pat += ups[rng.randint(0, nn - 1)]
            tabu.append(pat)
        tabu = list(set(tabu))
        yield (ups[:nn], n, tabu)

def count_dominators_generator(seed):
    rng = random.Random(seed)
    items = []
    top = 10000
    for i in range(top):
        yield (items[:],)
        items.append(rng.randint(1, 10 * (top - i)))

def optimal_crag_score_generator(seed):
    rng = random.Random(seed)
    for i in range(30):
        rolls = []
        for j in range(2 + (i % 7)):
            dice = tuple([rng.randint(1, 6) for k in range(3)])
            rolls.append(dice)
        yield (rolls,)

def count_distinct_lines_generator(seed):
    rng = random.Random(seed)
    for i in range(100):
        n = 3 + i
        points = set()
        for j in range(n):
            x = rng.randint(1, n*n)
            y = rng.randint(1, n*n)
            points.add((x, y))
        yield (list(points),)

def bulgarian_solitaire_generator(seed):
    rng = random.Random(seed)
    for k in range(2, 30):
        for i in range(5):
            result, total = [], (k*(k+1))//2
            while total > 0:
                p = rng.randint(1, total)
                result.append(p)
                total -= p
            result.sort(reverse = True)
            yield(result, k)

def manhattan_skyline_generator(seed):
    rng = random.Random(seed)
    for i in range(200):
        towers = []
        w = i * i + 1
        for k in range(i):
            s = rng.randint(1, w)
            e = s + rng.randint(1, w)
            h = rng.randint(1, 100)
            towers.append((s, e, h))
        yield(towers,)

def fractran_generator(seed):
    rng = random.Random(seed)
    conway = [(17, 91), (78, 85), (19, 51), (23, 38), (29, 33), (77, 29),
              (95, 23), (77, 19), (1, 17), (11, 13), (13, 11), (15, 2),
              (1, 7), (55, 1)]
    for n in range(2, 100):
        yield(n, conway[:], 100)
    for i in range(10):
        for j in range(10):
            prog = []
            for k in range(2, i + j):
                num = rng.randint(1, 100)
                den = rng.randint(1, 100)
                prog.append((num, den))
            n = rng.randint(2, 10)
            yield (n, prog, 30)

def scylla_or_charybdis_generator(seed):
    rng = random.Random(seed)
    for n in range(2, 10):
        for i in range(200):
            pos, result, = 0, ''
            for j in range(n * i):
                if pos == n - 1:
                    move = '-'
                elif pos == -n + 1:
                    move = '+'
                elif pos == 0:
                    move = rng.choice('+-')
                elif pos < 0:
                    move = rng.choice('++-')
                else:
                    move = rng.choice('--+')
                result += move
                pos += 1 if move == '+' else -1
            # Ensure success with k == 1, if nothing else.
            result += ('+' * (n + n))
            yield (result, n)

def fractional_fit_generator(seed):
    rng = random.Random(seed+1)
    for n in range(3, 12):
        for j in range(n*n):
            fs = []
            for i in range(n + 1):
                a = rng.randint(0, n*n)
                b = rng.randint(a + 1, n*n + 3)
                fs.append((a, b))
            yield (fs,)

def count_overlapping_disks_generator(seed):
    rng = random.Random(seed)
    for n in range(3, 150):
        d = 2 * n
        for i in range(10):
            disks = set()
            while len(disks) < n:
                x = rng.randint(-d, d)
                y = rng.randint(-d, d)
                r = rng.randint(1, n)
                disks.add((x, y, r))
            disks = list(disks)
            disks.sort()
            yield (disks,)

def sublist_with_mostest_generator(seed):
    rng = random.Random(seed)
    for n in range(11, 80):
        items, step = [rng.randint(1, 10)], 2
        for j in range(n):
            items.append(items[-1] + rng.randint(1, step))
            if j % 5 == 0:
                step += rng.randint(1, 5)
        for k in range(9, n // 2):
            yield (items[:], k)

def arithmetic_progression_generator(seed):
    rng = random.Random(seed)
    m = 5
    for i in range(300):
        elems = set()
        for j in range(m):
            start = rng.randint(1, i*i + 3)
            step = rng.randint(1, 100)
            n = rng.randint(1, 10)
            for k in range(n):
                elems.add(start + k * step)
        yield (sorted(list(elems)), )
        if i % 10 == 0:
            m += 1

def connected_islands_generator(seed):
    rng = random.Random(seed)
    for n in range(6, 100):
        for m in range(n // 2, n):
            bridges = set()
            while len(bridges) < m:
                s = rng.randint(0, n-1)
                e = rng.randint(0, n-1)
                if s != e:
                    bridges.add((s, e))
            bridges = list(bridges)
            queries = []
            while len(queries) < n:
                s = rng.randint(0, n-1)
                e = rng.randint(0, n-1)
                if s != e:
                    queries.append((s, e))
            yield (n, bridges, queries)

def cookie_generator(seed):
    rng = random.Random(seed)
    for i in range(30):
        items = [rng.randint(1, 50)]
        for j in range(3 + i % 7):
            items.append(items[-1] + rng.randint(1, 50))
        yield (items,)

def eliminate_neighbours_generator(seed):
    rng = random.Random(seed)
    items = []
    for i in range(1, 3000):
        items.append(i)
        rng.shuffle(items)
        yield (items[:], )

def counting_series_generator(seed):
    rng = random.Random(seed)
    curr, step = 0, 2
    for i in range(1000):
        yield (curr,)
        curr += rng.randint(1, step)
        step = step * 2

def __zigzag(rng, len_, prob):
    curr = rng.randint(1, 8)
    d = rng.choice([+1, -1])
    for k in range(len_):
        last = curr % 10
        dd = d if rng.randint(1, 100) < prob else -d
        if dd == +1 and last > 0:
            n = rng.randint(0, last - 1)
        elif dd == -1 and last < 9:
            n = rng.randint(last + 1, 9)
        else:
            n = rng.randint(0, 9)
        curr = curr * 10 + n
        d = -d
    return curr

def is_zigzag_generator(seed):
    rng = random.Random(seed)
    for i in range(100):
        for j in range(20):
            curr = __zigzag(rng, j, 10)
            yield (curr, )

def next_zigzag_generator(seed):
    rng = random.Random(seed)
    for k in range(100):
        for i in range(100):
            curr = rng.randint(1, 8)
            d = rng.choice([+1, -1])
            last = 0
            for j in range(i):
                last = curr % 10
                if d == -1:
                    n = rng.randint(last + 1, 9)
                else:
                    n = rng.randint(0, last - 1)
                curr = 10 * curr + n
                d = -d
            if d == -1 and last < 8:
                n = rng.randint(1, 10)
                curr = int(str(curr) + ("98" * n))
            elif d == +1 and last == 9:
                n = rng.randint(1, 10)
                curr = int(str(curr) + ("89" * n))
            yield (curr,)

__primes = [2, 3, 5, 7, 11, 13]
def md_generator(seed):
    rng = random.Random(seed)
    for i in range(1000):
        (a, b) = rng.sample(__primes, 2)
        yield (a, b, i + 2)
        b = rng.randint(1, 10) * 2 + 1
        yield (2, b, i + 2)

def wythoff_array_generator(seed):
    rng = random.Random(seed)
    curr, step = 1, 1
    for i in range(300):
        yield (curr, )
        curr += rng.randint(1, step)
        step += 1

def hourglass_flips_generator(seed):
    rng = random.Random(seed)
    for i in range(30):
        glasses, curr = [], rng.randint(3, 20)
        n = rng.randint(2, 5)
        for j in range(n):
            glasses.append((curr, 0))
            curr += rng.randint(1, 5)
        t = rng.randint(curr + 1, 2 * curr)
        yield (glasses, t)

def knight_jump_generator(seed):
    rng = random.Random(seed)
    for i in range(10000):
        k = 2 + (i % 50)
        steps = [1]
        for j in range(1, k):
            steps.append(steps[-1] + rng.randint(1, 5))
        start = [rng.randint(10, 20) for j in range(k)]
        rng.shuffle(steps)
        end = [x + y * rng.choice([-1, 1]) for (x, y) in zip(start, steps)]
        if rng.randint(1, 100) < 50:
            end[rng.randint(0, k - 1)] += 1
        steps.sort(reverse = True)
        yield (tuple(steps), tuple(start), tuple(end))

def frog_collision_time_generator(seed):
    rng = random.Random(seed)
    count = 0
    while count < 5000:
        c = [rng.randint(-10, 10) for i in range(6)]
        if c[2:4] == c[4:6] or c[2:4] == [0, 0] or c[4:6] == [0, 0]:
            continue
        t = rng.randint(1, 2 + 2**(count // 100))
        x1, y1 = c[0] + t * c[2], c[1] + t * c[3]
        x2, y2 = c[0] + t * c[4], c[1] + t * c[5]
        if rng.randint(1, 100) < 30:
            if rng.randint(1, 100) < 50:
                x1 += rng.choice([-10, 10])
            else:
                y1 += rng.choice([-10, 10])
        elif rng.randint(1, 100) < 10:
            c[2], c[3] = -c[2], -c[3]
        if (x1, x2) != (y1, y2):
            yield ((x1, y1, -c[2], -c[3]), (x2, y2, -c[4], -c[5]))
            count += 1

def spread_the_coins_generator(seed):
    rng = random.Random(seed)
    for i in range(2, 500):
        n = 10 + rng.randint(1, 2 + 2**(i//25))
        piles, nn = [], n
        while nn > 1:
            c = rng.randint(nn // 3, nn)
            piles.append(c)
            nn -= c
        u = rng.randint(5, n // 2)
        a = rng.randint(1, u - 1)
        b = u - a
        yield (piles, a, b)


def group_and_skip_generator(seed):
    rng = random.Random(seed)
    for n in range(2000):
        b = rng.randint(1, 10)
        a = 2 * b + rng.randint(1, 10)
        yield (n*n, a, b)

def nearest_polygonal_number_generator(seed):
    rng = random.Random(seed)
    yield from [(1, 10), (1, 100), (1, 10**100)]
    curr = 20
    for i in range(250):
        for j in range(15):
            curr = curr + rng.randint(1, curr // 10)
            s = rng.randint(3, min(curr // 3, 300))
            yield (curr, s)
        curr = curr * 2

def floor_power_solve_generator(seed):
    yield from [(2018, 4), (2011, 4)]
    rng = random.Random(seed)
    curr = 30
    for i in range(140):
        for j in range(10):
            curr = curr + rng.randint(1, curr // 10)
            yield (curr, j + 2)
        curr = curr * 2

def subtract_square_generator(seed):
    rng = random.Random(seed)
    for i in range(1, 9):
        curr = rng.randint(1, 10)
        query = []
        for j in range(4 * i):
            query.append(curr)
            curr = (4 * curr) // 3 + rng.randint(1, max(3, curr // 5))
        yield (query, )

def perimeter_limit_split_generator(seed):
    rng = random.Random(seed)
    for a in range(10, 100):
        for i in range(5):
            b = rng.randint(1, a)
            p = rng.randint(5, 3 * a)
            yield (a, b, p) if rng.randint(0, 1) else (b, a, p)

def duplicate_digit_bonus_generator(seed):
    rng = random.Random(seed);
    m = 1
    for i in range(400):
        n = 0
        if i % 10 == 0:
            m += 1
        for j in range(m):
            if rng.randint(0, 100) < 50:
                run = 1
            else:
                run = rng.randint(1, 6 + m // 10)
            d = rng.randint(0, 9)
            for k in range(run):
                n = 10 * n + d
        yield (n,)

def count_word_dominators_generator(seed):
    f = open('words_sorted.txt', 'r', encoding='utf-8')
    words = [x.strip() for x in f]
    f.close()
    m = 1
    wls = [ [w for w in words if len(w) == n] for n in range(3, 6)]
    rng = random.Random(seed)
    for i in range(1000):
        wl = rng.choice(wls)
        result = rng.sample(wl, m)
        yield (result,)
        result.sort(reverse = True)
        yield (result,)
        if(i % 10 == 4):
            m += 1

def hitting_integer_powers_generator():
    for b in range(3, 20):
        for a in range(2, b):
            yield (a, b, 10**(2 + (a+b) % 3))

def permutation_cycles_generator(seed):
    rng = random.Random(seed)
    yield ([0], )
    for i in range(200):
        n = 2 + i // 10
        for j in range(3 * i):
            perm = list(range(n))
            rng.shuffle(perm)
            yield (perm,)

# List of test cases for the 109 functions defined.

testcases = [
        # The original 109 problems. These are not in order.

        # Removed from problem set April 20, 2020
        # (
        # "connected_islands",
        # connected_islands_generator(seed),
        # "ceafc55f58a4f921582cf6fcd2c856851fca7444541e5024d1"
        # ),
        (
        "arithmetic_progression",
        arithmetic_progression_generator(seed),
        "aaab6fcefc56db92e43609036aa5bf92707f1070cdbcd96181"
        ),
        (
        "count_overlapping_disks",
        count_overlapping_disks_generator(seed),
        "18e8f5385fdc28a755dcad2167790f1177a3f4851760aa4285"
        ),
        (
        "fractional_fit",
        fractional_fit_generator(seed),
        "856627cc444098c9386367d5f250c0e2cddbf3ef0ecec3ba11"
        ),
        (
        "scylla_or_charybdis",
        scylla_or_charybdis_generator(seed),
        "ac773070f2e2a560e487aae218da4d37c287395865d0c44ec7"
        ),
        (
        "fractran",
        fractran_generator(seed),
        "4a5b2e7dee7eec27bdfdfa6748a4df2e4a06343cef38dd4ef1"
        ),
        (
        "manhattan_skyline",
        manhattan_skyline_generator(seed),
        "16609bdb523fae4ff85f8d36ffd1fcfa298bde94b95ca2917c"
        ),
        (
        "bulgarian_solitaire",
        bulgarian_solitaire_generator(seed),
        "187f2c702e6bbf306dcc655534a307e92b230505ea159c7e73"
        ),
        (
        "sum_of_distinct_cubes",
        sum_of_distinct_cubes_generator(seed),
        "d1ed5e8a0688116c7536b01804d09378a13559a0d6a9427ddf"
        ),
        (
        "tukeys_ninthers",
        tukeys_ninthers_generator(seed),
        "921de1acfc8f515bea0680f631bcdca4510d1e7957f3c1d0d1"
        ),
        (
        "optimal_crag_score",
        optimal_crag_score_generator(seed),
        "5eec80a1d286c8d129cbd9444f2bff3776d3e2e4277fb1e329"
        ),
        (
        "count_dominators",
        count_dominators_generator(seed),
        "a45e1faffd22005c1cfdf148e73d039cee2ab187a9bd7bfad3"
        ),
        (
        "forbidden_substrings",
        forbidden_substrings_generator(seed),
        "951cea3c20623874b27017d589c5d7ac1f99ac5af5c3b3f6c1"
        ),
        (
        "substitution_words",
        substitution_words_generator(seed),
        "ce3286c3c0df978b9f8f508476e6f1bcba3dd30cdb35602acf"
        ),
        (
        "taxi_zum_zum",
        taxi_zum_zum_generator(seed),
        "2fb59c4b26bb42d777436fe2826e5faabf0139710d38569c8c"
        ),
        (
        "midnight",
        midnight_generator(seed),
        "92da9d27a992755aa96419d6b0cebede43f9a481b5f21037fe",
        ),
        (
        "crag_score",
        crag_score_generator(),
        "ea62d9694e079b948a8b622c8f6dfd2aeebddeebc59c575721"
        ),
        (
        "unscramble",
        unscramble_generator(seed),
        "5859988a905549959fd6905cc038e0ad214812a6444d702713"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "suppressed_digit_sum",
        # suppressed_digit_sum_generator(seed),
        # "69130744180a37dae42a668f28a3aa95dd53522662e058f2cf"
        # ),
        (
        "van_eck",
        van_eck_generator(),
        "db1a6665205f46d0e80da4e1ff9926d01b33b04112013bdf43"
        ),
        (
        "domino_cycle",
        domino_cycle_generator(seed),
        "a584eae620badb493239fd0bebbfa7c8c17c12b3bc0f53f873"
        ),
        (
        "double_trouble",
        double_trouble_generator(seed),
        "49f103a7ad2c26d800d61e8645f967408a18c37cc6303a9dfc"
        ),
        (
        "nearest_smaller",
        nearest_smaller_generator(seed),
        "b0c97910c2f5b4743d8b8d88b11243f79a612a34bc072f5862"
        ),
        (
        "collatzy_distance",
        collatzy_distance_generator(),
        "f9489bca0de5fc512ea370d7cddd90b04aaa718f105d68441b"
        ),
        (
        "max_checkers_capture",
        max_checkers_capture_generator(seed),
        "a5221ae1753c13f587735ab72dd8551e61d27125aa2b913385"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "bridge_score",
        # bridge_score_generator(),
        # "1d1e3f4be9fec5fd85d87f7dcfa8c9e40b267c4de49672c65f"
        # ),
        # Removed from problem set April 20, 2020
        # (
        # "minimize_sum",
        # minimize_sum_generator(seed),
        # "7e6257c998d5842ec41699b8b51748400a15e539083e5a0a20"
        # ),
        (
        "count_growlers",
        count_growlers_generator(seed),
        "b7f1eb0877888b0263e3b2a923c9735a72347f4d817a0d38b1"
        ),
        (
        "kempner",
        kempner_generator(),
        "dfbf6a28719818c747e2c8e888ff853c2862fa8d99683c0815"
        ),
        (
        "words_with_letters",
        words_with_letters_generator(seed),
        "36cab5129635cc1495f9cff88c4b539a49a40be5585243788c"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "count_distinct_lines",
        # count_distinct_lines_generator(seed),
        # "c79db2f41e798a652e3742ef2a2b29801f0b3e52f4e285aa4e"
        # ),
        (
        "line_with_most_points",
        line_with_most_points_generator(seed),
        "40eab89aca1bfd182e9e2f2d8204306587b94d0cfaef041c36"
        ),
        (
        "count_maximal_layers",
        count_maximal_layers_generator(seed),
        "0e97cb2be56e1adef73a72de8fe0ccf2f4ac391201eb921986"
        ),
        (
        "square_follows",
        square_follows_generator(seed),
        "7b42ad97e654f023efeb0174c76d3f02f42a69615e90af31a3"
        ),
        (
        "extract_increasing",
        extract_increasing_generator(seed),
        "8f6ba301734d90b6a3685ae27b342ac481af80201ac35cd776"
        ),
        (
        "is_cyclops",
        is_cyclops_generator(seed),
        "5ced8d0e69d88367f1ee05f96bf6ea7fad6e1c522d0544b526"
        ),
        (
        "pyramid_blocks",
        pyramid_blocks_generator(seed),
        "e7609cac3f32844e182d296ca757104a9684f335df20558381"
        ),
        (
        "autocorrect_word",
        autocorrect_word_generator(seed),
        "be332e39f5a8a3431e913794d15f14b8a89b1153d89d94946a"
        ),
        (
        "remove_after_kth",
        remove_after_kth_generator(seed),
        "4988a0cea5800a5ffaf72f726388afd99192d04b4578289595"
        ),
        (
        "seven_zero",
        seven_zero_generator(),
        "2cbae9ac1812d155ee34be3f908001b148bdf635109a38981e"
        ),
        (
        "count_distinct_sums_and_products",
        count_distinct_sums_and_products_generator(seed),
        "b75370cf5c3d2c307585937311af34e8a7ad44ea82c032786d"
        ),
        (
        "sum_of_two_squares",
        sum_of_two_squares_generator(seed),
        "93086670c2c63510741e58329a83fe42cc469762ca26c74130"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "scrabble_value",
        # scrabble_value_generator(seed),
        # "b8b08a8a1a5fd687c49c5f7147fd35bc16d4c3ac88328ada64"
        # ),
        (
        "reverse_vowels",
        random_text_generator(seed),
        "06f67d9ccd7f91b25b023d9fccd4d0622195f15f1375da16dc"
        ),
        (
        "riffle",
        riffle_generator(seed),
        "bd3f7e2df596e742e43f3eb1cd80c2e52ca9f20c2b33f69c7d"
        ),
        (
        "ztalloc",
        ztalloc_generator(seed),
        "b6336106ac97b9ec4306c77c7e28775b0e1194e75dd10ee219"
        ),
        (
        "losing_trick_count",
        losing_trick_count_generator(seed),
        "814fa798f0de0d1c847b0622fc21a88047d19e427ebe1d16cf"
        ),
        (
        "postfix_evaluate",
        postfix_evaluate_generator(seed),
        "a9d473505f7a9c8458e6fbb7b3b75a56efabe1a0d3ced3d901"
        ),
        (
        "three_summers",
        three_summers_generator(seed),
        "d9d7f6ab17a31bf37653fb4f8504a39464debdde6fed786bee"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "is_permutation",
        # is_permutation_generator(seed),
        # "13f7265f40b407a6444d007720e680090b7b3c3a7d5c243794"
        # ),
        # Removed from problem set April 20, 2020
        # (
        # "first_missing_positive",
        # first_missing_positive_generator(seed),
        # "826ffa832d321ff26594683b3edb3123b77007f8bfc3893ac1"
        # ),
        # Removed from problem set April 20, 2020
        # (
        # "tribonacci",
        # tribonacci_generator(),
        # "ac64825e938d5a3104ea4662b216285f05a071cde8fd82c6fd"
        # ),
        (
        "count_squares",
        count_squares_generator(seed),
        "69c94bb56d9eff5bc9cdfc4890718606c0a8bdf242c3440d98"
        ),
        (
        "count_carries",
        count_carries_generator(seed),
        "e48e0785704b40e82bc086e6edd86d55aa18fe9d017a6547e7"
        ),
        (
        "lattice_paths",
        lattice_paths_generator(seed),
        "dbca1d47adc5713b65fcb90dd9ddf1d747f521eccf341289a4"
        ),
        (
        "pancake_scramble",
        pancake_scramble_generator(seed),
        "98fb3c9e30908ea6c2654d64d3c68ca2538927be529d75ddfe"
        ),
        (
        "only_odd_digits",
        only_odd_digits_generator(seed),
        "24d656750cff73ad12fa9ff8320bbae662c2fbb5a6f4ece514"
        ),
        (
        "squares_intersect",
        squares_intersect_generator(seed),
        "0ad0e8b2971f3cafc93c37e2bd618e94d66312da64f4bd6755"
        ),
        (
        "rooks_with_friends",
        rooks_with_friends_generator(seed),
        "e9cdb7f319ce483f5196eaa17dcfbab5b01b75551830088a66"
        ),
        (
        "safe_squares_rooks",
        safe_squares_generator(seed),
        "8a84bf052174d613f31b3e402be23ad58e64b51948990a7062"
        ),
        (
        "safe_squares_bishops",
        safe_squares_generator(seed),
        "e6b5cd8e52c82bd96c639cc11c7a6b431cc164ddeaf8e5d313"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "safe_squares_knights",
        # safe_squares_generator(seed),
        # "bcd8b6dba304f322a7789303f8d9256949fba5ef954fbe1665"
        # ),
        # Removed from problem set April 20, 2020
        # (
        # "disemvowel",
        # random_text_generator(seed),
        # "9e81bfae626ddf36655f4d3c2c36208d646eee416c18671ec1"
        # ),
        (
        "count_and_say",
        count_and_say_generator(seed),
        "9a99c40999726ec420a29287304f8ec811d590625fcb69d625"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "maximum_difference_sublist",
        # maximum_difference_sublist_generator(seed),
        # "e0e49c2c4d5ad7580fe42a71a411e8449d84c9bfd2a2b13df3"
        # ),
        (
        "first_preceded_by_smaller",
        first_preceded_by_smaller_generator(seed),
        "40ebe484996f84edb425c1a3ae5d70aa62ad308a09e926622b"
        ),
        (
        "words_with_given_shape",
        words_with_given_shape_generator(seed),
        "96d697cd85e4effa24f659b83b18aa1adf14a1b9e14c02207b"
        ),
        (
        "prime_factors",
        prime_factors_generator(seed),
        "fbb31e68d216d7430c47a3e3ac9eb0d4240ef2ae698eb2ded4"
        ),
        (
        "fibonacci_sum",
        fibonacci_sum_generator(seed),
        "bb13f872b52611a389234d48ad1a19ddea88bedb01ddb08a43"
        ),
        (
        "factoring_factorial",
        factoring_factorial_generator(seed),
        "be5d5249b396c259bde5338de73ae4d29831314d6c0fb9e369"
        ),
        (
        "bridge_hand_shorthand",
        bridge_hand_shorthand_generator(seed),
        "68459ff71e28b24e43df3f632706fabcda7403359d7d4d9255"
        ),
        (
        "milton_work_point_count",
        milton_work_point_count_generator(seed),
        "5694509170df1fef10bbb60641b7906e220d951b73d3072f7e"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "highest_n_scores",
        # highest_n_scores_generator(seed),
        # "978ce1599544e991c1cdc5824a762ffbed54ebcee76ca87821"
        # ),
        (
        "count_divisibles_in_range",
        count_divisibles_in_range_generator(seed),
        "4c3246091a84e8b3310c8c9bff017d2fab854e2248a05fab30"
        ),
        (
        "sort_by_digit_count",
        sort_by_digit_count_generator(seed),
        "15112b8c5374e1ebcf8d67bf391f3528c29a3ac3ece70ac5c1"
        ),
        (
        "is_perfect_power",
        is_perfect_power_generator(seed),
        "31baeffbf7aac8f1506fb1c4f70236abc5adc902e1a564724a"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "iterated_remove_pairs",
        # iterated_remove_pairs_generator(seed),
        # "f3d6588ec3c251abfc024698c2a7371dcc7e175af1e41bb0aa"
        # ),
        (
        "detab",
        detab_generator(seed),
        "7e1453906bc31dfb59159a377dcb7dbb8451e464b88bfd04b4"
        ),
        (
        "running_median_of_three",
        running_median_of_three_generator(seed),
        "62d8c78ec1a5a7bdc9e30655380f59f59a64daacc8a272a29b"
        ),
        (
        "frequency_sort",
        frequency_sort_generator(seed),
        "540f8b17005ed2cb3a40c49304eeb324e9aa0db81adf830bd0"
        ),
        (
        "count_consecutive_summers",
        count_consecutive_summers_generator(),
        "3ade63a194b40ff5aa1b53642eee754d30f2ab48ef77330540"
        ),
        (
        "brangelina",
        brangelina_generator(),
        "fdbbfd7aa2ebcb989862f4e23defc6cafd4aca55ce3235a463"
        ),
        (
        "balanced_ternary",
        balanced_ternary_generator(seed),
        "842084fa88061721ede89bef0e1fef414b55fceb580e3d1735"
        ),
        (
        "josephus",
        josephus_generator(),
        "3ff6a944f6f48e41cc53a7013e785da77be27c7372b4a4cdbb"
        ),
        (
        "aliquot_sequence",
        aliquot_sequence_generator(),
        "5942bb5b3dc190eaddff33df990de03666441706387cde0d7e"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "all_cyclic_shifts",
        # all_cyclic_shifts_generator(),
        # "1d06f1ef0547d8441800f2dc19aa430396a0f2e8bc414e6775"
        # ),
        (
        "fibonacci_word",
        fibonacci_word_generator(seed),
        "b6385c1cb1a88f2392f507cae3bc302c468d5747af8802e410"
        ),
        (
        "create_zigzag",
        create_zigzag_generator(seed),
        "e3376a7132fe7ed1b04f38215dea836d70e8cf8d0e316868cf"
        ),
        (
        "calkin_wilf",
        calkin_wilf_generator(),
        "e5ff0851c0830b72802a818eeaec66711b6e3b91a004263674"
        ),
        (
        "can_balance",
        can_balance_generator(seed),
        "6d06001694009cde7c976c645acc39da4e24142e7aca3c24af"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "contains_bingo",
        # contains_bingo_generator(seed),
        # "c352ce01918d0d47ca13adedf25556e5fd4ab1f672e07bc52f"
        # ),
        (
        "bulls_and_cows",
        bulls_and_cows_generator(seed),
        "e00ca4cd1996a51ef5cd5588a7facd0a00f2e3f3946d5f4e96"
        ),
        (
        "recaman",
        recaman_generator(),
        "48f7b14610fe8f54ab2b1d81265847eec47d450d13e4a4c6c5"
        ),
        (
        "collapse_intervals",
        collapse_intervals_generator(seed),
        "36e0b7bcddde70272108b2f7daeb504d71edee1146b7a1a5d0"
        ),
        (
        "expand_intervals",
        expand_intervals_generator(seed),
        "9fecebbd937380814f804508ed3f491a6a0c353050e60a3d60"
        ),
        (
        "reverse_ascending_sublists",
        reverse_ascending_sublists_generator(seed),
        "b4cbb1ed5006364e68d8875e733abeec1241165d7b84402f62"
        ),
        (
        "reverse_reversed",
        reverse_reversed_generator(seed),
        "c3ec2d6688cc38e8ad384ed5cbf5dabc663dbf9e97d7608367"
        ),
        (
        "longest_palindrome",
        longest_palindrome_generator(seed),
        "ac239750104ee8ff92f547c3e73ffd4ca943ac0363f3b79f5a"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "group_equal",
        # group_equal_generator(seed),
        # "242fac179412d7ad82bebadbd74ac7d0044b33942a714870b9"
        # ),
        (
        "ryerson_letter_grade",
        ryerson_letter_grade_generator(),
        "b9b86a019c4502be825b0ed52c187f9a29106a08fbbb1ffcc6"
        ),
        (
        "is_ascending",
        is_ascending_generator(seed),
        "0ec304f7cd0d1b7a4460570947b05af1756a2510a5ba5ba9f1"
        ),
        (
        "double_until_all_digits",
        double_until_all_digits_generator(),
        "7c4ba46364765cb0679f609d428bbbae8ba0df440b001c4162"
        ),
        (
        "give_change",
        give_change_generator(seed),
        "5c38f097ab4b39598124d3983a58a10301e012ee156ac05f1a"
        ),
        (
        "winning_card",
        winning_card_generator(seed),
        "521ef5920c74596498f231116663de8089b8fdbc1745e1219e"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "hand_is_badugi",
        # hand_is_badugi_generator(987),
        # "d37917aab58ce06778d3f667f6c348d1e30ee67271d9d1de60"
        # ),
        (
        "bridge_hand_shape",
        bridge_hand_shape_generator(seed),
        "61cfd31019c2838780311603caee80a9c57fae37d4f5b561ce"
        ),
        (
        "hand_shape_distribution",
        hand_shape_distribution_generator(seed),
        "0a34b7e0409552587469623bd8609dae1218f909c178c592db"
        ),
        # Removed from problem set April 20, 2020
        # (
        # "sort_by_typing_handedness",
        # sort_by_typing_handedness_generator(),
        # "919973a60cc556525aa38082a607f9981e83e5a58944d084af"
        # ),
        (
        "possible_words",
        possible_words_generator(seed),
        "f5fcb8d31014ed4dd3b618a08423b1370d80e171bd2d96f7d8"
        ),

        # New additions to the problem set in 2020.

        (
        "cookie",
        cookie_generator(seed),
        "ef5d2cc98a988383fdd167ac0ab2305312133dd57e9045cebe"
        ),
        (
        "eliminate_neighbours",
        eliminate_neighbours_generator(seed),
        "37bb46ab8421843a4d535a796de605eed5138fa31033c42506"
        ),
        (
        "counting_series",
        counting_series_generator(seed),
        "d7e9ef9de8cb71c901622aec367ff4b0eb96869cae7bbc8cd4"
        ),
        (
        "is_zigzag",
        is_zigzag_generator(seed),
        "fe5e03401a32bc5ca989759708d10a7f9d2cbd9e4821566b91"
        ),
        (
        "next_zigzag",
        next_zigzag_generator(seed),
        "52d66db24fc831dd08657f36e2e7b49ab788e6c86e8a25d3c5"
        ),
        (
        "md",
        md_generator(seed),
        "a1dcac70c093c0ba7fcfeae6d9d9655accb1cf871617f2a874"
        ),
        (
        "wythoff_array",
        wythoff_array_generator(seed),
        "d9c276aee0a2914dc393b0fce677b859d3fd98e996a7bd924d"
        ),
        (
        "hourglass_flips",
        hourglass_flips_generator(seed),
        "dabc24b96ab339c979f71ce837bed001ae149f3377e44f68de"
        ),
        (
        "knight_jump",
        knight_jump_generator(seed),
        "6a771380844685c2356a8a1eaf97376132aeb6f112bd6f6836"
        ),
        (
        "frog_collision_time",
        frog_collision_time_generator(seed),
        "2767a8f92c414656971210a1beeb83f20ad197d445897aff10"
        ),
        (
        "spread_the_coins",
        spread_the_coins_generator(seed),
        "5fceeacd218e1529190ff6477d81313150ff9a79910984c9de"
        ),
        (
        "group_and_skip",
        group_and_skip_generator(seed),
        "6f1dbf73dc63c5c0c2b5cebba4e2aa2e78da9c909e186ccfec"
        ),
        (
        "nearest_polygonal_number",
        nearest_polygonal_number_generator(seed),
        "6813a79fcc5c8249e92e0bf4c1301fde4187df58d2207b23ca"
        ),
        # Removed from problem set July 8, 2020
        #(
        #"floor_power_solve",
        #floor_power_solve_generator(seed),
        #"177465906587f4bb545d546d9b9e4324a4fcbc46c2d3ec4a97"
        #),
        (
        "subtract_square",
        subtract_square_generator(seed),
        "8959f61972a8804d0b26e2ae92d30d4d3fb6f08f1bcf5e28b9"
        ),
        (
        "perimeter_limit_split",
        perimeter_limit_split_generator(seed),
        "eaddf8ce7e7dd40995a6be7c73d89873b47864d6fcf3d14bb9"
        ),
        (
        "duplicate_digit_bonus",
        duplicate_digit_bonus_generator(seed),
        "079ceaf567ed618d2a235cfe9c95d6fb9d5c45efe4cc987a83"
        ),
        (
        "count_word_dominators",
        count_word_dominators_generator(seed),
        "ade953572b3bf2540d892ae5d6c8912cd691305a494e3d009b"
        ),
        (
        "hitting_integer_powers",
        hitting_integer_powers_generator(),
        "ee7c93a64dd4090a231abc889da7ab6f300aa4460fdd7ff79a"
        ),
        (
        "permutation_cycles",
        permutation_cycles_generator(seed),
        "45ecf7be3ff5dbfa46a97ce660ee0484fc99baac36f55c8ad5"
        )
]

print(f"109 Python Problems tester, {version}, Ilkka Kokkarinen.")
try:
    exec(f"import {studentfile} as labs109")
except Exception as e:
    print(f"ERROR: Unable to import {studentfile}.py. Exiting...")
    print(f"{e}")
    exit(1)

# discrepancy(labs109.ryerson_letter_grade, ryerson_letter_grade,
#            ryerson_letter_grade_generator(), True)

if os.path.exists(recordfile):
    known, curr = dict(), ''
    with gzip.open(recordfile, 'rt') as rf:
        for line in rf:
            line = line.strip()
            if line.startswith('****'):
                curr = line[4:]
                known[curr] = []
            else:
                known[curr].append(line)
    test_all_functions(labs109, testcases, known = known)
else:
    with gzip.open(recordfile, 'wt') as rf:
        test_all_functions(labs109, testcases, recorder = rf)
