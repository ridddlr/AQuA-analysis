import json
import os
import nltk

from collections import defaultdict

# from https://github.com/MurtyShikhar/Question-Answering/blob/master/preprocessing/squad_preprocess.py
def tokenize(sequence):
    tokens = [token.replace("``", '"').replace("''", '"') for token in nltk.word_tokenize(sequence)]
    return map(lambda x:x.encode('utf8'), tokens)

# load problems into Python list
def load_from_file(filename):
    jsonprobs = []
    plines = open(filename)
    for pline in plines:
        jsonprob = json.loads(pline)
        jsonprobs.append(jsonprob)
    return jsonprobs

# add user-defined attributes to each problem
def process_probs(jsonprobs):
    processed_probs = []
    for prob in jsonprobs:
        question = prob['question']
        correct = prob['correct']
        options = prob['options']
        rationale = prob['rationale']

        pvals, nvals = get_number_vals(question)
        processed_opts = get_processed_opts(options)

        prob['processed_opts'] = processed_opts
        prob['nvals'] = nvals
        prob['pvals'] = pvals
        processed_probs.append(prob)
    return processed_probs

# generate answer guesses for each problem
def answer_probs(jsonprobs):
    processed_probs = []
    for prob in jsonprobs:
        question = prob['question']
        correct = prob['correct']
        options = prob['options']
        rationale = prob['rationale']

        processed_opts = prob['processed_opts']
        nvals = prob['nvals']
        pvals = prob['pvals']

        if correct == 'A':
            ansi = 0
        elif correct == 'B':
            ansi = 1
        elif correct == 'C':
            ansi = 2
        elif correct == 'D':
            ansi = 3
        elif correct == 'E':
            ansi = 4

        avals = []
        cvals = []
        # basic guessing for problems with percentages
        if len(pvals) > 0:
            for n in nvals:
                for p in pvals:
                    avals.append(1.0*n*p/100.0)
                    avals.append(1.0*n*(100.0-p)/100.0)
        else:
            # basic guessing for problems with number values
            for n in nvals:
                for n2 in nvals:
                    avals.append(n+n2)
                    avals.append(n-n2)
                    avals.append(n*n2)
                    if n2 != 0:
                        avals.append(n*1.0/n2)

        for i in range(len(processed_opts)):
            o = processed_opts[i]
            if o in avals:
                cvals.append(i)
            else:
                pass

        if ansi in cvals:
            contained_ans = 1
        else:
            contained_ans = 0

        prob['cvals'] = cvals
        prob['ansi'] = ansi
        prob['contained_ans'] = contained_ans
        processed_probs.append(prob)
    return processed_probs

# load and immediately process problems from file
def load_and_process_from_file(filename):
    jsonprobs = load_from_file(filename)
    processed_probs = process_probs(jsonprobs)
    return processed_probs

# find number of problems with correct answer A,B,C,D,E
def get_correct_counts(jsonprobs):
    ccounts = defaultdict(int)
    for prob in jsonprobs:
        correct = prob['correct']
        ccounts[correct] += 1
    return ccounts

# process the answer options into numbers using float()
def get_processed_opts(options):
    processed_opts = []

    def process_opt(optstr):
        toks = tokenize(optstr)
        try:
            val = None
            for tok in toks:
                if val is not None:
                    return val
                try:
                    val = float(tok)
                except:
                    try:
                        val = None
                        ctok = tok.replace(",", "")
                        val = float(ctok)
                    except:
                        val = None
            if val is not None:
                return val
            val = float(optstr)
        except:
            return float(optstr)
        return val

    op0 = options[0][4:]
    op1 = options[1][4:]
    op2 = options[2][4:]
    op3 = options[3][4:]
    op4 = options[4][4:]
    try:
        o0 = process_opt(op0)
        o1 = process_opt(op1)
        o2 = process_opt(op2)
        o3 = process_opt(op3)
        processed_opts = [o0, o1, o2, o3]
        o4 = process_opt(op4)
        processed_opts = [o0, o1, o2, o3, o4]
    except:
        pass
    return processed_opts
        
# get number values and percentage values from question tokens
def get_number_vals(question):
    tokens = tokenize(question)
    nvals = []
    pvals = []
    for i in range(len(tokens)):
        token = tokens[i]
        val = None
        typestr = None
        try:
            val = int(token)
            typestr = 'int'
        except:
            try:
                val = float(token)
                typestr = 'float'
            except:
                val = None
                typestr = 'none'
        if typestr == 'int' or typestr == 'float':
            if i < len(tokens)-1 and tokens[i+1] == '%':
                pvals.append(val)
            else:
                nvals.append(val)
    return pvals, nvals

# pretty-print info on problem
def print_prob_info(q):
    question = q['question']
    options = q['options']
    rationale = q['rationale']
    correct = q['correct']
    processed_opts = q['processed_opts']
    nvals = q['nvals']
    pvals = q['pvals']

    print question
    print options
    print 'nvals', nvals
    print 'pvals', pvals
    print rationale
    print correct
    print processed_opts
    for oi in options:
        ot = tokenize(oi)
        print ot
    print ''

# basic guessing for questions with percentage values
def try_info(q):
    question = q['question']
    options = q['options']
    rationale = q['rationale']
    correct = q['correct']
    processed_opts = q['processed_opts']
    nvals = q['nvals']
    pvals = q['pvals']

    avals = []
    cvals = []
    for n in nvals:
        for p in pvals:
            avals.append(1.0*n*p/100.0)
            avals.append(1.0*n*(100.0-p)/100.0)
    for i in range(len(processed_opts)):
        o = processed_opts[i]
        print 'ptest'
        print i
        if o in avals:
            cvals.append(i)
            print 'true'
        else:
            print 'false'

    print 'cvals'
    print cvals
    
    print 'avals', avals
    print 'processed_opts', processed_opts
    for oi in options:
        ot = tokenize(oi)
        print ot
    print ''

# print info about problem list
def print_cvals_info(aprobs):

    cval_count = len(filter(lambda prob: len(prob['cvals']) >= 1, aprobs))
    contained_count = len(filter(lambda prob: prob['contained_ans'] == 1, aprobs))
    contained_count1 = len(filter(lambda prob: prob['contained_ans'] == 1 and len(prob['cvals']) == 1, aprobs))
    contained_count2 = len(filter(lambda prob: prob['contained_ans'] == 1 and len(prob['cvals']) == 2, aprobs))
    contained_count3 = len(filter(lambda prob: prob['contained_ans'] == 1 and len(prob['cvals']) == 3, aprobs))
    contained_count4 = len(filter(lambda prob: prob['contained_ans'] == 1 and len(prob['cvals']) == 4, aprobs))
    contained_count5 = len(filter(lambda prob: prob['contained_ans'] == 1 and len(prob['cvals']) == 5, aprobs))
    print 'len'
    print len(aprobs)
    print 'cval_count'
    print cval_count
    print 'contained_count'
    print contained_count
    print 'contained_count1'
    print contained_count1
    print contained_count2
    print contained_count3
    print contained_count4
    print contained_count5

# analyze questions file in AQuA dataset
QUESTION_FILE = 'AQuA/train.tok.json'

# load problems
processed_probs = load_and_process_from_file(QUESTION_FILE)

# guess answers for problems
aprobs = answer_probs(processed_probs)

# subset of problems with exactly one percentage value
p1qs = filter(lambda prob: len(prob['pvals']) == 1, processed_probs)

# subset of problems with exactly two number values
aprobs2 = filter(lambda prob: len(prob['nvals']) == 2, aprobs)

exactly_one_ans = filter(lambda prob: len(prob['cvals']) == 1, aprobs)
exactly_one_ans_correct = filter(lambda prob: prob['contained_ans'] == 1, exactly_one_ans)

at_least_one_ans = filter(lambda prob: len(prob['cvals']) >= 1, aprobs)
at_least_one_ans_correct = filter(lambda prob: prob['contained_ans'] == 1, at_least_one_ans)

ccounts = get_correct_counts(processed_probs)
pcount = len(filter(lambda prob: len(prob['pvals']) > 0, processed_probs))

print ''
print 'File analyzed:', QUESTION_FILE
print ''

print 'Correct answers by answer choice:'

for key in sorted(ccounts.keys()):
    print key, ccounts[key]
print ''
print 'Total number of questions:', len(aprobs)

print ''
print 'Questions with at least one percentage value:', pcount

print ''
print 'Questions with exactly one generated guess:', len(exactly_one_ans)
print 'Number of questions with correct guess:', len(exactly_one_ans_correct)

print ''
print 'Questions with at least one generated guess:', len(at_least_one_ans)
print 'Number of questions with correct guess:', len(at_least_one_ans_correct)

print ''
print 'Print info on sample question:'
print_prob_info(aprobs[0])

