import os
from tokenizers.models import BPE
from tokenizers import Tokenizer
from tokenizers.decoders import ByteLevel as ByteLevelDecoder
from tokenizers.normalizers import NFKC, Sequence
from tokenizers.pre_tokenizers import ByteLevel
from tokenizers.trainers import BpeTrainer
import argparse


__author__ = "Risto Luukkonen"


class BPE_token(object):
    def __init__(self):
        self.tokenizer = Tokenizer(BPE())
        self.tokenizer.normalizer = Sequence([
            NFKC()
        ])
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
             self.tokenizer.save(location+".json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data',type=str)
    parser.add_argument('--output_dir',type=str,required=True)
    parser.add_argument('--vocab_size',type=int,default=50257)
    parser.add_argument('--save_vocab_only',default=True, action='store_true',help="If true, saves merges.txt and vocab.json,\n \
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

    tokenizer = BPE_token()
    # train the tokenizer model
    tokenizer.bpe_train(args.vocab_size, paths)
    # saving the tokenized data in our specified folder
    tokenizer.save_tokenizer(args.output_dir)


if __name__=='__main__':
   main()
