#ifndef PROTOCOL_H
#define PROTOCOL_H

#define DEFAULT_PORT   8080
#define BUFFER_SIZE    8192
#define MAX_PATH_LEN   1024
#define MAX_LINE_LEN   2048
#define MAX_BACKLOG    128

#define METHOD_GET "GET"
#define METHOD_PUT "PUT"

#define ST_OK            200
#define ST_CREATED       201
#define ST_BAD_REQUEST   400
#define ST_FORBIDDEN     403
#define ST_NOT_FOUND     404
#define ST_INTERNAL      500

#define HDR_LENGTH "LENGTH:"

static inline const char *status_message(int code) {
    switch (code) {
        case ST_OK:          return "OK";
        case ST_CREATED:     return "CREATED";
        case ST_BAD_REQUEST: return "BAD REQUEST";
        case ST_FORBIDDEN:   return "FORBIDDEN";
        case ST_NOT_FOUND:   return "NOT FOUND";
        case ST_INTERNAL:    return "INTERNAL ERROR";
        default:             return "UNKNOWN";
    }
}

#endif /* PROTOCOL_H */
