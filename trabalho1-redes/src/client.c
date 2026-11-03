#include "protocol.h"
#include "common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

static int connect_server(const char *ip, int port) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    if (inet_pton(AF_INET, ip, &addr.sin_addr) <= 0) { close(fd); return -1; }
    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) { close(fd); return -1; }
    return fd;
}

static void log_csv(const char *csv, const char *tag, const char *op,
                    long bytes, double elapsed, int status) {
    if (!csv) return;
    int novo = (access(csv, F_OK) != 0);
    FILE *f = fopen(csv, "a");
    if (!f) return;
    if (novo) fprintf(f, "tag,operacao,bytes,tempo_s,vazao_mbps,status\n");
    double mbps = (elapsed > 0) ? (bytes * 8.0) / (elapsed * 1e6) : 0.0;
    fprintf(f, "%s,%s,%ld,%.6f,%.4f,%d\n", tag ? tag : "-", op, bytes, elapsed, mbps, status);
    fclose(f);
}

static int do_get(int fd, const char *remote, const char *outpath,
                  long *out_bytes, int *out_status) {
    char req[MAX_LINE_LEN];
    int n = snprintf(req, sizeof(req), "%s %s\r\n\r\n", METHOD_GET, remote);
    if (send_all(fd, req, (size_t)n) < 0) return -1;
    char statusline[MAX_LINE_LEN];
    if (recv_line(fd, statusline, sizeof(statusline)) <= 0) return -1;
    int code = atoi(statusline);
    *out_status = code;
    if (code != ST_OK) {
        recv_line(fd, statusline, sizeof(statusline));
        fprintf(stderr, "Erro do servidor: %d %s\n", code, status_message(code));
        return -1;
    }
    char lenline[MAX_LINE_LEN]; long length = -1;
    recv_line(fd, lenline, sizeof(lenline));
    sscanf(lenline, "%*s %ld", &length);
    char blank[MAX_LINE_LEN];
    recv_line(fd, blank, sizeof(blank));
    int outfd = open(outpath, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (outfd < 0) { perror("open saida"); return -1; }
    if (recv_file(fd, outfd, length) < 0) { close(outfd); return -1; }
    close(outfd);
    *out_bytes = length;
    return 0;
}

static int do_put(int fd, const char *localpath, const char *remote,
                  long *out_bytes, int *out_status) {
    long fsize = file_size(localpath);
    if (fsize < 0) { fprintf(stderr, "Arquivo local nao existe: %s\n", localpath); return -1; }
    int infd = open(localpath, O_RDONLY);
    if (infd < 0) { perror("open local"); return -1; }
    char header[MAX_LINE_LEN];
    int n = snprintf(header, sizeof(header), "%s %s\r\n%s %ld\r\n\r\n",
                     METHOD_PUT, remote, HDR_LENGTH, fsize);
    if (send_all(fd, header, (size_t)n) < 0) { close(infd); return -1; }
    if (send_file(fd, infd, fsize) < 0) { close(infd); return -1; }
    close(infd);
    char statusline[MAX_LINE_LEN];
    if (recv_line(fd, statusline, sizeof(statusline)) <= 0) return -1;
    int code = atoi(statusline);
    *out_status = code;
    char blank[MAX_LINE_LEN];
    recv_line(fd, blank, sizeof(blank));
    if (code != ST_CREATED) {
        fprintf(stderr, "Erro do servidor: %d %s\n", code, status_message(code));
        return -1;
    }
    *out_bytes = fsize;
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc < 6) {
        fprintf(stderr, "Uso:\n"
            "  %s <ip> <porta> GET <remoto> <saida_local> [--csv f.csv] [--tag r]\n"
            "  %s <ip> <porta> PUT <local> <dest_remoto> [--csv f.csv] [--tag r]\n",
            argv[0], argv[0]);
        return 1;
    }
    const char *ip = argv[1];
    int port = atoi(argv[2]);
    const char *op = argv[3];
    const char *arg4 = argv[4];
    const char *arg5 = argv[5];
    const char *csv = NULL, *tag = NULL;
    for (int i = 6; i < argc - 1; i++) {
        if (strcmp(argv[i], "--csv") == 0) csv = argv[++i];
        else if (strcmp(argv[i], "--tag") == 0) tag = argv[++i];
    }
    int fd = connect_server(ip, port);
    if (fd < 0) { fprintf(stderr, "Falha ao conectar em %s:%d\n", ip, port); return 1; }
    long bytes = 0; int status = 0; int rc;
    double t0 = now_sec();
    if (strcmp(op, "GET") == 0) rc = do_get(fd, arg4, arg5, &bytes, &status);
    else if (strcmp(op, "PUT") == 0) rc = do_put(fd, arg4, arg5, &bytes, &status);
    else { fprintf(stderr, "Operacao invalida: %s\n", op); close(fd); return 1; }
    double elapsed = now_sec() - t0;
    close(fd);
    if (rc == 0) {
        double mbps = (elapsed > 0) ? (bytes * 8.0) / (elapsed * 1e6) : 0.0;
        printf("[%s] OK | %ld bytes | %.4f s | %.4f Mbps\n", op, bytes, elapsed, mbps);
        log_csv(csv, tag, op, bytes, elapsed, status);
        return 0;
    } else {
        log_csv(csv, tag, op, bytes, elapsed, status);
        return 1;
    }
}
