# msg format
# |   3 bytes     |   1 byte         |   16 bytes                | 
# |   tag(hash)   |   #section_id    |   part of shared secret   | 


class Message(object):

  def __init__(self, msg=bytes(), tag_len=3, sec_id_len=1, secret_len=16):
    self._tag_len = tag_len
    self._sec_id_len = sec_id_len
    self._secret_len = secret_len
    self._msg_len = tag_len + sec_id_len + secret_len
    if (len(msg) != 0 and len(msg) != self._msg_len):
      raise ValueError(
          "Message length mismatch with total length od tag, sec_id and secret."
      )
    self._msg = msg

  @property
  def msg(self):
    return self._msg

  @msg.setter
  def msg(self, bundle):
    assert (len(bundle) == 3)
    tag, sec_id, secret = bundle

    if (not isinstance(tag, bytes) or \
        not isinstance(sec_id, bytes) or \
        not isinstance(secret, bytes)):
      raise ValueError("Arguments must be byte type")

    if (len(tag) != self._tag_len or \
        len(sec_id) != self._sec_id_len or \
        len(secret) != self._secret_len):
      raise ValueError("Message lenghth mismatch")

    # reset the message since we can't overwrite the bytes
    self._msg = bytes()

    # set tag
    self._msg += tag

    # set section id
    self._msg += sec_id

    # set secret
    self._msg += secret

    assert (len(self._msg) == self._msg_len)

  @property
  def tag(self):
    return self._msg[:self._tag_len]

  @property
  def sec_id(self):
    return self._msg[self._tag_len:self._tag_len + self._sec_id_len]

  @property
  def secret(self):
    return self._msg[self._tag_len + self._sec_id_len:]


if __name__ == "__main__":

  # Test new message
  m = Message()
  tag, sec_id, secret = b"hhh", b"\x01", b"\x99" * 16
  m.msg = tag, sec_id, secret
  assert (m.tag == tag)
  assert (m.sec_id == sec_id)
  assert (m.secret == secret)
  print("Test construct new message passed\n")

  # Test reassign new message
  tag, sec_id, secret = b"lll", b"\x02", b"\x66" * 16
  m.msg = tag, sec_id, secret
  assert (m.tag == tag)
  assert (m.sec_id == sec_id)
  assert (m.secret == secret)
  print("Test reassign new message passed\n")

  # constructor
  b = bytes(b"\x88" * 20)
  m = Message(b)
  tag, sec_id, secret = b"\x88" * 3, b"\x88", b"\x88" * 16
  assert (m.tag == tag)
  assert (m.sec_id == sec_id)
  assert (m.secret == secret)
  print("Test constructing from bytes passed")
