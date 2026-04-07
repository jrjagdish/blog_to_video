# name = input("File name: ")
# a = {"image": [".jpg", ".gif", ".jpeg", ".png"], "document": [".pdf", ".txt"], "archive": [".zip"]}
# for category, extensions in a.items():
#     if any(name.endswith(ext) for ext in extensions):
#         val=name.index('.')
#         print(f"{category}/{name[val+1:]}")
#         break
# else:
#     print(f"{name} is of an unknown type.")

expression=input("Expression: ")
x,y,z=expression.split(" ")

try:
    x=int(x)
    z=int(z)
    if y=="+":
       print(float(x+z))
    elif y=="/":
       print(float(x/z))
    elif y=="*":
        print(float(x*z))
    elif y=="-":
        print(float(x-z))
except ZeroDivisionError:
    raise ("Error can't divde by zero")



