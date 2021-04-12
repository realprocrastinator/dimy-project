import bgwork

if __name__ == "__main__":
  # uni test
  import time

  bgworker = bgwork.BackgroundWorker()

  @bgworker.myjob("hello1", 1, True)
  def print_hello1():
    print("Hello1")
    time.sleep(1)

  @bgworker.myjob("world1", 1, True)
  def print_world1():
    print("World1")
    time.sleep(1)

  @bgworker.myjob("hello2", 2, True)
  def print_hello2():
      print("Hello2")
      time.sleep(2)
  
  @bgworker.myjob("hello3", 3, True)
  def print_hello3():
      print("Hello3")
      time.sleep(3)

  bgworker.start()
  
  stopped = False
  while not stopped:
    print("This is in the main")
    cmd = input(">")
    if cmd == "s":
      stopped = True
      bgworker.stop()