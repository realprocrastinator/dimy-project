import array
import mmh3
import math

# This is only used for debuging in this file scope
# Cross file scope should use logging
DEBUG = False
if DEBUG:
  import uuid


# TODO(Jiawei):
# 1) Should make array sector size configurable depanding on the type supported by array
class BloomFilter(object):
  # class wide variables
  DEFAULTBITS = 800000
  DEFAULTHASHFUNS = 3
  DEFAULTARRSZ = 8
  DEFAULTHASH = mmh3.hash

  # By default we are going to use murmurhash
  def __init__(self,
               nbits=DEFAULTBITS,
               hash_func=DEFAULTHASH,
               hash_times=DEFAULTHASHFUNS,
               arrsz=DEFAULTARRSZ):
    self._nbits = nbits
    self._arrsz = arrsz
    self._narrs = (nbits + arrsz - 1) // arrsz
    # 'L' -> unsigned long type max 4 bytes
    self.arr = array.array('B', [0]) * self._narrs
    self._hash_func = hash_func
    self._hash_times = hash_times
    # number of elements have been inserted
    self._neles_inserted = 0

  def insert(self, data):
    if (DEBUG):
      print(f"Inserting data: {data}")
    for arr_idx, arr_bit_idx in self.hash_gen(data):
      self.arr[arr_idx] |= (1 << arr_bit_idx)
    if (DEBUG):
      with open(f"dump{uuid.uuid1().hex[:6]}.txt", 'w') as f:
        f.write(f"After insertion: {self.arr}")
    self._neles_inserted += 1

  def contains(self, data):
    return all(self.arr[arr_idx] & (1 << arr_bit_idx)
               for arr_idx, arr_bit_idx in self.hash_gen(data))

  def remove(self, data):
    if (DEBUG):
      print(f"Removing data: {data}")
    for arr_idx, arr_bit_idx in self.hash_gen(data):
      self.arr[arr_idx] &= (~(1 << arr_bit_idx))
    if (DEBUG):
      with open("dump_BF.txt", 'w') as f:
        f.write(f"After insertion: {self.arr}")
    self._neles_inserted -= 1

  # The semantic of union is the second bloomfilter will be union into the caller of the union
  # return True on success, Flase on error
  def union(self, bloomfilter):
    # check whther the `self` has the same shape and attributes as `bloomfilter`
    if (not (self._nbits == bloomfilter._nbits and \
             self._hash_times == bloomfilter._hash_times and \
             self._hash_func == bloomfilter._hash_func)):
      print("Can't union two bloomfilters with different attributes")
      return False
    else:
      for i, b in enumerate(bloomfilter.arr):
        self.arr[i] |= b

      if (DEBUG):
        with open(f"union-dump{uuid.uuid1().hex[:6]}.txt", 'w') as f:
          f.write(f"After insertion: {self.arr}")

      return True

  def intersect(self, bloomfilter):
    assert (not "Not implemented yet")

  # return bytes needed in total
  @property
  def size_in_bytes(self):
    return (self._nbits + 8 - 1) // 8

  @property
  def fs_prob(self):
    return self._calculate_fs_prob()

  def _calculate_fs_prob(self):
    return (1 - math.exp(-self._hash_times * self._neles_inserted /
                         self._nbits))**self._hash_times

  def do_hash(self, *args):
    hash_value = self._hash_func(*args)
    raw_idx = hash_value % self._nbits
    arr_idx = raw_idx // self._arrsz
    arr_bit_idx = raw_idx % self._arrsz

    if (DEBUG):
      print(f"Hash Value: {hash_value}")
      print(f"Raw Idx: {raw_idx}")
      print(f"Arr Idx: {arr_idx}")
      print(f"Arr Bit Idx: {arr_bit_idx}")

    return arr_idx, arr_bit_idx

  def hash_gen(self, data):
    # Assume we use murmur hash here, the second argument is the seed
    # TODO(Jiawei): Make it generic so that let the user define which hash func to use
    for seed in range(self._hash_times):
      arr_idx, arr_bit_idx = self.do_hash(data, seed)
      yield arr_idx, arr_bit_idx


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
      hash_set.add((mmh3.hash(state, i) % bf.DEFAULTBITS // bf.DEFAULTARRSZ,
                    mmh3.hash(state, i) % bf.DEFAULTBITS % bf.DEFAULTARRSZ))

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
  word_gen = lambda x: "".join(c for _ in range(x)
                               for c in random.choice(ascii_letters))
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
  print("Test remove data passed\n")
