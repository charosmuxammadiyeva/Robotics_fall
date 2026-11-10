import sys
import time
import random
import math

# Lab 9 - gyroscope parameters. Charos, 240070. Option A (open loop, in-place rotation).
# Same sequence as charos_240070_lab9.qrs, written as a TRIK Studio Python program so it can
# also log readRawData() (gz_raw) and the phase label in every line. No processing on the robot.
#
#   warmup     2 min   still, not logged
#   static     3 min   still, motors off, logged
#   sin       36 s     u = sat(A sin(2 pi t / 4 s)), A = 30 -> 60 -> 150 %
#   rect      36 s     u = sat(A sign(sin(2 pi t / 4 s))), same A
#   rest       3 s     motors off, logged
#   slipcheck 20 s     still - measure the tape-mark angle now
#   beep, hand 30 s    spin the robot by hand on an office chair (range backup, section 3)
#   beep, end
#
# Wheel powers: right M3 = u, left M4 = -u (u > 0 turns CCW). Encoders: left E4, right E3 (as in Gyro_demo).

class Program():
  __interpretation_started_timestamp__ = time.time() * 1000

  FILE = "lab9_gyro.csv"
  PERIOD_MS = 10          # one line every ~10 ms
  BLOCK = 50              # lines per script.writeToFile call (buffering)

  buf = None
  n = None

  def now(self):
    return time.time() * 1000 - self.__interpretation_started_timestamp__

  def show(self, text):
    brick.display().clear()
    brick.display().addLabel(text, 5, 5, 20)
    brick.display().redraw()

  def beep(self):
    try:
      brick.playSound("media/beep.wav")
    except Exception:
      pass

  def motors(self, u):
    brick.motor("M3").setPower(int(u))
    brick.motor("M4").setPower(int(-u))

  def flush(self):
    if self.n > 0:
      script.writeToFile(self.FILE, self.buf)
      self.buf = ""
      self.n = 0

  def amplitude(self, tp):
    k = int(tp // 12000)            # one step every 3 periods (12 s)
    if k > 2:
      k = 2
    return [30, 60, 150][k]

  def sat(self, v):
    return max(-100.0, min(100.0, v))

  def u_sin(self, tp):
    return self.sat(self.amplitude(tp) * math.sin(2 * math.pi * tp / 4000.0))

  def u_rect(self, tp):
    f = 1.0 if math.sin(2 * math.pi * tp / 4000.0) >= 0 else -1.0
    return self.sat(self.amplitude(tp) * f)

  def run_phase(self, phase, duration_ms, signal):
    # log one phase; signal(tp) gives the motor power, None = motors off
    self.show(phase)
    if signal is None:
      self.motors(0)
    t0 = self.now()
    while True:
      tp = self.now() - t0
      if tp >= duration_ms:
        break
      if signal is not None:
        self.motors(signal(tp))
      g = brick.gyroscope().read()
      raw = brick.gyroscope().readRawData()
      encL = brick.encoder("E4").read()
      encR = brick.encoder("E3").read()
      self.buf = self.buf + str(g[3]) + "," + str(g[2]) + "," + str(encL) + "," + str(encR) + "," \
                 + str(raw[2]) + "," + phase + "," + str(int(self.now())) + "\n"
      self.n = self.n + 1
      if self.n >= self.BLOCK:
        self.flush()
      script.wait(self.PERIOD_MS)
    self.flush()

  def execMain(self):
    brick.encoder("E3").reset()
    brick.encoder("E4").reset()
    script.removeFile(self.FILE)
    self.motors(0)
    self.buf = "t_us,gz_cal,encL,encR,gz_raw,phase,t_ms\n"
    self.n = 1
    self.flush()

    # Step 1 - static run
    self.show("warmup")
    script.wait(120000)                       # warm-up 2 min, not logged
    self.run_phase("static", 180000, None)

    # Step 2 - rotation run, Option A
    self.run_phase("sin", 36000, self.u_sin)
    self.run_phase("rect", 36000, self.u_rect)
    self.run_phase("rest", 3000, None)

    # slip check, then hand spin (section 3 backup)
    self.run_phase("slipcheck", 20000, None)
    self.beep()
    self.run_phase("hand", 30000, None)
    self.beep()
    self.motors(0)
    self.show("done")
    brick.stop()
    return

def main():
  program = Program()
  program.execMain()

if __name__ == '__main__':
  main()
