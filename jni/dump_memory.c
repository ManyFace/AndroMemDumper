#include <stdio.h>
#include<sys/ptrace.h>
#include <sys/wait.h>
#include <errno.h>

#define BUF_SIZE 4096

union unit
{
	uint32_t int_val;
	char char_array[sizeof(long)];
};

void dump(pid_t target_pid, uint_t start_addr, uint_t end_addr, FILE *fp)
{
	uint8_t buf[BUF_SIZE];
	uint32_t dump_size = end_addr - start_addr;
	uint32_t i = 0;
	uint32_t j = dump_size / 4;
	uint32_t remain = dump_size % 4;
	uint32_t total_dump_bytes = 0;
	union unit tmp_data;

	for (i = 0; i < j; i++)
	{
		tmp_data.int_val = ptrace(PTRACE_PEEKTEXT, target_pid, start_addr + total_dump_bytes, 0);
		memcpy(buf + total_dump_bytes % BUF_SIZE, tmp_data.char_array, 4);
		total_dump_bytes += 4;
		if (total_dump_bytes % BUF_SIZE == 0)
		{
			fwrite(buf, BUF_SIZE, 1, fp);
		}
	}
	if (total_dump_bytes % BUF_SIZE != 0)
	{
		fwrite(buf, total_dump_bytes % BUF_SIZE, 1, fp);
	}

	if (remain > 0)
	{
		tmp_data.int_val = ptrace(PTRACE_PEEKTEXT, target_pid, start_addr + total_dump_bytes, 0);
		total_dump_bytes += remain;
		fwrite(tmp_data.char_array, remain, 1, fp);
	}
}

int main(int argc, char*argv[])
{
	if (argc != 4)
	{
		fprintf(stderr, "the number of parameter error!\n");
		return -1;
	}

	//parse paramters
	pid_t target_pid = atoi(argv[1]);
	uint32_t start_addr = 0;
	uint32_t end_addr = 0;
	sscanf(argv[2], "%X", &start_addr);
	sscanf(argv[3], "%X", &end_addr);

	//attach target process
	if (ptrace(PTRACE_ATTACH, target_pid, NULL, NULL) < 0)
	{
		fprintf(stderr, "attach failed! %s\n", strerror(errno));
		return -1;
	}
	waitpid(target_pid, NULL, WUNTRACED); //wait pid stop

	char save_file_path[] = "/data/local/tmp/dumped_memory.raw";
	FILE * fp = fopen(save_file_path, "wb");
	if (NULL == fp)
	{
		fprintf(stderr, "open file failed! %s\n", strerror(errno));
		return -1;
	}

	//dump memory
	dump(target_pid, start_addr, end_addr, fp);

	fclose(fp);

	//detach process
	if (ptrace(PTRACE_DETACH, target_pid, NULL, NULL) < 0)
	{
		fprintf(stderr, "detach failed! %s\n", strerror(errno));
		return -1;
	}

	return 0;
}

