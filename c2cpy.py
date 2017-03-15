#!/usr/bin/env python

import argparse, os, shutil, sys, subprocess, shlex, tempfile
import zipfile
from glob import glob

def stop_err( msg ):
    sys.stderr.write( "%s\n" % msg )
    sys.exit

def zipper(dir, zip_file):
    zip = zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED)
    root_len = len(os.path.abspath(dir))
    for root, dirs, files in os.walk(dir):
        archive_root = os.path.abspath(root)[root_len:]
        for f in files:
            fullpath = os.path.join(root, f)
            archive_name = os.path.join(archive_root, f)
            zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
    zip.close()
    return zip_file

def __main__():
    # Parse Command Line
    parser = argparse.ArgumentParser(description='Wrapper for coverage2cytosine')

    parser.add_argument( '--bismark_path', dest='bismark_path', help='Path to the bismark perl scripts' )

    # Input options
    parser.add_argument( '--input_file', dest='input_file', help='Use coverage file generated from bismark2bedGraph' )
    parser.add_argument( '--genome_folder', dest='genome_folder', help='Index directory: location of .fa or .fasta files' )
    parser.add_argument( '--fasta_file', dest='fasta_file' )

    # Output files to be retrieved
    parser.add_argument( '--output', dest='output' )
    parser.add_argument( '--merged_CpG_coverage', help='Additional experimental output file  (--merge_CpG option )' )
    parser.add_argument( '--chromosome_zip_archive', help='Zip archive from using --split_by_chromosome option')

    # Options
    parser.add_argument( '-CX', '--CX_context', dest='CX_context', action="store_true",
        help='Generate output file containing information of every cytosine in the genome, irrespective of context' )
    parser.add_argument( '--merge_CpG', dest='merge_CpG', action="store_true",
        help='Experimental: create an additional coverage file containing both and bottom strand methylation evidence as a single CpG dinucleotide entity' )
    parser.add_argument( '--zero_based', dest='zero_based', action="store_true",
        help='Use 0-based coordinates instead of 1-based coordinates throughout' )
    parser.add_argument( '--split_by_chromosome', dest='split_by_chromosome', action="store_true",
        help='Writes output to individual files for each chromosome instead of a single output file')

    args = parser.parse_args()

    # Create/find index
    index_dir=""
    if args.fasta_file:
        tmp_index_dir = tempfile.mkdtemp()
        genome_folder = os.path.join( tmp_index_dir, '.'.join( os.path.split( args.fasta_file )[1].split('.')[:-1] ) )
        try:
            os.symlink (args.fasta_file, genome_folder + '.fa')
        except Exception, e:
            if os.path.exists( tmp_index_dir ):
                shutil.rmtree( tmp_index_dir )
            stop_err( 'Error in linking the reference database.\n' + str( e ) )
        cmd_index = 'bismark_genome_preparation --bowtie2 %s ' % ( tmp_index_dir )
        if args.bismark_path:
            if os.path.exists(args.bismark_path):
                cmd_index = os.path.join( args.bismark_path, cmd_index )
            else:
                cmd_index = 'perl %s ' % os.path.join(os.path.realpath(os.path.dirname(__file__)), cmd_index )
        try:
            tmpindex = tempfile.NamedTemporaryFile( dir=tmp_index_dir ).name
            tmp_stderr = open( tmpindex, 'wb' )
            proc = subprocess.Popen(args.cmd_index, shell=True, cwd=tmp_index_dir, stdout=open(os.devnull, 'wb'), stderr=tmp_stderr.fileno() )
            returncode = proc.wait()
            tmp_stderr.close()
            tmp_stderr = open( tmp, 'rb' )
            stderr = ''
            buffsize = 1048576
            try:
                while True:
                    stderr += tmp_stderr.read( buffsize )
                    if not stderr or len( stderr ) % buffsize != 0:
                        break
            except OverflowError:
                pass
            tmp_stderr.close()
            if returncode != 0:
                raise Exception, stderr
        except Exception, e:
            if os.path.exists( tmp_index_dir ):
                shutil.rmtree( tmp_index_dir )
            stop_err( 'Error indexing reference sequence\n' + str( e ) )
        index_dir = tmp_index_dir       
    #figure out the recreation of the bisulfite genome again if it does not exist
    else:
        # path is to the index directory
        index_dir = os.path.dirname( args.genome_folder )

    # Testing - tempfile.mkdtemp( dir='/path/to/output/dir/' )
    output_dir = tempfile.mkdtemp()
    output_name = 'cytosine_coverage_report.tabular'
    cmd = 'coverage2cytosine --dir %(output_dir)s  %(args)s --genome_folder %(genome_folder)s --output %(output_name)s %(input)s'

    if args.bismark_path:
        if os.path.exists(args.bismark_path):
            cmd = os.path.join(args.bismark_path, cmd)
        else:
            cmd = os.path.join(os.path.realpath(os.path.dirname(__file__)), cmd)

    arguments = {
    'genome_folder' : index_dir,
    'args' : '',
    'output_name' : output_name,
    'output_dir' : output_dir,
    'input' : '' 
    }

    input_file = ''
    if args.input_file:
        input_file = ' %s ' % (args.input_file)
 
    #Options setup
    opts = ''
    if args.CX_context:
        opts += ' --CX_context '
    if args.merge_CpG:
        opts += ' --merge_CpG '
    if args.zero_based:
        opts += ' --zero_based '
    if args.split_by_chromosome:
        opts += ' --split_by_chromosome '

    arguments.update( {'args': opts, 'input': input_file} )

    # Final coverage2cytosine command formation
    cmd = cmd % arguments
    # Run
    try:
        tmp_out = tempfile.NamedTemporaryFile().name
        tmp_stdout = open( tmp_out, 'wb' )
        tmp_err = tempfile.NamedTemporaryFile().name
        tmp_stderr = open( tmp_err, 'wb' )
        proc = subprocess.Popen( args=cmd, shell=True, cwd=".", stdout=tmp_stdout, stderr=tmp_stderr )
        returncode = proc.wait()
        tmp_stderr.close()
        # Memory use, please consider size of data and the use of options
        tmp_stderr = open( tmp_err, 'rb' )
        stderr = ''
        buffsize = 1048576
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

        #TODO: look for errors in program output
    except Exception, e:
        stop_err( 'Error in coverage2cytosine:\n' + str( e ) )
    
    #Collect both regular and split_by_chromosome files
    if args.output:
        shutil.move( glob(os.path.join( output_dir, '*.tabular'))[0], args.output )
    if args.merge_CpG:
        shutil.move( glob(os.path.join( output_dir, '*.merged_CpG_evidence.cov'))[0], args.merged_CpG_coverage )

    if args.chromosome_zip_archive and args.split_by_chromosome:
        zipper(output_dir, args.chromosome_zip_archive)

     #Included: Clean up temp_dirs
    if args.fasta_file:
        if os.path.exists( tmp_index_dir):
            shutil.rmtree( tmp_index_dir )
    if os.path.exists( output_dir ):
        shutil.rmtree( output_dir )

if __name__=="__main__": __main__()
