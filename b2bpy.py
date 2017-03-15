#!/usr/bin/env python

import argparse
import os
import shutil
import sys
import subprocess
import shlex
import tempfile
from glob import glob

def stop_err( msg ):
    sys.stderr.write( "%s\n" % msg )
    sys.exit

def __main__():
    # Parse Command Line
    parser = argparse.ArgumentParser(description='Wrapper for bismark2bedGraph')

    parser.add_argument( '--bismark_path', dest='bismark_path',
        help='Path to the bismark perl scripts' )

    # Context of the Methylation Extractor input files possible
    parser.add_argument( '--input_file', dest='input_file',
        help='Use output file from Bismark Methylation Extractor' )

    # Output files to be retrieved
    parser.add_argument( '--output', dest='output' )
    parser.add_argument( '--coverage' )
    parser.add_argument( '--zero_coverage',
        help='Additional output file using zero-based start coordinates (--zero_based option)' )

    # Options
    parser.add_argument('--cutoff', dest='cutoff', type=int, default=1, 
        help='Threshold check for methylation sorting' )
    parser.add_argument( '--buffer_size', dest='buffer_size', type=str,
        help='Limit memory usage by gigabyte units only')

    parser.add_argument( '--remove_spaces', dest='remove_spaces', action="store_true",
        help='Remove whitespaces contained in sequence ID of bismark methylation extractor files')
    parser.add_argument( '--scaffolds', '--gazillion', dest='scaffolds', action="store_true",
        help='Specified if your reference genome is unfinished or scaffolds' )
    parser.add_argument( '--ample_memory', dest='ample_memory', action="store_true",
        help='Two arrays for sorting' )
    parser.add_argument( '--zero_based', dest='zero_based', action="store_true",
        help='Create an additional zero-based start coordinate coverage file' )

    args = parser.parse_args()

    # Build bismark2bedGraph command
    # There are limitations in using bismark2bedGraph on local Galaxy. For --buffer_size, 10 GB is maximum limit at Hunter cluster
    # Testing - tempfile.mkdtemp( dir='/path/to/output/dir' )
    output_dir = tempfile.mkdtemp()
    output_name = 'eggs.bedGraph'
    cmd = 'bismark2bedGraph %(args)s --CX --dir %(output_dir)s --output %(output_name)s %(input)s'

    if args.bismark_path:
        if os.path.exists(args.bismark_path):
            cmd = os.path.join(args.bismark_path, cmd)
        else:
            cmd = os.path.join(os.path.realpath(os.path.dirname(__file__)), cmd)

    arguments = {
    'args': '',
    'output_name': output_name,
    'output_dir': output_dir, 
    'input': ''
    }

    input_file = ''
    if args.input_file:
        input_file += ' %s ' % (args.input_file)

    # Options setup
    opts = ''
    if args.cutoff:
        opts += ' --cutoff %s ' % args.cutoff
    if args.remove_spaces:
        opts += ' --remove_spaces '
    # large-cluster sort options
    if args.buffer_size:
        opts += ' --buffer_size %s'  % args.buffer_size
    if args.scaffolds:
        opts += ' --scaffolds '
    if args.ample_memory:
        opts += ' --ample_memory '
    if args.zero_based:
        opts += ' --zero_based '

    arguments.update( {'args': opts, 'input': input_file} )
 
    # Final bismark2bedGraph command formation
    cmd = cmd % arguments
    # Run
    try:
        tmp_out = tempfile.NamedTemporaryFile().name
        tmp_stdout = open ( tmp_out, 'wb' )
        tmp_err = tempfile.NamedTemporaryFile().name
        tmp_stderr = open( tmp_err, 'wb' )
        proc = subprocess.Popen( args=cmd, shell=True, cwd=".", stdout=tmp_stdout, stderr=tmp_stderr )
        returncode = proc.wait()
        tmp_stderr.close()
        # Memory use, check for standard errors due to --buffer_size option
        tmp_stderr = open( tmp_err, 'rb' )
        stderr = ''
        buffsize = 2097152
        try:
            while True:
                stderr += tmp_stderr.read ( buffsize )
                if not stderr or len( stderr ) % buffsize != 0:
                    break
        except OverflowError:
            pass
        tmp_stdout.close()
        tmp_stderr.close()
        if returncode != 0:
            raise Exception, stderr
			
        #TODO: look for errors in program output.
    except Exception, e:
        stop_err( 'Error in bismark2bedGraph:\n' + str( e ) )

    # Collect and copy output files
    if args.output:
        shutil.move( glob(os.path.join( output_dir, '*.bedGraph'))[0], args.output )
    if args.coverage:
        shutil.move( glob(os.path.join( output_dir, '*.bismark.cov'))[0], args.coverage )
    if args.zero_coverage:
        shutil.move( glob(os.path.join( output_dir, '*.bismark.zero.cov'))[0], args.zero_coverage )

    #Included: Clean up temp dirs
    if os.path.exists( output_dir ):
        shutil.rmtree( output_dir )

if __name__=="__main__": __main__()
