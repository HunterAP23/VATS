import argparse as argp
import multiprocessing as mp
import os
import subprocess as sp
import time

def time_function(func, i, sema, rlock):
    sema.acquire()
    func(i, sema)
    sema.release()

def run_in_parallel(fn, threads, lis, sema, rlock):
    proc = []
    for i in lis:
        p = mp.Process(target=time_function, args=(fn, i, sema, rlock))
        proc.append(p)

    for p in proc:
        p.start()

    for p in proc:
        try:
            p.join()
        except Exception as e:
            print("EXCEPTION: {}".format(e))

def multi_vmaf(i, sema):
    sp.Popen(command_final, stdout=sp.PIPE, stderr=sp.PIPE)


def parse_arguments():
    main_help = "Multithreaded VMAF report file generator through FFmpeg.\n"
    parser = argp.ArgumentParser(description=main_help, formatter_class=argp.RawTextHelpFormatter)
    parser.add_argument("VMAF_FILE", type=str, help="VMAF report file.")

    t_help = "Specify number of threads (Default is 2)"

if __name__ == "__main__":
    args = parse_arguments()
    threads = 2
    manager = mp.Manager()
    sema = mp.Semaphore(threads)
    rlock = manager.RLock()
    lis = manager.list()

    files_list

    for root, directories, filenames in os.walk(os.getcwd()):

    run_in_parallel(boring_task, threads, lis, sema, rlock)
