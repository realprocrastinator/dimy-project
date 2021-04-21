import array
import mmh3
import math
import sys

# This is only used for debuging in this file scope
# Cross file scope should use logging
DEBUG = False
if DEBUG:
  import uuid

from pathlib import Path  # if you haven't already done so

# Add toor dir of the src tree to the syspath, so that we can use absolute import
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from bfmng.bloomfilter import BloomFilter

if __name__ == "__main__":
  # Small unit testing
  from string import ascii_letters
  import random

  states = '''Alabama Alaska Arizona Arkansas California Colorado Connecticut
    Delaware Florida Georgia Hawaii Idaho Illinois Indiana Iowa Kansas
    Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota
    Mississippi Missouri Montana Nebraska Nevada NewHampshire NewJersey
    NewMexico NewYork NorthCarolina NorthDakota Ohio Oklahoma Oregon
    Pennsylvania RhodeIsland SouthCarolina SouthDakota Tennessee Texas Utah
    Vermont Virginia Washington WestVirginia Wisconsin Wyoming'''.split()

  bf = BloomFilter()
  assert (bf.fs_prob == 0)

  hash_set = set()
  for state in states:
    # book keeping each hash
    for i in range(bf._hash_times):
      hash_set.add((mmh3.hash(state, i) % bf.DEFAULTBITS // bf.DEFAULTARRSZ, mmh3.hash(state, i) % bf.DEFAULTBITS % bf.DEFAULTARRSZ))

    bf.insert(state)

  print(f"Now the FP is: {bf.fs_prob}")
  hash_funcs = 3
  neles = len(states)
  nbits = bf.DEFAULTBITS
  assert (bf.fs_prob == (1 - math.exp(-hash_funcs * neles / nbits))**hash_funcs)
  print("Test: false positive calculation passed\n")

  print("Testing `contains` method")
  print("Testing searching for inserted data")
  assert (all(bf.contains(d) for d in states))
  print("Test: searching inserted data passed\n")

  print("Testing searching for not insterted data")
  # generating a random word list for each word has length == max len of the word in states + 1
  nwords = 50
  word_gen = lambda x: "".join(c for _ in range(x) for c in random.choice(ascii_letters))
  word_list = [word_gen(len(max(states, key=len)) + 1) for _ in range(nwords)]

  # Shouldn't contain any in the bf!
  for w in word_list:
    # Shouldn't have this word but might due to false positive?
    if bf.contains(w):
      # Explicilty check if that is the case!
      assert(all((mmh3.hash(state, i) % bf.DEFAULTBITS // bf.DEFAULTARRSZ, \
                  mmh3.hash(state, i) % bf.DEFAULTBITS % bf.DEFAULTARRSZ) in hash_set \
                  for i in range(bf._hash_times)))
  print("Test not inserted data passed\n")

  print("Testing msc functionalities")
  assert (bf.size_in_bytes == (bf.DEFAULTBITS // 8))
  print("Test: arr size in bytes passed")

  print("Testing union functionalies")
  bf2 = BloomFilter()
  assert (bf2.fs_prob == 0)
  for word in word_list:
    bf2.insert(word)

  assert (bf.union(bf2))
  # Shouldn't contain any in the bf!
  assert (all(bf.contains(d) for d in word_list))
  print("Test union inserted data passed\n")

  print("Testing `remove` functionalies")
  for word in word_list:
    bf.remove(word)

  # After removing shouldn't contain any in the bf!
  for w in word_list:
    # Shouldn't have this word but might due to false positive?
    if bf.contains(w):
      # Explicilty check if that is the case!
      assert(all((mmh3.hash(state, i) % bf.DEFAULTBITS // bf.DEFAULTARRSZ, \
                  mmh3.hash(state, i) % bf.DEFAULTBITS % bf.DEFAULTARRSZ) in hash_set \
                  for i in range(bf._hash_times)))
  print("Test remove data passed")
