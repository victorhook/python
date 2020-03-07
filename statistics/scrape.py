from tabula import read_pdf

df = read_pdf('ceq.pdf')
print(dir(df))