from pyvi import ViTokenizer


class TokenizerHandler:

    def tokenize(self, text):
        return ViTokenizer.tokenize(text)