#define _GNU_SOURCE		/* GNU basename() and asprintf() */
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <ctype.h>

#include "hyphen.h"

#ifdef _MSC_VER
#define DLL_EXPORT  __declspec( dllexport )
#else
#define DLL_EXPORT
#endif

#define BUFSIZE 1000

char *progname;			/* short program name, set by main */
void help() {
  printf("Usage:\n");
  printf("%s [-s | -d | -n] path/to/dictionary.dic\n", progname);
  printf("\t-s = Only hyphenate using standard hyphenations\n");
  printf("\t-d = hyphenation with listing of the possible hyphenations\n");
  printf("\t-n = print hyphenation vector (as returned by libhyphen)\n");
  printf("\t-nn = print hyphenation vector (number of bytes for each word-chunk)\n");
}

/* get a pointer to the nth 8-bit or UTF-8 character of the word */
char * hindex(char * word, int n, int utf8) {
  int j = 0;
  while (j < n) {
    j++;
    word++;
    while (utf8 && ((((unsigned char) *word) >> 6) == 2)) word++;
  }
  return word;
}

/* list possible hyphenations with -d option (example for the usage of the hyphenate2() function) */
void single_hyphenations(char * word, char * hyphen, char ** rep, int * pos, int * cut, int utf8) {
  int i, k, j = 0;
  char r;
  for (i = 0; (i + 1) < strlen(word); i++) {
    if (utf8 && ((((unsigned char) word[i]) >> 6) == 2)) continue;
    if ((hyphen[j] & 1)) {
      if (rep && rep[j]) {
	k = hindex(word, j - pos[j] + 1, utf8) - word;
	r = word[k];
	word[k] = 0;
	printf(" - %s%s", word, rep[j]);
	word[k] = r;
	printf("%s\n", hindex(word + k, cut[j], utf8));
      } else {
	k = hindex(word, j + 1, utf8) - word;
	r = word[k];
	word[k] = 0;
	printf(" - %s=", word);
	word[k] = r;
	printf("%s\n", word + k);
      }
    }
    j++;
  }
}

size_t count_utf8_code_points(const char *s) {
    size_t count = 0;
    while (*s) {
        count += (*s++ & 0xC0) != 0x80;
    }
    return count;
}


DLL_EXPORT int parse_word(HyphenDict *dict, char *word, char *out, int k, int kk, int optn, int opts, int optnn, int optdd) {
    int i, j, c, n, z = 0;
    size_t utf8_k;
    int  nHyphCount;
    char *hyphens;
    char *hyphword;
    char hword[BUFSIZE * 2];
    char ** rep = NULL;
    int * pos = NULL;
    int * cut = NULL;

    /* Set aside a buffer to hold hyphen information */
    hyphens = (char *) malloc(k+5);
    if (!hyphens) return -2;

    hword[0] = '\0';

    if (hnj_hyphen_hyphenate3(dict, word, k, hyphens, hword, &rep, &pos, &cut, 4, 3, 2, 2)) {
      free(hyphens);
      // Do not exit, return error code
      return -1;
    }

    if (optn){
      z = snprintf(out, kk, "%s\n", hyphens);
    } else if (opts && rep) {
      z = snprintf(out, kk, "%s\n", word);
    }
    else if (optnn) {
        char remainder = BUFSIZE;
        if (rep) {
            z = snprintf(out, kk, "%d\n", k);
        }
        else {
            z = 0;
            c = 0;
            utf8_k = count_utf8_code_points(word);
            for (i = 0; i < utf8_k - 1; i++) {
              c++;
              if (hyphens[i] % 2 == 1) {
                int n = snprintf(out, kk, "%d ", c);
                if (n < 0 || n >= kk) break;
                z += n;
                out += n;
                kk -= n;
                c = 0;
              }
            }
            int n = snprintf(out, kk, "%d\n", c + 1);
            if (n > 0 && n < kk) z += n;
        }
    }
    else {
      z = snprintf(out, kk, "%s\n", hword);
    }

    if (optdd) single_hyphenations(word, hyphens, rep, pos, cut, dict->utf8);

    if (rep) {
        for (i = 0; i < k - 1; i++) {
          if (rep[i]) free(rep[i]);
        }
        free(rep);
    }
    if (pos) free(pos);
    if (cut) free(cut);

    free(hyphens);

    return z;
}

DLL_EXPORT int parse_words(HyphenDict *dict, char *words, char *out, int n, int kk, int optn, int opts, int optnn, int optdd) {
    int k, z;

    for (int i = 0; i < n; i++) {
        k = strlen(words);
        if (k < 0 || kk <= 0) return -2;

        z = parse_word(dict, words, out, k, kk, optn, opts, optnn, optdd);
        if (z < 0) return z;

        words += k + 1;
        out += z;
        kk -= z;

        if (kk <= 0) {
            return -1;
        }
    }

    return 0;
}

/* CLI program for when compiled as executable */
int main(int argc, char** argv)
{
  HyphenDict *dict;
  int k;
  int arg = 1;
  int opts = 0;
  int optn = 0;
  int optnn = 0;
  int optdd = 0;
  char hword[BUFSIZE * 2];

  /* what name to show for usage message */
  progname=strdup(argv[0]);

  if (argc == 1) {
      help();
      free(progname);  // Add cleanup
      exit(1);
  }

  /* first parse the command line options */
  while (arg < argc - 1) {
    if (argv[arg]) {
        if (strcmp(argv[arg], "-s") == 0) {
          opts = 1;
          arg++;
        }
        else if (argv[arg] && strcmp(argv[arg], "-n") == 0) {
          optn = 1;
          arg++;
        }
        else if (argv[arg] && strcmp(argv[arg], "-nn") == 0) {
          optnn = 1;
          opts = 1;  // This only works for standard hyphenation
          arg++;
        }
        else if (argv[arg] && strcmp(argv[arg], "-d") == 0) {
          optdd = 1;
          arg++;
        }
        else {
          help();
          free(progname);  // Add cleanup
          exit(1);
        }
      }
  }

  char *dictfile;
  dictfile = argv[arg];

  if ((dict = hnj_hyphen_load(dictfile)) == NULL) {
        fprintf(stderr,
     "Could not load dictionary file \"%s\"\n",
     dictfile);
      fflush(stderr);
      free(progname);  // Add cleanup
      exit(1);
  }

  char* word = (char*) malloc(BUFSIZE);
  char out[BUFSIZE * 2];

  while (fgets(word, BUFSIZE, stdin) != NULL ) {
    k = strlen(word) - 1;
    word[k] = 0;
    parse_word(dict, word, out, k, BUFSIZE*2, optn, opts, optnn, optdd);
    fputs(out, stdout);
    fflush(stdout);
  }

  free(word);
  free(progname);  // Add cleanup
  hnj_hyphen_free(dict);
  return 0;
}