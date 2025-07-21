import re
import urllib.error
import urllib.request
from pathlib import Path
from xml.etree import ElementTree

from .appdirs import user_data_dir

DEFAULT_DICT_PATH = Path(user_data_dir('hyperhyphen', 'hyperhyphen'))

DEFAULT_REPOSITORY = 'https://raw.githubusercontent.com/LibreOffice/dictionaries/master/'

LANGUAGES = [
    "af_ZA", "an_ES", "ar", "be_BY", "bg_BG", "bn_BD", "bo", "br_FR", "bs_BA",
    "ca", "ckb", "cs_CZ", "da_DK", "de", "el_GR", "en", "eo", "es", "et_EE",
    "fa_IR", "fr_FR", "gd_GB", "gl", "gu_IN", "gug", "he_IL", "hi_IN", "hr_HR",
    "hu_HU", "id", "is", "it_IT", "kmr_Latn", "ko_KR", "lo_LA", "lt_LT", "lv_LV",
    "mn_MN", "ne_NP", "nl_NL", "no", "oc_FR", "pl_PL", "pt_BR", "pt_PT", "ro",
    "ru_RU", "si_LK", "sk_SK", "sl_SI", "sq_AL", "sr", "sv_SE", "sw_TZ", "te_IN",
    "th_TH", "tr_TR", "uk_UA", "vi", "zu_ZA",
]


class DictionaryDownloader:
    """Handles downloading and parsing of dictionary metadata from repositories."""

    def __init__(self, repository_url=None):
        self.repository_url = repository_url or DEFAULT_REPOSITORY

    def find_dictionary_location(self, language, **request_args):
        """
        Find the location of a language dictionary from an xcu file from the LibreOffice repo.

        Args:
            language (str): Language code
            **request_args: Additional kwargs (headers, timeout, etc.)

        Returns:
            tuple: (dict_url, locales) or raises IOError if not found
        """
        # Try full language name first, then country code
        for lang_code in [language, language[:2]] if len(language) > 2 else [language]:
            origin_url = f'{self.repository_url.rstrip("/")}/{lang_code}'
            descr_file = self._download_dictionaries_xcu(origin_url, **request_args)

            if descr_file:
                dict_url, locales = self._parse_dictionary_location(descr_file, origin_url, language)
                if dict_url:
                    return dict_url, locales

        raise IOError(f'Cannot find hyphenation dictionary for language {language}.')

    def download_dictionary(self, dict_url, **request_args):
        """Download dictionary content from URL."""
        req = self._create_request(dict_url, **request_args)

        try:
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    raise urllib.error.HTTPError(
                        dict_url, response.status, f'HTTP {response.status}',
                        response.headers, None
                    )
                return response.read()
        except urllib.error.URLError as e:
            raise IOError(f'Failed to download dictionary from {dict_url}: {e}')

    def _download_dictionaries_xcu(self, origin_url, **request_args):
        """
        Try to download dictionaries.xcu from the url.

        Args:
            origin_url (str): Base URL to download from
            **request_args: Additional kwargs (headers, timeout, etc.)

        Returns:
            bytes or None: XML content if successful, None if failed
        """
        url = f'{origin_url}/dictionaries.xcu'
        req = self._create_request(url, **request_args)

        try:
            with urllib.request.urlopen(req) as response:
                return response.read() if response.status == 200 else None
        except urllib.error.URLError:
            return None

    def _create_request(self, url, **request_args):
        """
        Create a urllib.request.Request object with optional parameters.

        Args:
            url (str): URL to request
            **request_args: Optional parameters like headers, timeout

        Returns:
            urllib.request.Request: Configured request object
        """
        # Extract headers if provided
        headers = request_args.get('headers', {})

        # Create request object
        req = urllib.request.Request(url, headers=headers)

        # Add User-Agent if not specified
        if 'User-Agent' not in headers:
            req.add_header('User-Agent', 'Python-urllib/3.x')

        return req

    def _parse_dictionary_location(self, descr_file, origin_url, language):
        """
        Parse the dictionaries.xcu file to find the url of the most appropriate
        hyphenation dictionary.

        Args:
            descr_file (bytes): XML content of the dictionaries.xcu file
            origin_url (str): base url from which the xcu file was downloaded
            language (str): language code

        Returns:
            tuple: (url, locales) or (None, []) if not found
        """
        try:
            descr_tree = ElementTree.fromstring(descr_file)
        except ElementTree.ParseError:
            return None, []

        # Find hyphenation dictionary nodes
        for node in descr_tree.iter('node'):
            if not self._is_hyphenation_node(node):
                continue

            dict_location, locales = self._extract_dictionary_info(node)

            if self._language_matches(language, locales) and dict_location:
                # Strip the '%origin%' prefix and construct full URL
                dict_url = f'{origin_url}/{dict_location[9:]}'
                return dict_url, locales

        return None, []

    def _is_hyphenation_node(self, node):
        """Check if XML node relates to a hyphenation dictionary."""
        return any('hyphdic' in value.lower() for name, value in node.items())

    def _extract_dictionary_info(self, node):
        """Extract dictionary location and locales from XML node."""
        locales = []
        dict_location = None

        for prop in node:
            for prop_key, prop_value in prop.items():
                if prop_value.lower() == 'locations' and prop:
                    # Get first filename from the locations list
                    dict_location = prop[0].text.split()[0]
                elif prop_value.lower() == 'locales' and prop:
                    # Parse locales, converting hyphens to underscores
                    locales = prop[0].text.replace('-', '_').split()

        return dict_location, locales

    def _language_matches(self, language, locales):
        """Check if the requested language matches any of the available locales."""
        return (language in locales or
                any(locale.startswith(f'{language}_') for locale in locales))


class DictionaryStorage:
    """Manages local storage of hyphenation dictionaries by scanning the filesystem."""

    def __init__(self, directory=None):
        """Initialize the storage with a directory.

        Directory is not created if it does not exist, unless it is the default path.
        """
        self._directory = Path(directory or DEFAULT_DICT_PATH)

    @property
    def directory(self):
        """Return the directory where dictionaries are stored."""
        if self._directory == DEFAULT_DICT_PATH and not self._directory.exists():
            self._directory.mkdir(parents=True, exist_ok=True)
        elif not self._directory.exists():
            raise FileNotFoundError(f"Dictionary directory '{self._directory}' does not exist.")

        return self._directory

    def _scan_dictionary_files(self):
        """
        Scan the directory for dictionary files and extract language codes.

        Returns:
            dict: Mapping of language codes to file paths
        """
        dict_files = {}
        pattern = re.compile(r'^hyph_(.+)\.dic$')

        for file_path in self.directory.glob('hyph_*.dic'):
            match = pattern.match(file_path.name)
            if match:
                language_code = match.group(1)
                dict_files[language_code] = file_path

        return dict_files

    def installed_languages(self):
        """Return sorted list of installed language codes."""
        return sorted(self._scan_dictionary_files().keys())

    def is_installed(self, language):
        """Check if a language dictionary is installed."""
        dict_files = self._scan_dictionary_files()

        # Check for exact match first
        if language in dict_files:
            return True

        # Check if any file matches the language prefix (e.g., 'en' matches 'en_US')
        lang_prefix = language.split('_')[0]
        return any(lang.startswith(f'{lang_prefix}_') for lang in dict_files.keys())

    def get_filepath(self, language):
        """Get the filepath for an installed language dictionary."""
        dict_files = self._scan_dictionary_files()

        # Try exact match first
        if language in dict_files:
            return dict_files[language]

        # Try to find a match with the same language prefix
        lang_prefix = language.split('_')[0]
        for lang, path in dict_files.items():
            if lang.startswith(f'{lang_prefix}_'):
                return path

        raise KeyError(f"Language '{language}' is not installed")

    def add_dictionary(self, language, content):
        """Add a new dictionary file."""
        filename = f'hyph_{language}.dic'
        filepath = self.directory / filename

        # Save dictionary file
        with open(filepath, 'wb') as f:
            f.write(content)

        return str(filepath)

    def remove_dictionary(self, language):
        """Remove a language dictionary."""
        dict_files = self._scan_dictionary_files()

        # Try exact match first
        if language in dict_files:
            dict_files[language].unlink()
            return

        # Try to find a match with the same language prefix
        lang_prefix = language.split('_')[0]
        for lang, path in dict_files.items():
            if lang.startswith(f'{lang_prefix}_'):
                path.unlink()
                return


class DictionaryManager:
    """Main class for managing hyphenation dictionaries."""

    def __init__(self, directory=None, repository_url=None):
        """
        Initialize the dictionary manager.

        Args:
            directory (str): Local directory for storing dictionaries
            repository_url (str): URL of the dictionary repository
        """
        self.storage = DictionaryStorage(directory)
        self.downloader = DictionaryDownloader(repository_url)

    def list_installed(self):
        """Return a list of locales for which dictionaries are installed."""
        return self.storage.installed_languages()

    def is_installed(self, language):
        """
        Return True if the dictionary was already installed.

        Args:
            language (str): Language code of the form 'll_CC'.
                          Example: 'en_US' for US English.
        """
        return self.storage.is_installed(language)

    def get_dictionary_path(self, language):
        """Get the file path for an installed dictionary."""
        return str(self.storage.get_filepath(language))

    def install(self, language, use_description=True, overwrite=False, **request_args):
        """
        Download and install a dictionary file.

        Args:
            language (str): code of the form 'll_CC'. Example: 'en_US' for English, USA
            use_description (bool): if True, parse dictionaries.xcu file to
                automatically find the appropriate dictionary.
            overwrite (bool): if True, overwrite any existing dictionary. Default: False
            **request_args: additional kwargs to be passed to `requests.get()` for HTTP configuration

        Returns:
            str: The path to the file that was downloaded or is already installed.
        """
        # Return existing installation if not overwriting
        if not overwrite and self.storage.is_installed(language):
            return str(self.storage.get_filepath(language))

        # Try to find dictionary location from metadata
        dict_url = None

        if use_description:
            try:
                dict_url, locales = self.downloader.find_dictionary_location(language, **request_args)
            except IOError:
                pass  # Fall back to guessing URL

        # Fall back to guessing URL if metadata approach failed
        if not dict_url:
            dict_url = f'{self.downloader.repository_url.rstrip("/")}/{language}/hyph_{language}.dic'

        # Download and install dictionary
        content = self.downloader.download_dictionary(dict_url, **request_args)
        return self.storage.add_dictionary(language, content)

    def uninstall(self, language):
        """
        Uninstall the dictionary of the specified language.

        Args:
            language (str): Language code of the form 'll_CC' whereby ll is the
                language code and CC the country code.
        """
        self.storage.remove_dictionary(language)

_default_manager = None

def get_default_manager():
    """Get the default DictionaryManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = DictionaryManager()
    return _default_manager