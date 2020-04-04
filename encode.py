
from krrt.sat.CNF import Formula, Not as neg
from krrt.planning.strips.representation import parse_problem

USAGE_STRING = "\n  Usage: python encode.py [action|fluent] domain.pddl problem.pddl output.cnf\n"

def encode(mode, dfile, pfile, ofile):

    print "Parsing ground pddl..."

    # Load and set up the problem
    F, A, I, G = parse_problem(dfile, pfile)
    A = A.values()

    print "Building CNF model..."

    adders = {}

    for f in F:
        adders[f] = set([])

    for a in A:
        for f in a.adds:
            adders[f].add(a)

    formula = Formula()

    # For it to be a deadend, one of the goal fluents must be disabled
    formula.addClause(list(G))

    # If a fluent is disabled, then so is all of its adders
    for f in F:
        for a in adders[f]:
            if 'action' == mode:
                formula.addClause([neg(f), a])
            else:
                formula.addClause([neg(f)] + list(a.precond))

    if 'action' == mode:
        # If an action is disabled, then one of it's preconditions must be
        for a in A:
            formula.addClause([neg(a)] + list(a.precond))

    print "Writing files..."
    
    formula.writeCNF(ofile)
    formula.writeMapping(ofile+'.map')


if __name__ == '__main__':
    import sys
    if 5 != len(sys.argv) or sys.argv[1] not in ['action', 'fluent']:
        print USAGE_STRING
        sys.exit(1)
    encode(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
