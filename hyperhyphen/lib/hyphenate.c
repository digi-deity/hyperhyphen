#define _GNU_SOURCE		/* GNU basename() and asprintf() */
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <ctype.h>

#include "hyphen.h"

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

int
main(int argc, char** argv)
{
  HyphenDict *dict;
  int k, i, j, c;
  size_t utf8_k;
  int  nHyphCount;
  char *hyphens;
  char *hyphword;
  char hword[BUFSIZE * 2];
  int arg = 1;
  int opts = 0;
  int optn = 0;
  int optnn = 0;
  int optdd = 0;
  char ** rep;
  int * pos;
  int * cut;

  /* what name to show for usage message */
  progname=strdup(basename(argv[0]));

  if (argc == 1) {
      help();
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
          exit(1);
        }
      }
  }

  char *dictfile;
  dictfile = argv[arg];


  /* load the hyphenation dictionary */
  if ((dict = hnj_hyphen_load(dictfile)) == NULL) {
        fprintf(stderr,
	    "Could not load dictionary file \"%s\"\n",
	    dictfile);
      fflush(stderr);
      exit(1);
  }

  char* word = (char*) malloc(BUFSIZE);

  while (fgets(word, BUFSIZE, stdin) != NULL ) {
    k = strlen(word) - 1;
    word[k] = 0;  // trim newline character

    /* Set aside a buffer to hold hyphen information */
    hyphens = (char *)malloc(k+5);

    /* now actually try to hyphenate the word */
    rep = NULL;
    pos = NULL;
    cut = NULL;
    hword[0] = '\0';

    if (hnj_hyphen_hyphenate3(dict, word, k, hyphens, hword, &rep, &pos, &cut, 4, 3, 2, 2)) {
      free(hyphens);
      fprintf(stderr, "hyphenation error\n");
      exit(1);
    }

    if (optn){
      fprintf(stderr, "%s\n", hyphens);
    } else if (opts && rep) {
      fprintf(stdout,"%s\n", word);
    }
    else if (optnn) {
        if (rep) fprintf(stdout, "%d\n", k);
        else {
            c = 0;
            utf8_k = count_utf8_code_points(word);
            for (i = 0; i < utf8_k - 1; i++) {
              c++;
              if (hyphens[i] % 2 == 1) {
                fprintf(stdout, "%d ", c);
                c = 0;
              }
            }
            fprintf(stdout, "%d\n", c + 1);
        }
    }
    else {
      fprintf(stdout,"%s\n", hword);
    }

    fflush(stdout);

    if (optdd) single_hyphenations(word, hyphens, rep, pos, cut, dict->utf8);

    if (rep) {
        for (i = 0; i < k - 1; i++) {
          if (rep[i]) free(rep[i]);
        }
    free(rep);
    free(pos);
    free(cut);
    }

    free(hyphens);
  }
  free(word);
  hnj_hyphen_free(dict);
  return 0;
}