class MyClass:
     def __init__(self,x):
           self.x = x

lst  = ["A","B"]  # don't use list as an identifier

myclasses = {k: MyClass(text) for k in lst}