
import pprint

from krrt.utils import load_CSV

lines = load_CSV('results-fluents.csv')
lines += load_CSV('results-actions.csv')[1:]

print "\n    { Headers }\n"
for i in range(len(lines[0])):
    print "  %d\t%s" % (i, lines[0][i])
print

lines = lines[1:] # Remove the headers
lines = filter(lambda x: x[1] != 'testing', lines) # Remove the testing domain results

domains = ['airport', 'floortile', 'mystery', 'parcprinter', 'pegsol', 'sokoban', 'trucks', 'woodworking']
solvers = ['c2d-dt0', 'c2d-dt4', 'dsharp', 'sharpSAT', 'mc2d-dt0', 'mc2d-dt4', 'cnf2bdd', 'bddminisat']
goodsolvers = {'c2d-dt4': 'c2d',
               'dsharp': '\\textsc{Dsharp}',
               'sharpSAT': 'sharpSAT',
               'mc2d-dt0': 'minic2d',
               'cnf2bdd': 'cnf2bdd',
               'bddminisat': 'bddmin'}

domcount = {'airport': 50,
            'floortile': 20,
            'mystery': 30,
            'parcprinter': 20,
            'pegsol': 20,
            'sokoban': 20,
            'testing': 4,
            'trucks': 30,
            'woodworking': 20}

problems = {k: set() for k in domcount}

coverage = {t: {s: {d: 0 for d in domains} for s in solvers} for t in ['action', 'fluent']}
timeouts = {t: {s: {d: 0 for d in domains} for s in solvers} for t in ['action', 'fluent']}
memouts = {t: {s: {d: 0 for d in domains} for s in solvers} for t in ['action', 'fluent']}
errors = {t: {s: {d: 0 for d in domains} for s in solvers} for t in ['action', 'fluent']}
segfaults = {t: {s: {d: 0 for d in domains} for s in solvers} for t in ['action', 'fluent']}

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

ddn_probs = {d: {} for d in domains}
bdd_probs = {d: {} for d in domains}

cnf_sizes = {t: {d: {} for d in domains} for t in ['action', 'fluent']}

for l in lines:
    problems[l[1]].add(l[2])
    cnf_sizes[l[0]][l[1]][l[2]] = l[4]
    if 'memout' == l[8]:
        memouts[l[0]][l[3]][l[1]] += 1
    elif 'timeout' == l[8]:
        timeouts[l[0]][l[3]][l[1]] += 1
    elif 'segfault' == l[8]:
        segfaults[l[0]][l[3]][l[1]] += 1
    elif 'error' == l[8]:
        print " Error: %s" % str(l)
        errors[l[0]][l[3]][l[1]] += 1
    else:
        assert is_number(l[8]) or is_number(l[7]), "Offending line: %s" % str(l)
        if l[3] == 'c2d-dt4' and l[0] == 'fluent':
            ddn_probs[l[1]][l[2]] = int(l[7])
        elif l[3] == 'cnf2bdd' and l[0] == 'fluent':
            bdd_probs[l[1]][l[2]] = int(l[7])
        coverage[l[0]][l[3]][l[1]] += 1

for d in problems:
    #print "%d -> %d" % (domcount[d], len(problems[d]))
    domcount[d] = len(problems[d])

def print_coverage(t):
    print "\n\n Encoding Coverage (%s):\n" % t
    print "Domain\t\t%s\tALL" % '\t'.join([d[:4] for d in sorted(domains)])
    for s in solvers:
        print "%s\t" % s,
        if s in ['c2d-dt0', 'c2d-dt4', 'dsharp', 'cnf2bdd']:
            print '\t',
        print '\t'.join(map(str, coverage[t][solvers.index(s)])),
        print "\t%d" % sum(coverage[t][solvers.index(s)])
    print "Total\t\t%s\t%d" % ('\t'.join(map(str, [domcount[d] for d in sorted(domains)])),
                               sum([domcount[d] for d in sorted(domains)]))

#print_coverage('action')
#print_coverage('fluent')


def print_coverage_table():
    print "\multirow{2}{*}{Domain} & %s \\\\" % ' & '.join(["\multicolumn{2}{|c||}{%s}" % goodsolvers[s] for s in sorted(goodsolvers.keys())])
    print " & %s \\\\" % ' & '.join(['act & flu'] * 6)
    print "\hline"
    for d in sorted(domains):
        line = "%s (%d)" % (d, domcount[d])
        maxv = max([coverage[t][s][d] for t in ['action', 'fluent'] for s in goodsolvers])
        for s in sorted(goodsolvers.keys()):
            for t in ['action', 'fluent']:
                v = coverage[t][s][d]
                if v == maxv:
                    line += " & \\textbf{%d}" % v
                else:
                    line += " & %d" % v
        print "%s \\\\" % line
        print "\hline"
    line = "ALL (%d)" % sum(domcount.values())
    for s in sorted(goodsolvers.keys()):
        for t in ['action', 'fluent']:
            v = sum([coverage[t][s][d] for d in domains])
            if t == 'fluent' and s == 'c2d-dt4':
                line += " & \\textbf{%d}" % v
            else:
                line += " & %d" % v
    print "%s \\\\" % line

def compute_failure_stats():
    for t in ['action', 'fluent']:
        ms = sum([memouts[t][s][d] for s in goodsolvers for d in domains])
        ts = sum([timeouts[t][s][d] for s in goodsolvers for d in domains])
        ss = sum([segfaults[t][s][d] for s in goodsolvers for d in domains])
        cs = sum([coverage[t][s][d] for s in goodsolvers for d in domains])
        tot1 = sum([ms, ts, ss, cs])
        tot2 = sum([ms, ts, ss])

        print "\n%s ratios (normalized by all, and by unsolved)" % t
        print "  Memout\t%d\t%.2f\t%.2f" % (ms, float(ms) / float(tot1), float(ms) / float(tot2))
        print "  Timeout\t%d\t%.2f\t%.2f" % (ts, float(ts) / float(tot1), float(ts) / float(tot2))
        print "  Segfault\t%d\t%.2f\t%.2f" % (ss, float(ss) / float(tot1), float(ss) / float(tot2))
        print "  Solved\t%d\t%.2f" % (cs, float(cs) / float(tot1))
        print "  Total\t\t%d\t%d" % (tot1, tot2)

def compare_dd_w_bdd():
    data = {}
    for d in domains:
        print "\n%s" % d
        for p in bdd_probs[d]:
            if p in ddn_probs[d]:
                if d not in data:
                    data[d] = ([],[])
                data[d][0].append(ddn_probs[d][p])
                data[d][1].append(bdd_probs[d][p])
                print "%d =vs= %d" % (ddn_probs[d][p], bdd_probs[d][p])

    print
    pprint.pprint(data)
    print

def compare_cnf_sizes():
    data = {}
    for d in domains:
        data[d] = ([],[])
        for p in cnf_sizes['action'][d]:
            data[d][0].append(cnf_sizes['action'][d][p])
            data[d][1].append(cnf_sizes['fluent'][d][p])
    print
    #pprint.pprint(data)
    print data
    print

#print_coverage_table()
#compute_failure_stats()
#compare_dd_w_bdd()
compare_cnf_sizes()

print
