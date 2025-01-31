#ifdef _MSC_VER
#define DLL_EXPORT  __declspec( dllexport )
#else
#define DLL_EXPORT
#endif

DLL_EXPORT int parse_word(HyphenDict *dict, char *word, int k, int optn, int opts, int optnn, int optdd)
DLL_EXPORT int parse_words(HyphenDict *dict, char *words, char *out, int n, int kk, int optn, int opts, int optnn, int optdd)