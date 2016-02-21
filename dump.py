#!/usr/bin/env python
# encoding=utf-8
__author__ = 'pfCao'

import subprocess
import os
import time
import argparse

# config
REMOTE_FOLDER = "/data/local/tmp"  # do not change this variable
DUMP_TOOL_PATH_REMOTE = REMOTE_FOLDER + "/dumpMemory"
DUMP_FILE_REMOTE = REMOTE_FOLDER + "/dumped_memory.raw"  # do not change this variable

DUMP_TOOL_PATH_LOCAL = os.path.join(os.getcwd(), "bin", "dumpMemory")
DUMP_FILE_LOCAL = os.path.join(os.getcwd(), "dumped_memory.raw")


def hex_str(int_num):
    _hex = hex(int_num)
    if _hex.endswith("L") or _hex.endswith("l"):
        return _hex[0:-1]
    return _hex


class DumpMemory:
    def __init__(self, target_pid, start_addr, end_addr, output_path=DUMP_FILE_LOCAL):
        self.target_pid = target_pid
        self.output_path = output_path
        self.start_addr = start_addr
        self.end_addr = end_addr
        self.tmp_dump_files_list = []

    def dump(self):
        try:
            # push dumpMemory to emulator
            self.__run_adb_cmd(["push", DUMP_TOOL_PATH_LOCAL, REMOTE_FOLDER])
            self.__run_adb_cmd(["shell", "chmod", "777", DUMP_TOOL_PATH_REMOTE])

            # clear
            self.__run_adb_cmd(["shell", "rm", DUMP_FILE_REMOTE])
            # dump
            self.__dump_chunks()
            # save file
            self.__merge_files()
        except Exception, ex:
            print ex
            return False
        return True

    def __dump_chunks(self):
        dump_size = int(self.end_addr, 16) - int(self.start_addr, 16)
        chunk_size = 5 * 1024 * 1024
        for i in xrange(0, dump_size / chunk_size):
            start_addr = hex_str(int(self.start_addr, 16) + i * chunk_size)
            end_addr = hex_str(int(start_addr, 16) + chunk_size)
            self.__do_dump(start_addr, end_addr, str(time.time()))

        if dump_size % chunk_size != 0:
            start_addr = hex_str(int(self.end_addr, 16) - dump_size % chunk_size)
            end_addr = self.end_addr
            self.__do_dump(start_addr, end_addr, str(time.time()))

    def __do_dump(self, start_addr, end_addr, tmp_file_name):
        # run dumpMemory
        ret = self.__run_adb_cmd(["shell", DUMP_TOOL_PATH_REMOTE, self.target_pid, start_addr, end_addr])
        if ret[0]:
            raise Exception(ret[0])

        self.__run_adb_cmd(["pull", DUMP_FILE_REMOTE, tmp_file_name])  # pull dumped memory to localhost
        self.tmp_dump_files_list.append(tmp_file_name)

    def __merge_files(self):
        with open(self.output_path, "wb") as output_file:
            for tmp_file_name in self.tmp_dump_files_list:
                if not os.path.exists(tmp_file_name):
                    continue
                with open(tmp_file_name, "rb") as tmp_file:
                    output_file.write(tmp_file.read())
                os.remove(tmp_file_name)

    def __run_adb_cmd(self, cmd):
        try:
            args = ["adb"]
            args.extend(cmd)
            process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ret = process.communicate()
            return ret
        except Exception, ex:
            print ret
            raise Exception(ex)


def main():
    arg_parser = argparse.ArgumentParser(description="Dump Memory")
    arg_parser.add_argument("-pid", dest="pid", required=True,type=int, help="The process pid")
    arg_parser.add_argument("-saddr", dest="start_addr",required=True, help="the start address in hexadecimal format")
    arg_parser.add_argument("-eaddr", dest="end_addr", required=True, help="the end address in hexadecimal format")
    args = arg_parser.parse_args()

    target_pid = args.pid
    start_addr = args.start_addr
    end_addr = args.end_addr
    try:
        if int(start_addr,16)>=int(end_addr,16):
            print "Parameters error!\n End address must be larger than start address."
            return
    except Exception,ex:
        print "Parameters error!\n Address must be in hexadecimal format.\n Please check the format of start address or end address.\n\n"
        arg_parser.print_help()
        return

    dump_memory = DumpMemory(str(target_pid), start_addr, end_addr)

    print "start dumping memory..."
    if dump_memory.dump():
        print "finished.\nThe dumped memory is saved to "+dump_memory.output_path
    else:
        print "dump failed!"


if __name__ == '__main__':
    main()
