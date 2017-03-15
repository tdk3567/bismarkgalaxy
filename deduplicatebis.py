#!/usr/bin/env python

import argparse, os, shutil, subprocess, sys, tempfile, fileinput
from glob import glob

def stoperr(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit()

def __main__():
    parser = argparse.ArgumentParser(description='Wrapper for deduplicate Bismark')
    # Required command implement
    parser.add_argument('--bismark_path', dest='bismark_path', help='Path to bismark perl scripts')
    parser.add_argument('--samtools_path', dest='samtools_path', help='Provide path to samtools installation if it is not in the PATH')
    # IO
    parser.add_argument('--input_file', dest='input_file', help='Provide SAM for deduplication')
    parser.add_argument('--output', dest='output', help='Cleaned Bismark file')
    parser.add_argument('--report', dest='report', help='Deduplication report')
    """parser.add_argument('--representative_output')
    parser.add_argument('--barcode_output')
    parser.add_argument('--bam_output')
    parser.add_argument('--vanilla_output')
    """
    # Output options
    parser.add_argument('--bam', dest='bam', action="store_true", help='Write out Bismark file in BAM format')
    parser.add_argument('--single', dest='single', action="store_true", help='Single-end Bismark file')
    parser.add_argument('--paired', dest='paired', action="store_true", help='Paired-end Bismark file')
    parser.add_argument('--vanilla', dest='vanilla', action="store_true", help='Input file is old custom Bismark 0.6.x or lower')
    parser.add_argument('--representative', dest='representative', action="store_true", help='Print the most represented methylation call for any given position.')
    parser.add_argument('--barcode', dest='barcode', action='store_true', help='Account for barcode in deduplication')
    args = parser.parse_args()
    
    #Command
    command = 'deduplicate_bismark %(options)s %(input_files)s'

    perlargs = {
    'options': '',
    'input_files': ''
    }

    options = ''
    if args.bismark_path:
        if os.path.exists(args.bismark_path):
            command = os.path.join(args.bismark_path, command)
        else:
            command = os.path.join(os.path.realpath(os.path.dirname(__file__)), command)
    if args.samtools_path:
        options += ' --samtools_path %s ' % args.samtools_path 
    if args.bam:
        options += ' --bam '
    if args.paired:
        options += ' --paired '
    else:
        options += ' --single '
    if args.single:
        options += ' --single '
    if args.vanilla:
        options += ' --vanilla '
    if args.representative:
        options += ' --representative '
    if args.barcode:
        options += ' --barcode '
    input_files = ''
    if args.input_file:
        input_files += ' %s ' % args.input_file       
        cwddir = os.path.dirname(args.input_file)

    perlargs.update( {'options': options, 'input_files': input_files } )
    command = command % perlargs

    # Run
    try:
        tmpout = tempfile.NamedTemporaryFile().name
        tmpstdout = open(tmpout, 'wb')
        tmperr = tempfile.NamedTemporaryFile().name
        tmpstderr = open(tmperr, 'wb')
        proc = subprocess.Popen(args=command, shell=True, cwd=".", stdout=tmpstdout, stderr=tmpstderr)
        returncode = proc.wait()
        tmpstderr.close()
        tmpstderr = open(tmperr, 'rb')
        stderr = ''
        buffsize = 1048576
        try:
            while True:
                stderr += tmpstderr.read(buffsize)
                if not stderr or len(stderr) % buffsize != 0:
                    break
        except OverflowError:
            pass
        tmpstdout.close()
        tmpstderr.close()
        if returncode != 0:
            raise Exception, stderr
    except Exception, e:
        stoperr('Error in deduplication:\n' + str(e))
        
    # Retrieve output: file extension depend on options applied
    """ Depreciate for now:
    Default as .deduplicated_sam.gz
    barcode as .dedupRRBS.sam.gz
    representative as .deduplicated_to_representative_sequences.sam.gz
    """
    if args.report:
        shutil.move(glob(os.path.join(cwddir, '*.deduplication_report.txt'))[0], args.report)
    if args.output:
        shutil.move(glob(os.path.join(cwddir, '*.deduplicated*'))[0], args.output)
    if args.output and args.barcode is True:
        shutil.move(glob(os.path.join(cwddir, '.dedup_*'))[0], args.output)
    """3if no samtools_path:
        #(bam) .deduplicated.sam.gz

    if args.representative_output:
        shutil.move(glob(os.path.join(cwddir, '*.deduplicated_to_representative_sequences.sam'))[0], args.representative_output)
    # Paired options for representative
    elif args.paired is True and args.representative_output:
        shutil.move(glob(os.path.join(cwddir, '.deduplicated_to_representative_sequences_pe.sam'))[0], args.representative_output)
    elif args.paired is True and args.vanilla is True and args.representative_output:
        shutil.move(glob(os.path.join(cwddir, '*_deduplicated_to_representative_sequences_pe.txt'))[0], args.representative_output)
    # Other options for representative
    elif args.vanilla is True and args.representative_output:
        shutil.move(glob(os.path.join(cwddir, '*.deduplicated_to_representative_sequences.txt')[0], args.representative_output))
    elif args.bam is True and args.representative_output:
        shutil.move(glob(os.path.join(cwddir, '*.deduplicated_to_representative_sequences.bam'))[0], args.representative_output)

    if args.bam_output and args.bam is True:
        shutil.move(glob(os.path.join(cwddir, '*.deduplicated.bam'))[0], args.bam_output)

    if args.barcode_output and args.barcode is True:
        shutil.move(glob(os.path.join('*.dedup_RRBS.sam'))[0], args.barcode_output)
    elif args.barcode_output and args.vanilla is True:
        shutil.move(glob(os.path.join('*_dedup_RRBS.txt'))[0], args.barcode_output)
    elif args.barcode_output and args.bam is True:
        shutil.move(glob(os.path.join(cwddir, '*.dedup_RRBS.bam'))[0], args.barcode_output)

    if args.vanilla_output and args.vanilla is True:
        #Option should not be left in but is for Bismark 0.6x and degraded
        shutil.move(glob(os.path.join(cwddir, '*_deduplicated.txt'))[0], args.vanilla_output)
    """

if __name__=="__main__": __main__()
