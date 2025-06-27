from hyperhyphen.dictionaries import DictionaryManager

# Test to download the US dictionary
def test_download_us_dictionary():
    dm = DictionaryManager()

    # This will download the US dictionary if it is not already installed
    dm.install("en_US")

    # Check if the dictionary file exists
    assert "en_US" in dm.list_installed()
    assert dm.is_installed("en_US")

# Test removal of the US dictionary
def test_remove_us_dictionary():
    dm = DictionaryManager()

    dm.install("en_US")
    dm.uninstall("en_US")

    # Check if the dictionary file has been removed
    assert "en_US" not in dm.list_installed()
    assert not dm.is_installed("en_US")