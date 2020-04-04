
from os import walk

DOMAINS = {}

testing = [("domains/testing/d%d.pddl" % i, "domains/testing/p%d.pddl" % i) for i in range(1,5)]
DOMAINS['testing'] = testing

domlist = ['airport', 'floortile', 'mystery', 'parcprinter', 'pegsol', 'sokoban', 'trucks', 'woodworking']
for d in domlist:
    for (dirpath, dirnames, filenames) in walk('domains/'+d):
        domains = sorted([f for f in filenames if "domain" in f])
        problems = sorted([f for f in filenames if "domain" not in f])
        if len(domains) == 1:
            DOMAINS[d]=[ (domains[0], prob) for prob in problems]
        else:
            if len(domains) != len(problems):
                raise Exception( "missmatching domain and problem files" )
            DOMAINS[d] = zip( domains, problems )

    DOMAINS[d] = [("domains/%s/%s" % (d,df), "domains/%s/%s" % (d,pf)) for (df,pf) in DOMAINS[d]]
