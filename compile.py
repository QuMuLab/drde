
import os, sys

from krrt.utils import get_opts, get_value, read_file, match_value, get_lines

USAGE_STRING = "\n  Usage: python compile.py -compiler [c2d-dt0|c2d-dt4|sharpSAT|dsharp|mc2d-dt0|mc2d-dt4] -inout <input cnf>#<output file>\n"

def c2dn0(inp, out):
    out += 'c2d-dt0'
    localcnf = inp.split('/')[-1]
    return "cp %s .; ./../bin/c2d_linux -in %s -dt_method 0 -smooth_all -count > %s.log 2>&1; cp %s.nnf %s" % (inp, localcnf, out, localcnf, out)

def c2dn4(inp, out):
    out += 'c2d-dt4'
    localcnf = inp.split('/')[-1]
    return "cp %s .; ./../bin/c2d_linux -in %s -dt_method 4 -smooth_all -count > %s.log 2>&1; cp %s.nnf %s" % (inp, localcnf, out, localcnf, out)

def sharpSAT(inp, out):
    out += 'sharpSAT'
    return "./../bin/sharpSAT %s > %s.log 2>&1; echo \"No compilation -- only counting\" > %s; rm data.out" % (inp, out, out)

def dsharp(inp, out):
    out += 'dsharp'
    return "./../bin/dsharp -Fnnf %s %s > %s.log 2>&1" % (out, inp, out)

def minic2dn0(inp, out):
    out += 'mc2d-dt0'
    localcnf = inp.split('/')[-1]
    return "cp %s .; ./../bin/miniC2D -c %s -m 0 -C > %s.log 2>&1; cp %s.nnf %s" % (inp, localcnf, out, localcnf, out)

def minic2dn4(inp, out):
    out += 'mc2d-dt4'
    localcnf = inp.split('/')[-1]
    return "cp %s .; ./../bin/miniC2D -c %s -m 4 -C > %s.log 2>&1; cp %s.nnf %s" % (inp, localcnf, out, localcnf, out)

def cnf2bdd(inp, out):
    out += 'cnf2bdd'
    localcnf = inp.split('/')[-1]
    return "python ../bin/cnf2bdd.py %s > %s.log 2>&1; echo \"No compilation -- only counting\" > %s" % (inp, out, out)

def bddminisat(inp, out):
    out += 'bddminisat'
    localcnf = inp.split('/')[-1]
    return "./../bin/bdd_minisat_all %s > %s.log 2>&1; echo \"No compilation -- only counting\" > %s" % (inp, out, out)


###################################################


def nnf_size(fname):
    return len(read_file(fname)) - 1

def check_segfault(fname):
    return match_value(fname, '.*Segmentation fault.*')

def check_memout(fname):
    return match_value(fname, '.*std::bad_alloc.*') or \
           match_value(fname, '.*GNU MP: Cannot allocate memory.*') or \
           match_value(fname, '.*GNU MP: Cannot reallocate memory.*') or \
           match_value(fname, '.*Out of memory.*') or \
           match_value(fname, '.*memory allocation failed.*')

def check_timeout(fname):
    return False

def compute_fnames(res, compiler):
    outf = res.parameters['-inout'].split('#')[-1] + compiler
    logf = outf + '.log'
    return (outf, logf)

def check_for_failure(logf, res):
    if check_memout(logf):
        return ('memout','memout')
    elif check_timeout(logf) or res.timed_out:
        return ('timeout','timeout')
    elif check_segfault(logf):
        return ('segfault','segfault')
    else:
        return False

def parse_c2d(res, compiler):
    (outf, logf) = compute_fnames(res, compiler)
    failure = check_for_failure(logf, res)
    if failure:
        return failure
    else:
        solnum = get_value(logf, '.*Counting...([0-9]+) models.*', int)
        return (nnf_size(outf), solnum)

def parse_sharpSAT(res, compiler):
    (outf, logf) = compute_fnames(res, compiler)
    failure = check_for_failure(logf, res)
    if failure:
        return failure
    else:
        solnum = get_lines(logf, lower_bound="# solutions", upper_bound="# END")[0]
        return ('-', solnum)

def parse_dsharp(res, compiler):
    (outf, logf) = compute_fnames(res, compiler)
    failure = check_for_failure(logf, res)
    if failure:
        return failure
    else:
        solnum = get_value(logf, '.*# of solutions:[ \t]+([0-9]+\.[0-9]+e\+[0-9]+|[0-9]+).*', float)
        return (nnf_size(outf), int(solnum))

def parse_mc2d(res, compiler):
    (outf, logf) = compute_fnames(res, compiler)
    failure = check_for_failure(logf, res)
    if failure:
        return failure
    else:
        solnum = get_value(logf, '.*Counting... ([0-9]+) models.*', int)
        return (nnf_size(outf), solnum)

def parse_cnf2bdd(res, compiler):
    (outf, logf) = compute_fnames(res, compiler)
    failure = check_for_failure(logf, res)
    if failure:
        return failure
    else:
        bddsize = get_value(logf, '.*[ ]+([0-9]+) live nodes now.*', int)
        return (bddsize, '-')

def parse_bddminisat(res, compiler):
    (outf, logf) = compute_fnames(res, compiler)
    failure = check_for_failure(logf, res)
    if failure:
        return failure
    else:
        solnum = get_value(logf, '.*SAT \(full\)[ ]*:[ ]*([0-9]+).*', int)
        bddsize = get_value(logf, '.*\|obdd\|[ ]*:[ ]*([0-9]+).*', int)
        return (bddsize, solnum)

COMPILERS = {
    'c2d-dt0': (c2dn0, parse_c2d),
    'c2d-dt4': (c2dn4, parse_c2d),
    'sharpSAT': (sharpSAT, parse_sharpSAT),
    'dsharp': (dsharp, parse_dsharp),
    'mc2d-dt0': (minic2dn0, parse_mc2d),
    'mc2d-dt4': (minic2dn4, parse_mc2d),
    'cnf2bdd': (cnf2bdd, parse_cnf2bdd),
    'bddminisat': (bddminisat, parse_bddminisat)
}

if __name__ == '__main__':

    print "Command: %s" % ' '.join(sys.argv)

    (opts, flags) = get_opts()

    if ('-compiler' not in opts) or (opts['-compiler'] not in COMPILERS.keys()) or ('-inout' not in opts):
        print USAGE_STRING
        sys.exit(1)

    inp = opts['-inout'].split('#')[0]
    out = opts['-inout'].split('#')[1]
    os.system(COMPILERS[opts['-compiler']][0](inp, out))
