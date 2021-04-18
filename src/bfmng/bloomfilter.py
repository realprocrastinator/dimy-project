import array
import mmh3
import math

# This is only used for debuging in this file scope
# Cross file scope should use logging
DEBUG = False
if DEBUG:
  import uuid


class BloomFilter(object):
  # class wide variables
  # in bits
  DEFAULTBITS = 800000
  DEFAULTARRSZ = 8
  DEFAULTHASHFUNS = 3
  DEFAULTHASH = mmh3.hash

  # By default we are going to use murmurhash
  def __init__(self, nbits=DEFAULTBITS, hash_func=DEFAULTHASH, hash_times=DEFAULTHASHFUNS, arrsz=DEFAULTARRSZ):
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
    return all(self.arr[arr_idx] & (1 << arr_bit_idx) for arr_idx, arr_bit_idx in self.hash_gen(data))

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
    return (1 - math.exp(-self._hash_times * self._neles_inserted / self._nbits))**self._hash_times

  def do_hash(self, *args):
    hash_value = self._hash_func(*args)
    raw_idx = hash_value % self._nbits
    print("Inserting @position:", raw_idx)

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

