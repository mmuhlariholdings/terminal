/*
 * test_framework.h: a minimal assert-and-count test helper for the host-side unit tests (plain C, no dependencies).
 * Each test program calls CHECK(...) and ends with `return test_summary("name");` (non-zero exit = failure, for ctest).
 */
#ifndef TERMINAL_TEST_FRAMEWORK_H
#define TERMINAL_TEST_FRAMEWORK_H

#include <stdio.h>

static int test_checks = 0;
static int test_failures = 0;

#define CHECK(condition)                                                                       \
    do {                                                                                       \
        test_checks++;                                                                         \
        if (!(condition)) {                                                                    \
            test_failures++;                                                                   \
            fprintf(stderr, "%s:%d: check failed: %s\n", __FILE__, __LINE__, #condition);      \
        }                                                                                      \
    } while (0)

#define CHECK_EQUAL(expected, actual)                                                          \
    do {                                                                                       \
        long long expected_value = (long long)(expected);                                      \
        long long actual_value = (long long)(actual);                                          \
        test_checks++;                                                                         \
        if (expected_value != actual_value) {                                                  \
            test_failures++;                                                                   \
            fprintf(stderr, "%s:%d: %s: expected %lld, got %lld\n", __FILE__, __LINE__,        \
                    #actual, expected_value, actual_value);                                    \
        }                                                                                      \
    } while (0)

static int test_summary(const char *name)
{
    printf("%s: %d checks, %d failed\n", name, test_checks, test_failures);
    return test_failures == 0 ? 0 : 1;
}

#endif
