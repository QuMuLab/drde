
import sys, os, time

from krrt.utils import run_experiment, run_command, read_file

from settings import *
from domains import DOMAINS
from compile import COMPILERS

USAGE_STRING = "\n  Usage: python run.py [action|fluent|both] [<domain>|all] <output directory>\n"


def run(types, doms, outdir):

    os.system("echo \"Type,Domain,Problem,Compiler,SAT Clauses,SAT Vars,SAT Encoding Time,Compiled Size,Compiled #Sol,Compile Time\" > %s/results.csv" % outdir)

    for t in types:

        os.mkdir("%s/%s" % (outdir, t))

        for d in doms:

            os.mkdir("%s/%s/%s" % (outdir, t, d))

            print "\n  -{ Running type (%s) with domain %s }-" % (t,d)

            ## Encode things into a CNF file ##
            print "\n    Encoding..."

            cnfs = []
            cnf_stats = {}
            for (dom,prob) in DOMAINS[d]:
                cnffile = "%s/%s/%s/%s.cnf" % (outdir, t, d, prob.split('/')[-1])
                logfile = cnffile.split('/drde/')[-1] + '.log'
                errfile = logfile[:-4] + '.err'
                cnfs.append(cnffile)
                startT = time.time()
                run_command("python encode.py %s %s %s %s" % (t, dom, prob, cnffile),
                            output_file = logfile, error_file = errfile,
                            MEMLIMIT = 4000000, TIMELIMIT = 300)

                if os.path.isfile(cnffile):
                    cnfline = read_file(cnffile)[3]
                    numV = cnfline.split()[2]
                    numC = cnfline.split()[3]
                    encodeTime = time.time() - startT
                    cnf_stats[prob.split('/')[-1]] = (numC,numV,encodeTime)


            ## Solve things with every compiler ##
            print "\n    Solving..."

            inout= ["%s#%s.compiled-by-" % (cnf, cnf[:-4]) for cnf in cnfs]
            results = run_experiment(
                base_directory = '/'.join(outdir.split('/')[:-1]),
                base_command = 'python ../compile.py',
                parameters = {'-compiler': COMPILERS.keys(),
                              '-inout': inout},
                time_limit = TIMEOUT,
                memory_limit = MEMOUT,
                processors = PROCS,
                progress_file = None,
                output_file_func = (lambda res: "%s%s.krrt-log" % (res.parameters['-inout'].split('#')[-1].split('/')[-1],
                                                                   res.parameters['-compiler'])),
                sandbox = "%s-%s" % (t,d),
                results_dir = "%s/%s/%s" % (outdir, t, d)
            )


            ## Analyze the results ##
            print "\n    Analyzing..."
            for res in results:
                compiler = res.parameters['-compiler']
                problem = res.parameters['-inout'].split('#')[-1].split('/')[-1].split('.compiled-by')[0]
                try:
                    (size,solnum) = COMPILERS[compiler][1](res,compiler)
                except:
                    (size,solnum) = ('error','error')
                    print "\nWarning: Cannot fetch the size/solnum for result..."
                    print res
                    print
                os.system("echo \"%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\" >> %s/results.csv" % (t, d, problem, compiler,
                                                                                        cnf_stats[problem][0],
                                                                                        cnf_stats[problem][1],
                                                                                        cnf_stats[problem][2],
                                                                                        size, solnum, res.runtime, outdir))

if __name__ == '__main__':

    if 4 != len(sys.argv) or sys.argv[1] not in ['action', 'fluent', 'both']:
        print USAGE_STRING
        sys.exit(1)

    types = [sys.argv[1]]
    if 'both' == sys.argv[1]:
        types = ['action','fluent']

    doms = [sys.argv[2]]
    if 'all' == sys.argv[2]:
        doms = DOMAINS.keys()

    outdir = sys.argv[3]
    if os.path.isdir(outdir):
        print "\nError: Output directory %s already exists\n" % outdir
        sys.exit(1)
    elif '/' != outdir[0]:
        print "\nError: Best if you specify the output directory in absolute terms\n"
        sys.exit(1)
    else:
        os.mkdir(outdir)

    run(types, doms, outdir)
    print
