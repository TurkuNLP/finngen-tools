import os
from tokenizers.models import BPE
from tokenizers import Tokenizer
from tokenizers.decoders import ByteLevel as ByteLevelDecoder
from tokenizers.normalizers import NFC, NFD, NFKC, NFKD, Sequence
from tokenizers.pre_tokenizers import ByteLevel
from tokenizers.trainers import BpeTrainer
from transformers import PreTrainedTokenizerFast
import argparse


__author__ = "Risto Luukkonen"


NORMALIZER = {
    'NFC': NFC,
    'NFD': NFD,
    'NFKC': NFKC,
    'NFKD': NFKD,
}


class BPETokenizer(object):
    def __init__(self, normalization):
        self.tokenizer = Tokenizer(BPE())
        if normalization is not None:
            normalizer = NORMALIZER[normalization]()
            self.tokenizer.normalizer = Sequence([normalizer])
        self.tokenizer.pre_tokenizer = ByteLevel()
        self.tokenizer.decoder = ByteLevelDecoder()

    def bpe_train(self,vocab_size, paths):
        trainer = BpeTrainer(vocab_size=vocab_size, show_progress=True, initial_alphabet=ByteLevel.alphabet(), special_tokens=["<|endoftext|>"])
        self.tokenizer.train(paths,trainer)

    def save_tokenizer(self, location,vocab_only=True):
        if not os.path.exists(location):
            os.makedirs(location)
        if vocab_only:
           self.tokenizer.model.save(location)
        else:
            fast_tokenizer = PreTrainedTokenizerFast(
                tokenizer_object=self.tokenizer
            )
            fast_tokenizer.save_pretrained(location)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data',type=str)
    parser.add_argument('--output_dir',type=str,required=True)
    parser.add_argument('--normalization', default=None, choices=NORMALIZER.keys())
    parser.add_argument('--vocab_size',type=int,default=50257)
    parser.add_argument('--save_vocab_only',default=False, action='store_true',help="If true, saves merges.txt and vocab.json,\n \
                        else saves a single file that can be load with Tokenizer.from_file() but isn't so easy to use with AutoTokenizer-api")
    #TODO see how Tokenizer.from_file() can be used with transformers.AutoTokenizer()

    args = parser.parse_args()

    from pathlib import Path

    if os.path.isdir(args.data):
        paths = [str(x) for x in Path(path).glob("**/*.txt")]
        if len(paths)>200:
            print(f"WARNING: file count is {len(paths)}, trainer may take a while...")
    elif args.data.split('.')[-1]!='txt':
        print("data format needed is plain text with  .txt-suffix")
        sys.exit(1)
    else:
        paths = [args.data]

    tokenizer = BPETokenizer(args.normalization)
    # train the tokenizer model
    tokenizer.bpe_train(args.vocab_size, paths)
    # saving the tokenized data in our specified folder
    tokenizer.save_tokenizer(args.output_dir, args.save_vocab_only)


if __name__=='__main__':
   main()
