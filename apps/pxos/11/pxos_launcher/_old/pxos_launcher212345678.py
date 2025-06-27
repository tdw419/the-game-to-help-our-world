import ast, os
from PIL import Image

class PXBot:
  def __init__(s, vfs, rt): s.v, s.r, s.h = vfs, rt, []
  def run(s, i):
    s.h.append(i); p = i.split(":")
    try:
      if p[0] == "create":
        if p[1] == "function": return s._f(p[2], p[3], p[4] if len(p) > 4 else "None")
        if p[1] == "class": return s._c(p[2], p[3], p[4] if len(p) > 4 else "")
      if p[0] == "edit": return s._e(p[2], p[3])
      if p[0] == "exec": return s.r.exec(p[1])
    except Exception as e: return f"Err:{e}"
  def _f(s, n, p, r):
    b = "if n==0:return 1\n return n*f(n-1)" if "fact" in n else "pass"
    c = f"def {n}({p}):\n {b}\n return {r}"
    return s._s(c, n)
  def _c(s, n, a, m):
    i = "\n ".join([f"self.{x}={x}" for x in a.split(",")])
    m = "\n ".join([f"def {x}(self): pass" for x in m.split(",")]) or "pass"
    c = f"class {n}:\n def __init__(self,{a}):\n {i}\n {m}"
    return s._s(c, n)
  def _e(s, n, d):
    c = s.r.load(n)
    c += "\n print('Edit')" if "print" in d else "\n #Edit"
    return s._s(c, n)
  def _s(s, c, n):
    try: ast.parse(c)
    except: return "Bad code"
    b = f"/code/{n}.png"; i = s._enc(c); i.save(b)
    s.v.add(os.path.dirname(b)); s.r.save(n, b)
    return f"Ok:{n}@{b}"
  def _enc(s, c):
    d = c.encode(); w = int(len(d)**0.5)+1
    i = Image.new("RGB", (w,w)); p = i.load()
    for j, x in enumerate(d): p[j%w, j//w] = (x,0,0)
    return i

class MiniVFS:
  def add(self, p): pass

class MiniRT:
  def __init__(s): s.d = {}
  def save(s, k, v): s.d[k] = v
  def load(s, k): return open(s.d.get(k)).read() if k in s.d else None
  def exec(s, k): print(f"Exec: {k}\n{open(s.d.get(k)).read()}")

if __name__ == "__main__":
  v, r = MiniVFS(), MiniRT(); b = PXBot(v, r)
  while 1:
    i = input(">> ")
    if i == "exit": break
    print(b.run(i))
